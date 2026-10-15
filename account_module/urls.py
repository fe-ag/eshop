from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='account_register'),
    path('login/', views.LoginView.as_view(), name='account_login'),
    path('logout/', views.logout_view, name='account_logout'),
    path('', views.account_view, name='account_page'),
    path('password/', views.change_password_view, name='account_password'),
]
