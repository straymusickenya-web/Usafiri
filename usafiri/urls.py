from django.contrib import admin
from django.urls import path, include
from core import views as core_views


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', core_views.home, name='home'),
    path('', include(('core.urls', 'core'), namespace='core')),

    # path('about/', core_views.about, name='about'),
    # path('terms/', core_views.terms, name='terms'),
    # path('contact/', core_views.contact, name='contact'),
    path('accounts/', include('accounts.urls')),
    path('drivers/', include('drivers.urls')),
    path('payments/', include('payments.urls')),
    path('ratings/', include('ratings.urls')),
    path('captcha/', include('captcha.urls')),
    path('contact/', core_views.contact, name='contact'),
]
