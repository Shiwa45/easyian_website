from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from blog.sitemaps import BlogCategorySitemap, BlogPostSitemap
from core.sitemaps import ServiceSitemap, StaticPageSitemap
from core.views import robots_txt

admin.site.site_header = "Easyian Admin"
admin.site.site_title = "Easyian Admin"
admin.site.index_title = "Website content & leads"

sitemaps = {
    "pages": StaticPageSitemap,
    "services": ServiceSitemap,
    "blog": BlogPostSitemap,
    "blog-categories": BlogCategorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("blog/", include("blog.urls")),
    path("lead/", include("leads.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.page_not_found"
