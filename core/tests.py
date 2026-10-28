from django.core.management import call_command
from django.test import TestCase

from blog.models import Post


class PageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_pages_render_with_seo(self):
        for url in ["/", "/services/", "/services/crm-software/", "/dialsathi/", "/about/", "/blog/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            html = r.content.decode()
            self.assertIn('<link rel="canonical"', html, url)
            self.assertIn('application/ld+json', html, url)
            self.assertIn('og:title', html, url)
            self.assertEqual(html.count("<h1"), 1, url)

    def test_blog_post_and_draft(self):
        post = Post.objects.published().first()
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)
        post.status = Post.Status.DRAFT
        post.save()
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 404)

    def test_seo_files(self):
        self.assertContains(self.client.get("/robots.txt"), "Sitemap:")
        self.assertContains(self.client.get("/sitemap.xml"), "/blog/")
        self.assertEqual(self.client.get("/blog/feed/").status_code, 200)
        self.assertEqual(self.client.get("/contact/").status_code, 301)
