from django.contrib.sitemaps import Sitemap

from core.sitemaps import SiteProtocolMixin

from .models import Category, Post


class BlogPostSitemap(SiteProtocolMixin, Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Post.objects.published().filter(noindex=False, canonical_url="")

    def lastmod(self, obj):
        return obj.updated_at


class BlogCategorySitemap(SiteProtocolMixin, Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Category.objects.filter(noindex=False, posts__status=Post.Status.PUBLISHED).distinct()
