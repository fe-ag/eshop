"""
Cart logic. Logged-in users have a database cart, guests a session cart. Prices, stock and
availability are always read from the database, never from data sent by the browser.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from product_module.models import ProductVariant

from .models import Cart, CartItem

SESSION_KEY = 'cart'


def max_per_item():
    return getattr(settings, 'CART_MAX_QUANTITY_PER_ITEM', 10)


def variant_is_purchasable(variant):
    product = variant.product
    return bool(
        variant.is_active and product.is_active and product.brand.is_active and product.category.is_active
    )


@dataclass
class CartLine:
    variant: object
    stored_quantity: int
    quantity: int
    available: bool
    note: str = ''

    @property
    def unit_price(self):
        return self.variant.effective_price

    @property
    def list_price(self):
        return self.variant.price

    @property
    def has_discount(self):
        return self.variant.has_discount

    @property
    def line_total(self):
        return self.unit_price * self.quantity if self.available else Decimal('0')


def _variant_queryset():
    return ProductVariant.objects.select_related(
        'product', 'product__brand', 'product__category', 'storage', 'color')


def build_line(variant, stored_quantity):
    if not variant_is_purchasable(variant):
        return CartLine(variant, stored_quantity, 0, False, 'This item is no longer available.')
    if variant.stock <= 0:
        return CartLine(variant, stored_quantity, 0, False, 'This item is out of stock.')
    limit = min(variant.stock, max_per_item())
    quantity = max(1, min(stored_quantity, limit))
    note = ''
    if quantity < stored_quantity:
        note = f'Only {limit} available - quantity adjusted.'
    return CartLine(variant, stored_quantity, quantity, True, note)


class CartService:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

    # ---- raw storage -------------------------------------------------------------
    def _session_cart(self):
        data = self.request.session.get(SESSION_KEY)
        if not isinstance(data, dict):
            data = {}
        clean = {}
        for key, value in data.items():
            try:
                clean[int(key)] = int(value)
            except (TypeError, ValueError):
                continue
        return clean

    def _save_session_cart(self, data):
        self.request.session[SESSION_KEY] = {str(k): int(v) for k, v in data.items()}
        self.request.session.modified = True

    def _db_cart(self):
        cart, _created = Cart.objects.get_or_create(user=self.user)
        return cart

    def stored_quantities(self):
        """Mapping variant_id -> stored quantity (in insertion order)."""
        if self.user:
            items = CartItem.objects.filter(cart__user=self.user).order_by('added_at', 'id')
            return {item.variant_id: item.quantity for item in items}
        return self._session_cart()

    # ---- reading -----------------------------------------------------------------
    def lines(self):
        quantities = self.stored_quantities()
        if not quantities:
            return []
        variants = {v.pk: v for v in _variant_queryset().filter(pk__in=quantities.keys())}
        lines = []
        for variant_id, stored in quantities.items():
            variant = variants.get(variant_id)
            if variant is not None:
                lines.append(build_line(variant, stored))
        return lines

    def count(self):
        return sum(self.stored_quantities().values())

    def total(self, lines=None):
        lines = self.lines() if lines is None else lines
        return sum((line.line_total for line in lines), Decimal('0'))

    # ---- writing -----------------------------------------------------------------
    def _get_variant(self, variant_id):
        try:
            return _variant_queryset().get(pk=int(variant_id))
        except (TypeError, ValueError, ProductVariant.DoesNotExist):
            return None

    @staticmethod
    def parse_quantity(raw):
        """Return an int, or None when the value is missing or not a whole number."""
        try:
            return int(str(raw).strip())
        except (TypeError, ValueError):
            return None

    def _write(self, variant_id, quantity):
        if self.user:
            cart = self._db_cart()
            if quantity <= 0:
                CartItem.objects.filter(cart=cart, variant_id=variant_id).delete()
            else:
                CartItem.objects.update_or_create(
                    cart=cart, variant_id=variant_id, defaults={'quantity': quantity})
        else:
            data = self._session_cart()
            if quantity <= 0:
                data.pop(variant_id, None)
            else:
                data[variant_id] = quantity
            self._save_session_cart(data)

    def add(self, variant_id, quantity):
        """Add `quantity` of a variant. Returns (ok, message)."""
        variant = self._get_variant(variant_id)
        if variant is None or not variant_is_purchasable(variant):
            return False, 'This product is not available.'
        if quantity < 1:
            return False, 'Quantity must be at least 1.'
        if variant.stock <= 0:
            return False, 'Sorry, this version is out of stock.'
        limit = min(variant.stock, max_per_item())
        current = self.stored_quantities().get(variant.pk, 0)
        wanted = current + quantity
        if wanted > limit:
            self._write(variant.pk, limit)
            return True, f'Only {limit} available - your cart now holds {limit}.'
        self._write(variant.pk, wanted)
        return True, f'{variant.product.name} was added to your cart.'

    def set_quantity(self, variant_id, quantity):
        variant = self._get_variant(variant_id)
        if variant is None or variant.pk not in self.stored_quantities():
            return False, 'This item is not in your cart.'
        if quantity < 1:
            self._write(variant.pk, 0)
            return True, 'Item removed from your cart.'
        if not variant_is_purchasable(variant) or variant.stock <= 0:
            return False, 'This item is not available right now.'
        limit = min(variant.stock, max_per_item())
        if quantity > limit:
            self._write(variant.pk, limit)
            return True, f'Only {limit} available - quantity set to {limit}.'
        self._write(variant.pk, quantity)
        return True, 'Cart updated.'

    def remove(self, variant_id):
        try:
            variant_id = int(variant_id)
        except (TypeError, ValueError):
            return False, 'This item is not in your cart.'
        if variant_id not in self.stored_quantities():
            return False, 'This item is not in your cart.'
        self._write(variant_id, 0)
        return True, 'Item removed from your cart.'


@transaction.atomic
def merge_session_cart_into_user(request, user):
    """Move the guest (session) cart into the user's database cart after login."""
    data = request.session.get(SESSION_KEY)
    if not isinstance(data, dict) or not data:
        return
    cart, _created = Cart.objects.get_or_create(user=user)
    existing = {item.variant_id: item for item in CartItem.objects.filter(cart=cart)}
    variants = {v.pk: v for v in _variant_queryset().filter(pk__in=[int(k) for k in data if str(k).isdigit()])}
    for key, raw_quantity in data.items():
        try:
            variant_id, quantity = int(key), int(raw_quantity)
        except (TypeError, ValueError):
            continue
        variant = variants.get(variant_id)
        if variant is None or quantity < 1 or not variant_is_purchasable(variant) or variant.stock <= 0:
            continue
        limit = min(variant.stock, max_per_item())
        item = existing.get(variant_id)
        if item:
            item.quantity = min(limit, item.quantity + quantity)
            item.save(update_fields=['quantity'])
        else:
            CartItem.objects.create(cart=cart, variant=variant, quantity=min(limit, quantity))
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
