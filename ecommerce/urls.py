"""
URL configuration for Marazzo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from Marazzo import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

app_name = 'ecommerce'  # Ensure this line is present

urlpatterns = [
    path('', views.index, name='index'),  
    path('index/', views.index, name='index'),  
    path('track-orders/', views.track, name='track_orders'),
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),  # This should be present
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('load-more/', views.load_more, name='load_more'),  # Use underscores instead of hyphens
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




