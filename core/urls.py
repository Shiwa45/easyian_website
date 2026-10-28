from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("dialsathi/", views.dialsathi, name="dialsathi"),
    path("about/", views.about, name="about"),
    path("contact/", RedirectView.as_view(pattern_name="core:about", permanent=True), name="contact"),
]
