import logging

from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import SiteSettings
from core.seo import build_meta

from . import antispam
from .forms import LeadForm
from .models import BlockedSubmission

logger = logging.getLogger("leads")


def _wants_json(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or \
        "application/json" in request.headers.get("accept", "")


def _safe_back(request, path):
    if path and url_has_allowed_host_and_scheme(path, allowed_hosts={request.get_host()}):
        return path
    return "/"


def _notify(lead):
    site = SiteSettings.load()
    if not site.lead_notification_email:
        return
    body = "\n".join([
        f"Name: {lead.name}", f"Company: {lead.company}", f"Phone: {lead.phone}", f"Email: {lead.email}",
        f"Team size: {lead.team_size}", f"Interests: {lead.interests}", "", lead.message, "",
        f"Page: {lead.source_page}", f"UTM: {lead.utm_source} / {lead.utm_medium} / {lead.utm_campaign}",
    ])
    send_mail(f"New website lead: {lead.name}", body, None, [site.lead_notification_email], fail_silently=True)


@require_POST
def submit(request):
    site = SiteSettings.load()
    back = _safe_back(request, request.POST.get("source_page", "/"))

    try:
        antispam.run_checks(request, request.POST)
    except antispam.SpamDetected as exc:
        BlockedSubmission.objects.create(
            reason=exc.reason,
            ip_address=antispam.client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
            payload=str({k: v for k, v in request.POST.items() if k not in ("csrfmiddlewaretoken", "challenge")})[:2000],
        )
        logger.info("Blocked lead submission: %s", exc.reason)
        # Bots get the same "success" reply so they learn nothing. Humans who hit a check
        # (e.g. form left open for hours) get a clear, friendly message instead.
        if exc.reason in ("honeypot", "replayed"):
            if _wants_json(request):
                return JsonResponse({"ok": True, "message": site.lead_success_message,
                                     "challenge": antispam.new_challenge()})
            messages.success(request, site.lead_success_message)
            return redirect(back + "#lead-form")
        friendly = {
            "expired-form": "This form was open for a long time. Please refresh the page and try again.",
            "rate-limited": "You've sent several requests already — we'll be in touch soon.",
            "too-many-links": "Please remove the links from your message and try again.",
        }.get(exc.reason, "We couldn't verify the form. Please wait a moment and submit again.")
        if _wants_json(request):
            return JsonResponse({"ok": False, "message": friendly, "refresh": exc.reason == "expired-form",
                                 "challenge": antispam.new_challenge()}, status=400)
        messages.error(request, friendly)
        return redirect(back + "#lead-form")

    form = LeadForm(request.POST, request=request)
    if form.is_valid():
        lead = form.save()
        _notify(lead)
        if _wants_json(request):
            return JsonResponse({"ok": True, "message": site.lead_success_message,
                                 "challenge": antispam.new_challenge()})
        messages.success(request, site.lead_success_message)
        return redirect(back + "#lead-form")

    if _wants_json(request):
        # Form errors: the challenge was consumed, so send a fresh one.
        return JsonResponse({
            "ok": False,
            "errors": {k: [str(e) for e in v] for k, v in form.errors.items()},
            "challenge": antispam.new_challenge(),
        }, status=400)
    data = request.POST.copy()
    data["challenge"] = antispam.new_challenge()
    data["pow"] = ""
    retry = LeadForm(data, request=request)
    retry.is_valid()
    return render(request, "leads/retry.html", {
        "lead_form": retry,
        "meta": build_meta(request, title="Check your details", noindex=True),
    }, status=400)
