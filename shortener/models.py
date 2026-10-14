import shortuuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_short_code():
    length = getattr(settings, 'SHORT_CODE_LENGTH', 7)
    for _ in range(5):
        code = shortuuid.ShortUUID().random(length=length)
        if not ShortURL.objects.filter(short_code=code).exists():
            return code
    raise RuntimeError('Could not generate a unique short code, try increasing SHORT_CODE_LENGTH')


class ShortURL(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=20, unique=True, db_index=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='short_urls',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.short_code} -> {self.original_url}'

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = generate_short_code()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    @property
    def is_usable(self):
        return self.is_active and not self.is_expired
