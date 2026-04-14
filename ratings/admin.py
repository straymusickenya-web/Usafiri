from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('client', 'driver', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('client__username', 'driver__full_name', 'comment')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('client', 'driver', 'score', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )