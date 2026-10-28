from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from tinymce.models import HTMLField

# Clay palette used across the site. Admin users pick from these so the design stays consistent.
COLOR_CHOICES = [
    ("coral", "Coral"),
    ("teal", "Teal"),
    ("yellow", "Sunny yellow"),
    ("sky", "Sky blue"),
    ("peach", "Peach"),
    ("mint", "Mint"),
]

ICON_CHOICES = [
    ("chart", "Chart / CRM"),
    ("bot", "Robot / AI"),
    ("monitor", "Monitor / Web"),
    ("phone", "Phone / Dialer"),
    ("wifi", "Signal / VoIP"),
    ("mobile", "Mobile"),
    ("mail", "Mail"),
    ("pin", "Location"),
    ("spark", "Spark"),
    ("shield", "Shield"),
    ("users", "Users"),
    ("rupee", "Rupee / Billing"),
]


class SeoFields(models.Model):
    meta_title = models.CharField(
        max_length=70, blank=True,
        help_text="Shown in Google results and the browser tab. Aim for 50–60 characters.")
    meta_description = models.CharField(
        max_length=170, blank=True,
        help_text="Search result snippet. Aim for 140–160 characters.")
    og_image = models.ImageField(
        upload_to="seo/", blank=True,
        help_text="Image for WhatsApp / LinkedIn / Facebook shares (1200×630 recommended).")
    noindex = models.BooleanField(default=False, help_text="Hide this page from search engines.")

    class Meta:
        abstract = True


class SiteSettings(models.Model):
    """One row holds the global settings. Edit it in Admin → Site settings."""

    site_name = models.CharField(max_length=80, default="Easyian")
    legal_name = models.CharField(max_length=120, default="Easyian Tech OPC Private Limited")
    tagline = models.CharField(max_length=160, default="SaaS CRM, AI agents, predictive dialers, VoIP and websites.")
    logo = models.ImageField(upload_to="brand/", blank=True, help_text="Optional. Leave empty to use the bundled Easyian logo.")
    favicon = models.ImageField(upload_to="brand/", blank=True)

    phone = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField(max_length=40, blank=True, help_text="Digits with country code, e.g. 919876543210")
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=60, default="India")
    map_embed_url = models.URLField(blank=True, help_text="Google Maps embed URL (optional).")

    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    header_cta_label = models.CharField(max_length=40, default="Book a demo")
    footer_about = models.TextField(default="SaaS CRM, AI agents, predictive dialers, VoIP and websites for teams that sell by phone.")

    default_meta_title = models.CharField(max_length=70, default="Easyian — CRM, AI Agents, Predictive Dialer & VoIP")
    default_meta_description = models.CharField(
        max_length=170,
        default="Easyian builds SaaS CRM, AI voice & chat agents, predictive autodialers, VoIP setups and "
                "websites for Indian sales teams.")
    default_og_image = models.ImageField(upload_to="seo/", blank=True)
    google_site_verification = models.CharField(max_length=120, blank=True)
    google_analytics_id = models.CharField(max_length=40, blank=True, help_text="e.g. G-XXXXXXX")
    extra_head_html = models.TextField(blank=True, help_text="Advanced: extra tags injected into <head> (pixels etc.).")

    lead_notification_email = models.EmailField(
        blank=True, help_text="New website leads are emailed here (optional).")
    lead_success_message = models.CharField(
        max_length=200, default="Thanks! Our team will call you back shortly.")

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("site_settings")

    @classmethod
    def load(cls):
        obj = cache.get("site_settings")
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set("site_settings", obj, 300)
        return obj


class Page(SeoFields):
    """Hero text + SEO for each fixed page of the site."""

    KEY_CHOICES = [
        ("home", "Home"),
        ("services", "Services"),
        ("dialsathi", "DialSathi"),
        ("about", "About & Contact"),
        ("blog", "Blog"),
    ]
    key = models.CharField(max_length=20, choices=KEY_CHOICES, unique=True)
    eyebrow = models.CharField(max_length=120, blank=True)
    heading = models.CharField(max_length=160)
    heading_highlight = models.CharField(
        max_length=80, blank=True, help_text="Optional coloured words shown after the heading.")
    subheading = models.TextField(blank=True)
    primary_cta_label = models.CharField(max_length=40, blank=True)
    primary_cta_url = models.CharField(max_length=200, blank=True)
    secondary_cta_label = models.CharField(max_length=40, blank=True)
    secondary_cta_url = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.get_key_display()

    @classmethod
    def get(cls, key):
        page = cls.objects.filter(key=key).first()
        if page is None:
            page = cls(key=key, heading=dict(cls.KEY_CHOICES).get(key, key.title()))
        return page


class Service(SeoFields):
    title = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default="chart")
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default="coral")
    short_description = models.CharField(max_length=220)
    description = HTMLField(blank=True, help_text="Full description for the service page.")
    features = models.TextField(blank=True, help_text="One feature per line.")
    good_for = models.CharField(max_length=120, blank=True)
    cta_label = models.CharField(max_length=40, default="Book a demo")
    external_url = models.URLField(blank=True, help_text="Optional: link the card to another site (e.g. a product site).")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # DialSathi has its own product page; avoid duplicate content.
        if self.slug == "dialsathi":
            return reverse("core:dialsathi")
        return reverse("core:service_detail", args=[self.slug])

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]


class Highlight(models.Model):
    """Small cards used in several sections. Pick the section it belongs to."""

    SECTION_CHOICES = [
        ("home_flow", "Home · How it fits together (numbered steps)"),
        ("home_ai", "Home · AI agent bullet points"),
        ("home_why", "Home · Why teams pick Easyian"),
        ("process", "Services · How we work (steps)"),
        ("about_values", "About · Values"),
        ("dialsathi_features", "DialSathi · Features"),
        ("dialsathi_addons", "DialSathi · Add-on modules"),
        ("dialsathi_points", "DialSathi · Short feature chips (home spotlight)"),
    ]
    section = models.CharField(max_length=30, choices=SECTION_CHOICES)
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default="coral")
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "order", "id"]

    def __str__(self):
        return f"{self.get_section_display()} — {self.title}"


class PricingPlan(models.Model):
    name = models.CharField(max_length=60)
    price = models.CharField(max_length=40, help_text="e.g. ₹12,999")
    period = models.CharField(max_length=30, default="/year")
    users_label = models.CharField(max_length=80, blank=True, help_text="e.g. Up to 10 users")
    features = models.TextField(blank=True, help_text="Optional, one per line.")
    cta_label = models.CharField(max_length=40, default="Get started")
    is_highlighted = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]


class Integration(models.Model):
    name = models.CharField(max_length=60)
    logo = models.ImageField(upload_to="integrations/", blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Industry(models.Model):
    name = models.CharField(max_length=60)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Industries"

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    name = models.CharField(max_length=80)
    role = models.CharField(max_length=80, blank=True)
    company = models.CharField(max_length=80, blank=True)
    quote = models.TextField()
    photo = models.ImageField(upload_to="testimonials/", blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "-id"]

    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name


class FAQ(models.Model):
    PAGE_CHOICES = [
        ("home", "Home"),
        ("services", "Services"),
        ("dialsathi", "DialSathi"),
        ("about", "About & Contact"),
    ]
    page = models.CharField(max_length=20, choices=PAGE_CHOICES, default="home")
    question = models.CharField(max_length=220)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["page", "order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
