import re

from django import forms
from django.conf import settings

from core.models import Service

from . import antispam
from .models import Lead

PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{8,20}$")


def _interest_choices():
    choices = [(s.slug, s.title) for s in Service.objects.filter(is_active=True)]
    return choices or [("general", "General enquiry")]


class LeadForm(forms.ModelForm):
    interests = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)

    # ---- hidden captcha fields (see leads/antispam.py) ----
    website = forms.CharField(required=False, label="Website",
                              widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
    fax_number = forms.CharField(required=False, label="Fax",
                                 widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
    challenge = forms.CharField(widget=forms.HiddenInput)
    pow = forms.CharField(required=False, widget=forms.HiddenInput)
    source_page = forms.CharField(required=False, widget=forms.HiddenInput)
    utm_source = forms.CharField(required=False, widget=forms.HiddenInput)
    utm_medium = forms.CharField(required=False, widget=forms.HiddenInput)
    utm_campaign = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Lead
        fields = ["name", "company", "phone", "email", "team_size", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Full name", "autocomplete": "name"}),
            "company": forms.TextInput(attrs={"placeholder": "Company name", "autocomplete": "organization"}),
            "phone": forms.TextInput(attrs={"placeholder": "+91", "type": "tel", "autocomplete": "tel",
                                            "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@company.com", "autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 4,
                                             "placeholder": "Lead sources, current tools, what you want to fix…"}),
        }
        labels = {
            "name": "Your name",
            "company": "Company",
            "phone": "Mobile",
            "email": "Work email",
            "team_size": "Team size",
            "message": "Tell us a little",
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.fields["interests"].choices = _interest_choices()
        self.fields["interests"].label = "I'm interested in"
        self.fields["name"].required = True
        self.fields["phone"].required = True
        for name in ("name", "company", "phone", "email", "team_size", "message"):
            self.fields[name].widget.attrs["class"] = "input"
        if not self.is_bound:
            self.initial["challenge"] = antispam.new_challenge()
            if request is not None:
                self.initial.setdefault("source_page", request.path)

    @property
    def turnstile_site_key(self):
        return settings.TURNSTILE_SITE_KEY

    @property
    def pow_difficulty(self):
        return antispam.POW_DIFFICULTY

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter your name.")
        if "http" in name.lower() or "www." in name.lower():
            raise forms.ValidationError("Please enter a valid name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if not PHONE_RE.match(phone) or not (10 <= len(digits) <= 15):
            raise forms.ValidationError("Please enter a valid mobile number.")
        return phone

    def save(self, commit=True):
        lead = super().save(commit=False)
        lead.interests = ", ".join(self.cleaned_data.get("interests") or [])
        for field in ("source_page", "utm_source", "utm_medium", "utm_campaign"):
            setattr(lead, field, (self.cleaned_data.get(field) or "")[:250])
        if self.request is not None:
            lead.ip_address = antispam.client_ip(self.request)
            lead.user_agent = self.request.META.get("HTTP_USER_AGENT", "")[:300]
        if commit:
            lead.save()
        return lead
