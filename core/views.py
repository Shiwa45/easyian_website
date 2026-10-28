from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from blog.models import Post
from leads.forms import LeadForm

from .models import FAQ, Highlight, Industry, Integration, Page, PricingPlan, Service, Testimonial
from .seo import breadcrumb_ld, build_meta, faq_ld, jsonld, organization_ld


def _highlights(section):
    return Highlight.objects.filter(section=section, is_active=True)


def _faqs(page):
    return FAQ.objects.filter(page=page, is_active=True)


def home(request):
    page = Page.get("home")
    faqs = _faqs("home")
    context = {
        "page": page,
        "services": Service.objects.filter(is_active=True, show_on_home=True),
        "flow_steps": _highlights("home_flow"),
        "ai_points": _highlights("home_ai"),
        "why_points": _highlights("home_why"),
        "sathi_points": _highlights("dialsathi_points"),
        "starting_plan": PricingPlan.objects.filter(is_active=True).first(),
        "testimonials": Testimonial.objects.filter(is_active=True),
        "faqs": faqs,
        "latest_posts": Post.objects.published().select_related("category")[:3],
        "meta": build_meta(request, obj=page),
        "jsonld": jsonld(organization_ld(), {
            "@context": "https://schema.org", "@type": "WebSite",
            "name": request_site_name(), "url": settings.SITE_URL + "/",
        }, faq_ld(faqs)),
        "nav_active": "home",
    }
    return render(request, "core/home.html", context)


def request_site_name():
    from .models import SiteSettings
    return SiteSettings.load().site_name


def services(request):
    page = Page.get("services")
    faqs = _faqs("services")
    services_qs = Service.objects.filter(is_active=True)
    context = {
        "page": page,
        "services": services_qs,
        "process_steps": _highlights("process"),
        "faqs": faqs,
        "meta": build_meta(request, obj=page, title=page.heading),
        "jsonld": jsonld(
            breadcrumb_ld([("Home", "/"), ("Services", reverse("core:services"))]),
            faq_ld(faqs),
        ),
        "nav_active": "services",
    }
    return render(request, "core/services.html", context)


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    if service.get_absolute_url() != request.path:
        return redirect(service.get_absolute_url(), permanent=True)
    context = {
        "service": service,
        "other_services": Service.objects.filter(is_active=True).exclude(pk=service.pk),
        "lead_form": LeadForm(request=request, initial={"interests": [service.slug]}),
        "meta": build_meta(request, obj=service, title=service.title, description=service.short_description),
        "jsonld": jsonld(
            breadcrumb_ld([("Home", "/"), ("Services", reverse("core:services")),
                           (service.title, service.get_absolute_url())]),
            {
                "@context": "https://schema.org", "@type": "Service",
                "name": service.title, "description": service.short_description,
                "provider": {"@type": "Organization", "name": request_site_name()},
                "areaServed": "IN",
            },
        ),
        "nav_active": "services",
    }
    return render(request, "core/service_detail.html", context)


def dialsathi(request):
    page = Page.get("dialsathi")
    faqs = _faqs("dialsathi")
    plans = PricingPlan.objects.filter(is_active=True)
    product_ld = {
        "@context": "https://schema.org", "@type": "SoftwareApplication",
        "name": "DialSathi", "applicationCategory": "BusinessApplication",
        "operatingSystem": "Android, Web", "url": "https://dialsathi.com",
        "publisher": {"@type": "Organization", "name": request_site_name()},
    }
    offers = []
    for plan in plans:
        digits = "".join(ch for ch in plan.price if ch.isdigit() or ch == ".")
        if digits:
            offers.append({"@type": "Offer", "name": plan.name, "price": digits, "priceCurrency": "INR"})
    if offers:
        product_ld["offers"] = offers
    context = {
        "page": page,
        "features": _highlights("dialsathi_features"),
        "addons": _highlights("dialsathi_addons"),
        "plans": plans,
        "integrations": Integration.objects.filter(is_active=True),
        "industries": Industry.objects.filter(is_active=True),
        "faqs": faqs,
        "lead_form": LeadForm(request=request, initial={"interests": ["dialsathi"]}),
        "meta": build_meta(request, obj=page, title=page.heading),
        "jsonld": jsonld(
            breadcrumb_ld([("Home", "/"), ("DialSathi", reverse("core:dialsathi"))]),
            product_ld, faq_ld(faqs),
        ),
        "nav_active": "dialsathi",
    }
    return render(request, "core/dialsathi.html", context)


def about(request):
    page = Page.get("about")
    faqs = _faqs("about")
    context = {
        "page": page,
        "values": _highlights("about_values"),
        "faqs": faqs,
        "lead_form": LeadForm(request=request),
        "meta": build_meta(request, obj=page, title="About & Contact"),
        "jsonld": jsonld(
            organization_ld(),
            breadcrumb_ld([("Home", "/"), ("About & Contact", reverse("core:about"))]),
            faq_ld(faqs),
        ),
        "nav_active": "about",
    }
    return render(request, "core/about.html", context)


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /lead/",
        "Disallow: /tinymce/",
        "Allow: /",
        "",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def page_not_found(request, exception=None):
    context = {"meta": build_meta(request, title="Page not found", noindex=True)}
    return render(request, "404.html", context, status=404)
