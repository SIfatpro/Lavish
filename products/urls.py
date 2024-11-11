from django.urls import path # type: ignore
from . import views

app_name = 'products'  # This defines the 'product' namespace

urlpatterns = [
    path('detail/<slug:product_slug>/', views.product_detail, name='product_detail'),
]
