"""Helpers that keep uploaded files safe: a file is removed only when nothing else uses it."""
from django.apps import apps
from django.db import models


def file_reference_count(name):
    """Count how many model rows reference the stored file `name`."""
    if not name:
        return 0
    total = 0
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, models.FileField) and not field.many_to_many:
                total += model._default_manager.filter(**{field.name: name}).count()
    return total


def delete_file_if_unused(file_field):
    """Delete the physical file of `file_field` when no database row references it any more."""
    name = getattr(file_field, 'name', '') or ''
    if not name:
        return False
    if file_reference_count(name) > 0:
        return False
    try:
        file_field.storage.delete(name)
    except Exception:
        return False
    return True


def delete_stored_file_if_unused(storage, name):
    """Same as delete_file_if_unused but for a (storage, name) pair that no longer sits on a model."""
    if not name or file_reference_count(name) > 0:
        return False
    try:
        storage.delete(name)
    except Exception:
        return False
    return True
