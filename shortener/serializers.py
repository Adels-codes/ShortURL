from django.urls import reverse
from rest_framework import serializers

from .models import ShortURL


class ShortURLSerializer(serializers.ModelSerializer):
    short_code = serializers.CharField(required=False)
    short_link = serializers.SerializerMethodField()
    click_count = serializers.IntegerField(source='clicks.count', read_only=True)

    class Meta:
        model = ShortURL
        fields = [
            'id', 'original_url', 'short_code', 'short_link',
            'click_count', 'created_at', 'expires_at', 'is_active',
        ]
        read_only_fields = ['id', 'created_at', 'is_active']

    def get_short_link(self, obj):
        path = reverse('shortener:redirect', args=[obj.short_code])
        request = self.context.get('request')
        return request.build_absolute_uri(path) if request else path

    def validate_short_code(self, value):
        if not value:
            return value
        if not value.isalnum():
            raise serializers.ValidationError('Alias must be alphanumeric.')
        if ShortURL.objects.filter(short_code=value).exists():
            raise serializers.ValidationError('That alias is already taken.')
        return value
