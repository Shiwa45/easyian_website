import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from .models import BlockedSubmission, Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "company", "interests", "team_size", "status", "assigned_to", "created_at")
    list_filter = ("status", "team_size", "created_at", "utm_source", "assigned_to")
    list_editable = ("status", "assigned_to")
    search_fields = ("name", "phone", "email", "company", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("source_page", "utm_source", "utm_medium", "utm_campaign", "ip_address",
                       "user_agent", "created_at", "updated_at")
    fieldsets = (
        ("Contact", {"fields": ("name", "company", "phone", "email", "team_size", "interests", "message")}),
        ("Follow-up", {"fields": ("status", "assigned_to", "notes")}),
        ("Tracking", {"classes": ("collapse",), "fields": readonly_fields}),
    )
    actions = ("export_csv", "mark_contacted", "mark_junk")

    @admin.action(description="Export selected leads to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        stamp = timezone.localtime().strftime("%Y%m%d-%H%M")
        response["Content-Disposition"] = f'attachment; filename="easyian-leads-{stamp}.csv"'
        response.write("﻿")  # BOM so Excel opens UTF-8 correctly
        writer = csv.writer(response)
        cols = ["created_at", "name", "company", "phone", "email", "team_size", "interests", "message",
                "status", "source_page", "utm_source", "utm_medium", "utm_campaign"]
        writer.writerow(cols)
        for lead in queryset:
            row = []
            for col in cols:
                value = getattr(lead, col)
                if col == "created_at":
                    value = timezone.localtime(value).strftime("%Y-%m-%d %H:%M")
                row.append(value)
            writer.writerow(row)
        return response

    @admin.action(description="Mark as contacted")
    def mark_contacted(self, request, queryset):
        queryset.update(status=Lead.Status.CONTACTED)

    @admin.action(description="Mark as junk")
    def mark_junk(self, request, queryset):
        queryset.update(status=Lead.Status.JUNK)


@admin.register(BlockedSubmission)
class BlockedSubmissionAdmin(admin.ModelAdmin):
    list_display = ("reason", "ip_address", "created_at")
    list_filter = ("reason", "created_at")
    readonly_fields = ("reason", "ip_address", "user_agent", "payload", "created_at")

    def has_add_permission(self, request):
        return False
