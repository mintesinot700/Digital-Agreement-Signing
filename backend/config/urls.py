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
from django.views.static import serve as media_serve
from django.views.generic import TemplateView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('agreement.urls')),
]

# Uploaded media files. django.conf.urls.static.static() is a no-op when
# DEBUG=False, which would 404 every uploaded photo/signature in production —
# serve explicitly in all modes instead (a proxy/CDN can take over later).
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]

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
