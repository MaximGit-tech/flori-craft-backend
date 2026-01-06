from apps.cart.models import Cart, CartItem


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

def get_items(user):
    cart = get_or_create_cart(user)
    return list(
        cart.items.values('product_id')
    )


