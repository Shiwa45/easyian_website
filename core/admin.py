from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import (FAQ, Highlight, Industry, Integration, Page, PricingPlan, Service,
                     SiteSettings, Testimonial)

SEO_FIELDSET = ("SEO", {
    "classes": ("collapse",),
    "fields": ("meta_title", "meta_description", "og_image", "noindex"),
})


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Brand", {"fields": ("site_name", "legal_name", "tagline", "logo", "favicon")}),
        ("Contact details", {"fields": ("phone", "whatsapp", "email", "address", "city", "state",
                                        "postal_code", "country", "map_embed_url")}),
        ("Social links", {"fields": ("linkedin_url", "facebook_url", "instagram_url", "youtube_url", "twitter_url")}),
        ("Header & footer", {"fields": ("header_cta_label", "footer_about")}),
        ("Default SEO", {"fields": ("default_meta_title", "default_meta_description", "default_og_image",
                                    "google_site_verification", "google_analytics_id", "extra_head_html")}),
        ("Lead form", {"fields": ("lead_notification_email", "lead_success_message")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[obj.pk]))


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "heading", "meta_title")
    fieldsets = (
        (None, {"fields": ("key", "eyebrow", "heading", "heading_highlight", "subheading")}),
        ("Buttons", {"fields": (("primary_cta_label", "primary_cta_url"), ("secondary_cta_label", "secondary_cta_url"))}),
        SEO_FIELDSET,
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "color", "order", "is_active", "show_on_home")
    list_editable = ("order", "is_active", "show_on_home")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "short_description")
    fieldsets = (
        (None, {"fields": ("title", "slug", ("icon", "color"), "short_description", "description",
                           "features", "good_for", "cta_label", "external_url")}),
        ("Display", {"fields": (("order", "is_active", "show_on_home"),)}),
        SEO_FIELDSET,
    )


@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "color", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("section", "is_active")
    search_fields = ("title", "text")


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "period", "users_label", "is_highlighted", "order", "is_active")
    list_editable = ("order", "is_active", "is_highlighted")


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "page", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("page",)
    search_fields = ("question", "answer")
