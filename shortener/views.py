from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django_ratelimit.decorators import ratelimit

from .forms import ShortenForm
from .models import Click, ShortURL, shorturl_cache_key

REDIRECT_CACHE_TTL = 60  # seconds; invalidated immediately on save/delete via signal


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class HomeView(View):
    template_name = 'shortener/home.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ShortenForm()})

    def post(self, request):
        form = ShortenForm(request.POST)
        if form.is_valid():
            short_url = form.save()
            short_link = request.build_absolute_uri(
                reverse('shortener:redirect', args=[short_url.short_code])
            )
            return render(request, self.template_name, {
                'form': ShortenForm(),
                'short_link': short_link,
                'short_url': short_url,
            })
        return render(request, self.template_name, {'form': form})


def redirect_short_url(request, short_code):
    cache_key = shorturl_cache_key(short_code)
    short_url = cache.get(cache_key)
    if short_url is None:
        short_url = get_object_or_404(ShortURL, short_code=short_code)
        cache.set(cache_key, short_url, REDIRECT_CACHE_TTL)

    if not short_url.is_usable:
        raise Http404('This link is no longer active.')

    Click.objects.create(
        short_url=short_url,
        ip_address=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        referrer=request.META.get('HTTP_REFERER', '')[:512],
    )
    return redirect(short_url.original_url)


def stats(request, short_code):
    short_url = get_object_or_404(ShortURL, short_code=short_code)
    clicks = short_url.clicks.all()[:50]
    return render(request, 'shortener/stats.html', {
        'short_url': short_url,
        'clicks': clicks,
        'total_clicks': short_url.clicks.count(),
    })
