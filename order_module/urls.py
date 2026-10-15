from django.urls import path

from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart_page'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout_view, name='checkout_page'),
]
