from apps.cart.models import Cart, CartItem


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_items(user):
    cart = get_or_create_cart(user)
    return cart.items.all()


def add_item(user, item_data: dict):
    cart = get_or_create_cart(user)

    CartItem.objects.update_or_create(
        cart=cart,
        product_id=item_data['product_id'],
        size=item_data.get('size'),
        defaults={
            'title': item_data['title'],
            'price': item_data['price'],
            'image': item_data['image'],
        }
    )


def remove_item(user, item_data: dict):
    CartItem.objects.filter(
        cart__user=user,
        product_id=item_data['product_id'],
        size=item_data.get('size'),
    ).delete()


