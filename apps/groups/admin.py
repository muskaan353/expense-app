from django.contrib import admin

from apps.groups.models import Group, GroupMembership


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "base_currency", "created_at", "archived_at")
    list_filter = ("base_currency", "archived_at")
    search_fields = ("name", "owner__email")


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "role", "joined_at", "left_at")
    list_filter = ("role",)
    search_fields = ("group__name", "user__email")
