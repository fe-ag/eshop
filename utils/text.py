from django.utils.text import slugify


def unique_slug(model, value, instance=None, field='slug', max_length=140, fallback='item'):
    """Return a slug based on `value` that is unique for `model`."""
    base = slugify(value)[:max_length] or fallback
    slug = base
    counter = 2
    queryset = model.objects.all()
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(**{field: slug}).exists():
        suffix = f'-{counter}'
        slug = f'{base[:max_length - len(suffix)]}{suffix}'
        counter += 1
    return slug
