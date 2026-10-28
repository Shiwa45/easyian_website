from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Category, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "post_count")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "order")}),
        ("SEO", {"classes": ("collapse",), "fields": ("meta_title", "meta_description", "og_image", "noindex")}),
    )

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "is_featured", "published_at", "view_link")
    list_filter = ("status", "category", "is_featured", "tags")
    list_editable = ("status", "is_featured")
    search_fields = ("title", "excerpt", "content", "focus_keyword")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    date_hierarchy = "published_at"
    actions = ("publish_now", "make_draft")
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "content")}),
        ("Cover image", {"fields": ("cover_image", "cover_alt")}),
        ("Organise", {"fields": ("category", "tags", "is_featured")}),
        ("Publishing", {"fields": ("status", "published_at", "author", "author_name")}),
        ("SEO", {"fields": ("focus_keyword", "meta_title", "meta_description", "og_image",
                            "canonical_url", "noindex")}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="Live page")
    def view_link(self, obj):
        if obj.pk and obj.is_live:
            return format_html('<a href="{}" target="_blank" rel="noopener">View ↗</a>', obj.get_absolute_url())
        return "—"

    @admin.action(description="Publish selected posts now")
    def publish_now(self, request, queryset):
        updated = queryset.update(status=Post.Status.PUBLISHED, published_at=timezone.now())
        self.message_user(request, f"{updated} post(s) published.")

    @admin.action(description="Move selected posts to draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"{updated} post(s) moved to draft.")
