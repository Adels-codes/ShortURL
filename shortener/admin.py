from django.contrib import admin

from .models import Click, ShortURL


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url', 'owner', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('short_code', 'original_url')
    readonly_fields = ('short_code', 'created_at')


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'clicked_at', 'ip_address')
    list_filter = ('clicked_at',)
    search_fields = ('short_url__short_code', 'ip_address')
