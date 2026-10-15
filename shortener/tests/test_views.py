from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from shortener.models import Click, ShortURL


@override_settings(RATELIMIT_ENABLE=False)
class HomeViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_get_renders_form(self):
        response = self.client.get(reverse('shortener:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shorten a URL')

    def test_post_creates_short_url_and_shows_link(self):
        response = self.client.post(reverse('shortener:home'), {
            'original_url': 'https://www.djangoproject.com',
            'custom_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShortURL.objects.count(), 1)
        self.assertContains(response, 'Your short link')

    def test_post_with_custom_alias(self):
        response = self.client.post(reverse('shortener:home'), {
            'original_url': 'https://www.djangoproject.com',
            'custom_code': 'djcode',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ShortURL.objects.filter(short_code='djcode').exists())

    def test_post_rejects_taken_alias(self):
        ShortURL.objects.create(original_url='https://example.com', short_code='taken')
        response = self.client.post(reverse('shortener:home'), {
            'original_url': 'https://www.djangoproject.com',
            'custom_code': 'taken',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already taken')
        self.assertEqual(ShortURL.objects.filter(short_code='taken').count(), 1)


@override_settings(RATELIMIT_ENABLE=False)
class RedirectViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.short_url = ShortURL.objects.create(
            original_url='https://www.djangoproject.com',
            short_code='djtest',
        )

    def test_redirects_to_original_url(self):
        response = self.client.get(reverse('shortener:redirect', args=['djtest']))
        self.assertRedirects(response, 'https://www.djangoproject.com', fetch_redirect_response=False)

    def test_unknown_code_404s(self):
        response = self.client.get(reverse('shortener:redirect', args=['doesnotexist']))
        self.assertEqual(response.status_code, 404)

    def test_inactive_link_404s(self):
        self.short_url.is_active = False
        self.short_url.save()
        response = self.client.get(reverse('shortener:redirect', args=['djtest']))
        self.assertEqual(response.status_code, 404)

    def test_redirect_records_a_click(self):
        self.client.get(reverse('shortener:redirect', args=['djtest']), HTTP_USER_AGENT='pytest-agent')
        self.assertEqual(Click.objects.filter(short_url=self.short_url).count(), 1)
        click = Click.objects.get(short_url=self.short_url)
        self.assertEqual(click.user_agent, 'pytest-agent')

    def test_stats_page_shows_total_clicks(self):
        self.client.get(reverse('shortener:redirect', args=['djtest']))
        self.client.get(reverse('shortener:redirect', args=['djtest']))
        response = self.client.get(reverse('shortener:stats', args=['djtest']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<strong>2</strong>')


class RateLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_home_post_is_rate_limited_after_ten_requests_per_minute(self):
        client = Client(REMOTE_ADDR='10.0.0.1')
        statuses = []
        for i in range(11):
            response = client.post(reverse('shortener:home'), {
                'original_url': f'https://example.com/{i}',
                'custom_code': '',
            })
            statuses.append(response.status_code)
        self.assertEqual(statuses[:10], [200] * 10)
        self.assertEqual(statuses[10], 403)
