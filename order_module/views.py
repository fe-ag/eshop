from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .cart import CartService


def _back(request, default='cart_page'):
    target = request.POST.get('next') or ''
    if target and url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(target)
    return redirect(default)


def cart_view(request):
    service = CartService(request)
    lines = service.lines()
    return render(request, 'order_module/cart.html', {
        'lines': lines,
        'total': service.total(lines),
        'has_unavailable': any(not line.available for line in lines),
        'has_items': bool(lines),
    })


@require_POST
def cart_add(request):
    service = CartService(request)
    quantity = service.parse_quantity(request.POST.get('quantity', '1'))
    if quantity is None:
        messages.error(request, 'Please enter a valid quantity.')
        return _back(request)
    ok, message = service.add(request.POST.get('variant_id'), quantity)
    (messages.success if ok else messages.error)(request, message)
    return _back(request)


@require_POST
def cart_update(request):
    service = CartService(request)
    quantity = service.parse_quantity(request.POST.get('quantity'))
    if quantity is None:
        messages.error(request, 'Please enter a valid quantity.')
        return redirect('cart_page')
    ok, message = service.set_quantity(request.POST.get('variant_id'), quantity)
    (messages.success if ok else messages.error)(request, message)
    return redirect('cart_page')


@require_POST
def cart_remove(request):
    ok, message = CartService(request).remove(request.POST.get('variant_id'))
    (messages.success if ok else messages.error)(request, message)
    return redirect('cart_page')


@login_required
def checkout_view(request):
    """Checkout requires login. Payments are intentionally not implemented yet."""
    service = CartService(request)
    lines = service.lines()
    purchasable = [line for line in lines if line.available]
    if not purchasable:
        messages.error(request, 'Your cart has no available items.')
        return redirect('cart_page')
    return render(request, 'order_module/checkout.html', {
        'lines': lines,
        'total': service.total(lines),
    })
