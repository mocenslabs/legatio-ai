"""Health check URL configuration."""

from django.urls import path

from core.health import views

app_name = "health"

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("ready/", views.readiness_check, name="readiness-check"),
]
