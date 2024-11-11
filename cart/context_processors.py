from django.db.models import Sum
from cart.models import CartItem  # Make sure to import your CartItem model


def cart_item_count(request):
    if request.user.is_authenticated:
        total_cart_count = (
            CartItem.objects.filter(cart__user=request.user, cart__is_paid=False)
            .aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        )
        print("Authenticated user cart count:", total_cart_count)  # Debug print
    else:
        total_cart_count = 0  # Handle case for unauthenticated users
        print("Unauthenticated user cart count: 0")  # Debug print

    return {
        'cart_item_count': total_cart_count,
    }
