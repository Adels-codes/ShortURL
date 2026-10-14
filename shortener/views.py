from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from .forms import ShortenForm
from .models import ShortURL


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
    short_url = get_object_or_404(ShortURL, short_code=short_code)
    if not short_url.is_usable:
        raise Http404('This link is no longer active.')
    return redirect(short_url.original_url)
