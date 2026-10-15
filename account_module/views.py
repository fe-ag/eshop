from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_POST

from .forms import AddressForm, LoginForm, ProfileForm, RegisterForm


def get_safe_next(request, default='home_page'):
    """Return the `next` redirect target only when it stays on this site."""
    target = request.POST.get('next') or request.GET.get('next') or ''
    if target and url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse(default)


class RegisterView(View):
    template_name = 'account_module/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home_page')
        return render(request, self.template_name, {'form': RegisterForm(), 'next': request.GET.get('next', '')})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home_page')
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created. Welcome!')
            return redirect(get_safe_next(request))
        return render(request, self.template_name, {'form': form, 'next': request.POST.get('next', '')})


class LoginView(View):
    template_name = 'account_module/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(get_safe_next(request))
        return render(request, self.template_name, {'form': LoginForm(), 'next': request.GET.get('next', '')})

    def post(self, request):
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login(request, form.user)
            messages.success(request, 'You are now signed in.')
            return redirect(get_safe_next(request))
        return render(request, self.template_name, {'form': form, 'next': request.POST.get('next', '')})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('home_page')


@login_required
def account_view(request):
    profile_form = ProfileForm(instance=request.user)
    address_form = AddressForm(instance=request.user)
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'profile':
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your personal information has been updated.')
                return redirect('account_page')
        elif form_type == 'address':
            address_form = AddressForm(request.POST, instance=request.user)
            if address_form.is_valid():
                address_form.save()
                messages.success(request, 'Your address has been updated.')
                return redirect('account_page')
    return render(request, 'account_module/account.html', {
        'profile_form': profile_form,
        'address_form': address_form,
    })


@login_required
def change_password_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Your password has been changed.')
        return redirect('account_page')
    return render(request, 'account_module/change_password.html', {'form': form})
