"""
Root URL configuration.

- /django-admin/  Django admin (moved off /admin/ because the React SPA uses
                  /admin/dashboard as a client-side route)
- /api/     REST API (Accounts + agreement apps)
- /media/   uploaded files (served in all modes for simplicity behind a proxy;
            access control for sensitive media can be added later)
- /         React SPA (production build) with client-side routing fallback
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/', include('Accounts.urls')),
    path('api/', include('agreement.urls')),
]

# Uploaded media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# React SPA catch-all: any non-API route serves the built index.html so that
# client-side routes like /admin/dashboard survive a hard refresh.
if settings.REACT_BUILD_DIR.exists():
    urlpatterns += [
        re_path(
            r'^(?!api/|django-admin/|media/|static/).*$',
            TemplateView.as_view(template_name='index.html'),
            name='react-spa',
        ),
    ]
