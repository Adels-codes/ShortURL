from django import forms

from .models import ShortURL


class ShortenForm(forms.ModelForm):
    custom_code = forms.CharField(
        max_length=20,
        required=False,
        help_text='Optional custom alias (letters/numbers only)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'my-alias'}),
    )

    class Meta:
        model = ShortURL
        fields = ['original_url']
        widgets = {
            'original_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/a/very/long/url',
            }),
        }

    def clean_custom_code(self):
        code = self.cleaned_data.get('custom_code')
        if code:
            if not code.isalnum():
                raise forms.ValidationError('Alias must be alphanumeric.')
            if ShortURL.objects.filter(short_code=code).exists():
                raise forms.ValidationError('That alias is already taken.')
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        custom_code = self.cleaned_data.get('custom_code')
        if custom_code:
            instance.short_code = custom_code
        if commit:
            instance.save()
        return instance
