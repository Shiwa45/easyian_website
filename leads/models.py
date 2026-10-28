from django.conf import settings
from django.db import models


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        DEMO = "demo", "Demo scheduled"
        WON = "won", "Won"
        LOST = "lost", "Lost"
        JUNK = "junk", "Junk"

    TEAM_SIZE_CHOICES = [
        ("", "Select team size"),
        ("1-10", "1–10 agents"),
        ("11-20", "11–20 agents"),
        ("21-50", "21–50 agents"),
        ("50+", "50+ agents"),
    ]

    name = models.CharField(max_length=120)
    company = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    team_size = models.CharField(max_length=10, choices=TEAM_SIZE_CHOICES, blank=True)
    interests = models.CharField(max_length=255, blank=True, help_text="Services the visitor picked.")
    message = models.TextField(blank=True)

    source_page = models.CharField(max_length=255, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes (not visible to the visitor).")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.phone}"


class BlockedSubmission(models.Model):
    """Log of submissions stopped by the hidden captcha, so you can see it working."""

    reason = models.CharField(max_length=60)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    payload = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blocked spam submission"

    def __str__(self):
        return f"{self.reason} · {self.created_at:%d %b %Y %H:%M}"
