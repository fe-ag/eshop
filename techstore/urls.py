from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from site_module import views as site_views

urlpatterns = [
    path('manage/', include('manager_panel.urls')),
    path('account/', include('account_module.urls')),
    path('products/', include('product_module.urls')),
    path('', include('order_module.urls')),
    path('pages/<slug:slug>/', site_views.content_page, name='content_page'),
    path('', include('home_module.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
