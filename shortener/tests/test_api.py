from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from shortener.models import ShortURL


class ShortURLAPITests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_create_short_url(self):
        response = self.client.post(reverse('shortener_api:link-list'), {
            'original_url': 'https://www.python.org',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ShortURL.objects.count(), 1)
        self.assertIn('short_link', response.data)
        self.assertEqual(response.data['click_count'], 0)

    def test_create_with_custom_alias(self):
        response = self.client.post(reverse('shortener_api:link-list'), {
            'original_url': 'https://www.python.org',
            'short_code': 'pycode',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['short_code'], 'pycode')

    def test_create_rejects_taken_alias(self):
        ShortURL.objects.create(original_url='https://example.com', short_code='dup')
        response = self.client.post(reverse('shortener_api:link-list'), {
            'original_url': 'https://www.python.org',
            'short_code': 'dup',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('short_code', response.data)

    def test_is_active_is_read_only_on_create(self):
        response = self.client.post(reverse('shortener_api:link-list'), {
            'original_url': 'https://www.python.org',
            'is_active': False,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_active'])

    def test_list_returns_created_links(self):
        ShortURL.objects.create(original_url='https://example.com', short_code='abc1234')
        response = self.client.get(reverse('shortener_api:link-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_by_short_code(self):
        ShortURL.objects.create(original_url='https://example.com', short_code='abc1234')
        response = self.client.get(reverse('shortener_api:link-detail', args=['abc1234']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_url'], 'https://example.com')

    def test_retrieve_unknown_code_404s(self):
        response = self.client.get(reverse('shortener_api:link-detail', args=['missing']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShortURLAPIThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()

    @patch.object(ScopedRateThrottle, 'THROTTLE_RATES', {'short-url-create': '2/min'})
    def test_third_request_within_a_minute_is_throttled(self):
        statuses = []
        for i in range(3):
            response = self.client.post(reverse('shortener_api:link-list'), {
                'original_url': f'https://example.com/{i}',
            })
            statuses.append(response.status_code)
        self.assertEqual(statuses, [
            status.HTTP_201_CREATED,
            status.HTTP_201_CREATED,
            status.HTTP_429_TOO_MANY_REQUESTS,
        ])
