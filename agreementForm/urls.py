from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers  
from agreement import views

router = routers.DefaultRouter()
router.register(r'agreements', views.AgreementCreateView, basename='agreement')

# Redirect to the API root
# This will redirect the root URL to 'api/'
urlpatterns = [
    path('', RedirectView.as_view(url='api/')), 
    path('admin/', admin.site.urls),
    path('api/', include('Accounts.urls')),
    path('api/', include('agreement.urls')),
    
]

# Static and media files settings
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
