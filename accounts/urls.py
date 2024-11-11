from django.urls import path # type: ignore
from accounts import views

app_name = 'accounts'  # Ensure this line is present

urlpatterns = [
    # User authentication URLs
    path('login/', views.login, name='login'),  # User login page
    path('register/', views.register, name='register'),  # User registration page
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),  # Add user_id parameter
    path('logout/', views.logout_view, name='logout'),  # User logout action

    # Custom Password Reset URLs
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),

    # User-related URLs
    path('user_accounts/', views.user_accounts, name='user_accounts'),  # User accounts page
    path('updateuser_accounts/', views.updateuser_accounts, name='updateuser_accounts'), 
    path('user_order/', views.user_order, name='user_order'),  # User orders page
    path('user_wishlist/', views.user_wishlist, name='user_wishlist'),  # User wishlist page
    path('user_review/', views.user_review, name='user_review'),  # User reviews page
    path('user_ratings/', views.user_ratings, name='user_ratings'),  # User ratings page
    path('user_coupon/', views.user_coupon, name='user_coupon'),  # User coupons page
]
