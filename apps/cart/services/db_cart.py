from apps.cart.models import Cart, CartItem


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_items(user):
    cart = get_or_create_cart(user)
    return cart.items.all()


def add_item(user, product_id: str):
    cart = get_or_create_cart(user)

    CartItem.objects.get_or_create(
        cart=cart,
        product_id=product_id
    )


def remove_item(user, product_id: str):
    CartItem.objects.filter(
        cart__user=user,
        product_id=product_id
    ).delete()


