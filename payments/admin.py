from django.contrib import admin
from .models import Payment, DriverAccessGrant

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'driver', 'amount', 'provider', 'status', 'created_at')
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('client__username', 'driver__full_name', 'checkout_request_id', 'merchant_request_id')
    readonly_fields = ('id', 'created_at', 'checkout_request_id', 'merchant_request_id')
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('id', 'client', 'driver', 'amount', 'provider', 'status')
        }),
        ('M-Pesa Details', {
            'fields': ('checkout_request_id', 'merchant_request_id')
        }),
        ('Additional Information', {
            'fields': ('metadata', 'created_at')
        }),
    )

@admin.register(DriverAccessGrant)
class DriverAccessGrantAdmin(admin.ModelAdmin):
    list_display = ('client', 'driver', 'payment', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('client__username', 'driver__full_name')
    readonly_fields = ('created_at',)