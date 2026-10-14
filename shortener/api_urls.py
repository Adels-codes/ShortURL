from django.urls import path

from . import api_views

app_name = 'shortener_api'

urlpatterns = [
    path('links/', api_views.ShortURLListCreateAPIView.as_view(), name='link-list'),
    path('links/<str:short_code>/', api_views.ShortURLDetailAPIView.as_view(), name='link-detail'),
]
