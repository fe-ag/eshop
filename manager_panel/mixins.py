from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url


def is_manager(user):
    """Server-side rule for the management panel: an active staff member or superuser."""
    return bool(user.is_authenticated and user.is_active and (user.is_staff or user.is_superuser))


class ManagerRequiredMixin(AccessMixin):
    login_url = 'manage_login'
    raise_exception = False
    permission_denied_message = 'You do not have permission to open the management panel.'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_manager(request.user):
            raise PermissionDenied(self.permission_denied_message)
        return super().dispatch(request, *args, **kwargs)


def manager_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), resolve_url('manage_login'))
        if not is_manager(request.user):
            raise PermissionDenied('You do not have permission to open the management panel.')
        return view(request, *args, **kwargs)
    return wrapper
