from rest_framework import generics, permissions
from rest_framework.throttling import ScopedRateThrottle

from .models import ShortURL
from .serializers import ShortURLSerializer


class ShortURLListCreateAPIView(generics.ListCreateAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'short-url-create'


class ShortURLDetailAPIView(generics.RetrieveAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer
    lookup_field = 'short_code'
    permission_classes = [permissions.AllowAny]
