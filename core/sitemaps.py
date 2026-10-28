from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Service


class SiteProtocolMixin:
    """Build sitemap URLs from settings.SITE_URL (scheme + domain) instead of the request host."""

    def get_protocol(self, protocol=None):
        return urlsplit(settings.SITE_URL).scheme or "https"

    def get_domain(self, site=None):
        return urlsplit(settings.SITE_URL).netloc


class StaticPageSitemap(SiteProtocolMixin, Sitemap):
    changefreq = "weekly"

    def items(self):
        return ["core:home", "core:services", "core:dialsathi", "core:about", "blog:list"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.8


class ServiceSitemap(SiteProtocolMixin, Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Service.objects.filter(is_active=True, noindex=False)
