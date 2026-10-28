from django.contrib.syndication.views import Feed
from django.urls import reverse

from core.models import SiteSettings

from .models import Post


class LatestPostsFeed(Feed):
    def title(self):
        return f"{SiteSettings.load().site_name} Blog"

    def link(self):
        return reverse("blog:list")

    def description(self):
        return "Latest articles from the Easyian blog."

    def items(self):
        return Post.objects.published()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at
