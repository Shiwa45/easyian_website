"""Helpers that build the SEO context (title, description, canonical, Open Graph, JSON-LD)."""
import json

from django.conf import settings
from django.templatetags.static import static
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

from .models import SiteSettings


def absolute(url):
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"{settings.SITE_URL}{url}"


def _image_url(*candidates):
    for image in candidates:
        if image:
            try:
                return absolute(image.url)
            except ValueError:
                continue
    return absolute(f"{settings.STATIC_URL}img/og-default.png")


def build_meta(request, *, title="", description="", image=None, obj=None, og_type="website",
               noindex=False, canonical=None):
    """Return a dict the base template turns into <title>, meta, OG and Twitter tags.

    `obj` may be any model using core.models.SeoFields — its meta fields win over the defaults.
    """
    site = SiteSettings.load()
    if obj is not None:
        title = getattr(obj, "meta_title", "") or title
        description = getattr(obj, "meta_description", "") or description
        image = getattr(obj, "og_image", None) or image
        noindex = noindex or getattr(obj, "noindex", False)

    full_title = title or site.default_meta_title
    if title and site.site_name.lower() not in title.lower():
        # Google truncates around 60 characters; keep the page's own words over the brand.
        suffixed = f"{title} | {site.site_name}"
        full_title = suffixed if len(suffixed) <= 60 else title
    description = Truncator(strip_tags(description or site.default_meta_description)).chars(165)

    return {
        "title": full_title,
        "description": description,
        "canonical": absolute(canonical or request.path),
        "image": _image_url(image, site.default_og_image),
        "type": og_type,
        "robots": "noindex, nofollow" if noindex else "index, follow, max-image-preview:large",
    }


def jsonld(*objects):
    """Serialise JSON-LD blocks safely for inclusion in a <script type="application/ld+json">."""
    data = [o for o in objects if o]
    if not data:
        return ""
    payload = data[0] if len(data) == 1 else {"@context": "https://schema.org", "@graph": data}
    text = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return mark_safe(text)


def organization_ld():
    site = SiteSettings.load()
    same_as = [u for u in (site.linkedin_url, site.facebook_url, site.instagram_url,
                           site.youtube_url, site.twitter_url) if u]
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site.site_name,
        "legalName": site.legal_name,
        "url": settings.SITE_URL + "/",
        "description": site.tagline,
    }
    org["logo"] = absolute(site.logo.url if site.logo else static("img/logo.png"))
    if site.email:
        org["email"] = site.email
    if site.phone:
        org["telephone"] = site.phone
    if site.city or site.address:
        org["address"] = {
            "@type": "PostalAddress",
            "streetAddress": site.address,
            "addressLocality": site.city,
            "addressRegion": site.state,
            "postalCode": site.postal_code,
            "addressCountry": "IN" if site.country.lower() == "india" else site.country,
        }
    if same_as:
        org["sameAs"] = same_as
    return org


def breadcrumb_ld(items):
    """items: list of (name, url) tuples."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": absolute(url)}
            for i, (name, url) in enumerate(items, start=1)
        ],
    }


def faq_ld(faqs):
    faqs = list(faqs)
    if not faqs:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f.question,
             "acceptedAnswer": {"@type": "Answer", "text": f.answer}}
            for f in faqs
        ],
    }
