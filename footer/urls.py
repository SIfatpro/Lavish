from django.urls import path
from footer import views

urlpatterns = [
    path('',views.footer,name="Home"),
    path('footer/',views.footer),
]