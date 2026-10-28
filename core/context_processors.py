from django.conf import settings

from .models import Service, SiteSettings


def site(request):
    return {
        "site": SiteSettings.load(),
        "site_url": settings.SITE_URL,
        "nav_services": Service.objects.filter(is_active=True).only("title", "slug"),
    }
