from django.urls import path

from . import views

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='product_category'),
    path('brand/<slug:brand_slug>/', views.ProductListView.as_view(), name='product_brand'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
