from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_driver', 'is_client', 'is_staff', 'date_joined')
    list_filter = ('is_driver', 'is_client', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {
            'fields': ('is_driver', 'is_client', 'phone_number')
        }),
    )