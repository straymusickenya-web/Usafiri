from django.contrib import admin
from django.utils.html import format_html
from .models import DriverProfile, DriverDestination, DriverVehicle

class DriverDestinationInline(admin.TabularInline):
    model = DriverDestination
    extra = 1
    fields = ("name", "is_active", "created_at")
    readonly_fields = ("created_at",)

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'user', 'vehicle_type', 'vehicle_seats',
        'location', 'id_verified', 'is_active_searchable',
        'created_at'
    )
    list_filter = ('vehicle_type', 'id_verified', 'is_active_searchable', 'created_at')
    search_fields = ('full_name', 'id_number', 'phone_number', 'location', 'user__username')
    list_editable = ('id_verified', 'is_active_searchable')
    readonly_fields = ('created_at', 'photo_preview', 'photo_url')
    inlines = [DriverDestinationInline]

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'id_number', 'phone_number')
        }),
        ('Vehicle Information', {
            'fields': ('vehicle_type', 'vehicle_seats')
        }),
        ('Location', {
            'fields': ('location', 'lat', 'lng')
        }),
        ('Verification', {
            'fields': ('id_photo', 'photo_preview', 'photo_url', 'id_verified', 'is_active_searchable')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def photo_preview(self, obj):
        if obj.id_photo:
            return format_html('<img src="{}" style="max-height:150px;" />', obj.id_photo.url)
        return "No image"

    def photo_url(self, obj):
        return obj.id_photo.url if obj.id_photo else "No URL"

@admin.register(DriverVehicle)
class DriverVehicleAdmin(admin.ModelAdmin):
    list_display = ("registration", "make", "model", "color", "is_primary", "driver")
    list_filter = ("is_primary", "make")
    search_fields = ("registration", "driver__full_name")

@admin.register(DriverDestination)
class DriverDestinationAdmin(admin.ModelAdmin):
    list_display = ("driver", "name", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("driver__full_name", "name")

