# cart/urls.py

from django.urls import path
from . import views

app_name = 'cart'  # Add this line

urlpatterns = [
    path('', views.cart, name='cart'),  # Main cart view
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Add product to cart
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),  # Remove item from cart
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),  # Update item quantity in cart
    path('update-cart-count/', views.update_cart_count, name='update_cart_count'),  # Update total cart item count
    path('checkout/', views.checkout, name='checkout'),  # Checkout view
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),  # Apply coupon to cart
    path('get_cities/<int:division_id>/', views.get_cities, name='get_cities'),
    path('get_areas/<int:city_id>/', views.get_areas, name='get_areas'),
    path('payment-gateway/', views.payment_gateway, name='payment_gateway'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
]
