from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from shortener.models import ShortURL, shorturl_cache_key


class ShortURLModelTests(TestCase):
    def test_short_code_is_auto_generated(self):
        short_url = ShortURL.objects.create(original_url='https://example.com')
        self.assertTrue(short_url.short_code)
        self.assertEqual(len(short_url.short_code), 7)

    def test_custom_short_code_is_preserved(self):
        short_url = ShortURL.objects.create(
            original_url='https://example.com',
            short_code='my-alias',
        )
        self.assertEqual(short_url.short_code, 'my-alias')

    def test_is_usable_true_by_default(self):
        short_url = ShortURL.objects.create(original_url='https://example.com')
        self.assertTrue(short_url.is_usable)

    def test_is_usable_false_when_inactive(self):
        short_url = ShortURL.objects.create(original_url='https://example.com', is_active=False)
        self.assertFalse(short_url.is_usable)

    def test_is_usable_false_when_expired(self):
        short_url = ShortURL.objects.create(
            original_url='https://example.com',
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(short_url.is_expired)
        self.assertFalse(short_url.is_usable)

    def test_save_invalidates_cache_entry(self):
        short_url = ShortURL.objects.create(original_url='https://example.com')
        cache_key = shorturl_cache_key(short_url.short_code)
        cache.set(cache_key, short_url, 60)
        self.assertIsNotNone(cache.get(cache_key))

        short_url.is_active = False
        short_url.save()

        self.assertIsNone(cache.get(cache_key))

    def test_delete_invalidates_cache_entry(self):
        short_url = ShortURL.objects.create(original_url='https://example.com')
        cache_key = shorturl_cache_key(short_url.short_code)
        cache.set(cache_key, short_url, 60)

        short_url.delete()

        self.assertIsNone(cache.get(cache_key))
