from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from core.models import Page
from core.seo import absolute, breadcrumb_ld, build_meta, jsonld

from .models import Category, Post, Tag

PAGE_SIZE = 9


def _list_context(request, queryset, *, heading, intro, crumbs, obj=None, title=None):
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) |
                                   Q(content__icontains=query))
    paginator = Paginator(queryset, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    # Paginated and search pages should not compete with page 1 in search results.
    noindex = bool(query)
    canonical = request.path if page_obj.number == 1 else f"{request.path}?page={page_obj.number}"
    return {
        "heading": heading,
        "intro": intro,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
        "query": query,
        "categories": Category.objects.all(),
        "featured": Post.objects.published().filter(is_featured=True).first() if page_obj.number == 1 and not query else None,
        "meta": build_meta(request, obj=obj, title=title or heading, description=intro,
                           noindex=noindex, canonical=canonical),
        "jsonld": jsonld(breadcrumb_ld(crumbs)),
        "nav_active": "blog",
    }


def post_list(request):
    page = Page.get("blog")
    qs = Post.objects.published().select_related("category")
    context = _list_context(
        request, qs,
        heading=page.heading if page.pk else "The Easyian Blog",
        intro=page.subheading or "Guides on CRM, predictive dialers, AI agents and running a better sales floor.",
        crumbs=[("Home", "/"), ("Blog", reverse("blog:list"))],
        obj=page if page.pk else None,
        title="Blog",
    )
    context["page"] = page
    return render(request, "blog/list.html", context)


def category(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    qs = Post.objects.published().filter(category=cat).select_related("category")
    context = _list_context(
        request, qs, heading=cat.name, intro=cat.description or f"Articles about {cat.name}.",
        crumbs=[("Home", "/"), ("Blog", reverse("blog:list")), (cat.name, cat.get_absolute_url())],
        obj=cat,
    )
    context["active_category"] = cat
    return render(request, "blog/list.html", context)


def tag(request, slug):
    tg = get_object_or_404(Tag, slug=slug)
    qs = Post.objects.published().filter(tags=tg).select_related("category")
    context = _list_context(
        request, qs, heading=f"#{tg.name}", intro=f"Articles tagged {tg.name}.",
        crumbs=[("Home", "/"), ("Blog", reverse("blog:list")), (tg.name, tg.get_absolute_url())],
    )
    # Tag archives are thin pages; keep them out of the index but let crawlers follow links.
    context["meta"]["robots"] = "noindex, follow"
    return render(request, "blog/list.html", context)


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("category", "author").prefetch_related("tags"), slug=slug)
    if not post.is_live and not request.user.is_staff:
        raise Http404
    related = Post.objects.published().exclude(pk=post.pk)
    if post.category_id:
        related = related.filter(category_id=post.category_id)
    related = list(related[:3])
    if len(related) < 3:
        extra = Post.objects.published().exclude(pk=post.pk).exclude(pk__in=[p.pk for p in related])
        related += list(extra[: 3 - len(related)])

    meta = build_meta(request, obj=post, title=post.title, description=post.excerpt,
                      image=post.cover_image, og_type="article",
                      noindex=not post.is_live, canonical=post.canonical_url or None)
    article_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": meta["description"],
        "image": [meta["image"]],
        "datePublished": post.published_at.isoformat(),
        "dateModified": post.updated_at.isoformat(),
        "author": {"@type": "Person" if post.author_name or post.author else "Organization",
                   "name": post.author_display},
        "mainEntityOfPage": absolute(post.get_absolute_url()),
        "wordCount": len(post.content.split()),
    }
    if post.category:
        article_ld["articleSection"] = post.category.name
    crumbs = [("Home", "/"), ("Blog", reverse("blog:list"))]
    if post.category:
        crumbs.append((post.category.name, post.category.get_absolute_url()))
    crumbs.append((post.title, post.get_absolute_url()))

    context = {
        "post": post,
        "related": related,
        "meta": meta,
        "jsonld": jsonld(article_ld, breadcrumb_ld(crumbs)),
        "nav_active": "blog",
    }
    return render(request, "blog/detail.html", context)
