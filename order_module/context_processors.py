from .cart import CartService


def cart_context(request):
    if request.path.startswith('/manage/') or not hasattr(request, 'session'):
        return {'cart_count': 0}
    return {'cart_count': CartService(request).count()}
