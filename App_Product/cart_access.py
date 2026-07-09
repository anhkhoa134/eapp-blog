from App_Quanly.models import CommerceBehaviorConfig

from .models import Cart, CartItem, Product, Wishlist


def commerce_behavior():
    return CommerceBehaviorConfig.load()


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_cart_for_request(request, create=False):
    if request.user.is_authenticated:
        if create:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        return Cart.objects.filter(user=request.user).first()

    config = commerce_behavior()
    if not config.allow_guest_cart:
        return None

    session_key = ensure_session_key(request) if create else request.session.session_key
    if not session_key:
        return None

    if create:
        cart, _ = Cart.objects.get_or_create(user=None, session_key=session_key)
        return cart
    return Cart.objects.filter(user=None, session_key=session_key).first()


def get_owned_cart_item(request, cart_item_id):
    cart = get_cart_for_request(request)
    if not cart:
        return None
    return CartItem.objects.filter(id=cart_item_id, cart=cart).select_related('product', 'variant').first()


def wishlist_product_ids(request):
    if request.user.is_authenticated:
        return set(request.user.wishlist.values_list('product_id', flat=True))

    config = commerce_behavior()
    session_key = request.session.session_key
    if not config.allow_guest_wishlist or not session_key:
        return set()

    return set(Wishlist.objects.filter(user=None, session_key=session_key).values_list('product_id', flat=True))


def get_wishlist_items_for_request(request):
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user).select_related('product', 'product__category').order_by('-added_at')

    config = commerce_behavior()
    session_key = request.session.session_key
    if not config.allow_guest_wishlist or not session_key:
        return Wishlist.objects.none()

    return Wishlist.objects.filter(user=None, session_key=session_key).select_related('product', 'product__category').order_by('-added_at')


def add_product_to_wishlist(request, product):
    if request.user.is_authenticated:
        return Wishlist.objects.get_or_create(user=request.user, product=product)

    config = commerce_behavior()
    if not config.allow_guest_wishlist:
        return None, False

    session_key = ensure_session_key(request)
    return Wishlist.objects.get_or_create(user=None, session_key=session_key, product=product)


def remove_product_from_wishlist(request, product):
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user, product=product).delete()

    config = commerce_behavior()
    session_key = request.session.session_key
    if not config.allow_guest_wishlist or not session_key:
        return 0, {}

    return Wishlist.objects.filter(user=None, session_key=session_key, product=product).delete()


def merge_guest_commerce_to_user(request, user, old_session_key):
    if not old_session_key:
        return

    guest_cart = Cart.objects.filter(user=None, session_key=old_session_key).prefetch_related('items').first()
    if guest_cart:
        user_cart, _ = Cart.objects.get_or_create(user=user)
        for item in guest_cart.items.all():
            cart_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=item.product,
                variant=item.variant,
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save(update_fields=['quantity'])
            else:
                cart_item.quantity = item.quantity
                cart_item.save(update_fields=['quantity'])
        guest_cart.delete()

    guest_wishlist = Wishlist.objects.filter(user=None, session_key=old_session_key).select_related('product')
    for item in guest_wishlist:
        if isinstance(item.product, Product):
            Wishlist.objects.get_or_create(user=user, product=item.product)
    guest_wishlist.delete()
