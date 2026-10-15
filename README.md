# Shrtnr — a Django URL shortener

A small but complete URL-shortening service built with Django. Beyond the
basic "long URL in, short code out" flow, it covers a few things that show
up in real services: per-click analytics, a REST API, rate limiting, and
cache-backed redirects with signal-based invalidation.

## Features

- **Shorten URLs** with an auto-generated 7-character code (via `shortuuid`)
  or an optional custom alias.
- **Click analytics** — every redirect logs IP, user agent, and referrer;
  a per-link stats page shows total clicks and recent activity.
- **REST API** (Django REST Framework) to create, list, and retrieve short
  links programmatically.
- **Rate limiting** — link creation is capped at 10/min per IP, both on the
  HTML form (`django-ratelimit`) and the API (DRF `ScopedRateThrottle`).
- **Cached redirects** — the redirect lookup is cached, with a model signal
  invalidating the cache entry immediately on save/delete so edits (e.g.
  deactivating a link) take effect without waiting out the TTL.
- **Django admin** for inspecting links and clicks.

## Tech stack

Django 6, Django REST Framework, django-ratelimit, shortuuid, SQLite (dev),
Bootstrap 5 (CDN, no build step).

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to shorten a link, or `/admin/` to browse
links and clicks directly.

## REST API

| Method | Endpoint                 | Description                          |
|--------|--------------------------|---------------------------------------|
| GET    | `/api/links/`            | List short links (paginated)         |
| POST   | `/api/links/`            | Create a short link                  |
| GET    | `/api/links/<code>/`     | Retrieve a link by its short code    |

Create a link:

```bash
curl -X POST http://127.0.0.1:8000/api/links/ \
  -d "original_url=https://www.djangoproject.com" \
  -d "short_code=django"   # optional custom alias
```

```json
{
  "id": 1,
  "original_url": "https://www.djangoproject.com",
  "short_code": "django",
  "short_link": "http://127.0.0.1:8000/django/",
  "click_count": 0,
  "created_at": "2026-10-14T15:30:00Z",
  "expires_at": null,
  "is_active": true
}
```

`short_code` must be alphanumeric and unique; `is_active` is read-only on
create (always `true`) so a client can't accidentally deactivate a link by
omitting the field. Creation is throttled to 10 requests/min per client.

## Running tests

```bash
python manage.py test shortener
```

25 tests covering model behavior (code generation, expiry, cache
invalidation), the form/redirect/stats views (including rate limiting),
and the API (CRUD, validation, throttling).

## Notes on the caching setup

Redirect lookups are cached via Django's cache framework, configured here
with `LocMemCache` for simplicity. A `post_save`/`post_delete` signal on
`ShortURL` deletes the corresponding cache entry, so changes made through
the admin or API are reflected immediately rather than after the TTL
expires. `LocMemCache` is per-process — in a multi-process/production
deployment, swap `CACHES['default']['BACKEND']` for a shared backend such
as `django_redis.cache.RedisCache` so all workers see the same cache and
invalidation.

## Project structure

```
config/             Django project settings, root URLconf
shortener/
  models.py         ShortURL, Click
  forms.py          ShortenForm (HTML form, with custom-alias validation)
  views.py          Home (shorten), redirect, stats
  serializers.py     DRF serializer for the API
  api_views.py       DRF generic views
  tests/             Model, view, and API test suites
templates/          Base layout + shortener templates (Bootstrap 5)
```
