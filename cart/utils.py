from cart.models import Cart, CartItem
from products.models import ProductVariant
from django.db.models import Sum

class CartHandler:
    def __init__(self, user, session):
        self.user = user
        self.session = session
        self.session_cart = session.get('cart', [])

    def get_cart_item(self, item_id):
        """Fetch the CartItem based on the provided item_id and ensure related product_variant is included."""
        try:
            # Fetch CartItem along with the related product_variant for easier access
            cart_item = CartItem.objects.get(id=item_id, cart__user=self.user)
            return cart_item
        except CartItem.DoesNotExist:
            return None  # Return None or handle the exception as needed

    def remove_from_cart(self, product_variant_id):
        """Remove a product variant from the cart."""
        if self.user.is_authenticated:
            cart = Cart.objects.filter(user=self.user, is_paid=False).first()
            if cart:
                try:
                    cart_item = CartItem.objects.get(cart=cart, product_variant_id=product_variant_id)
                    cart_item.delete()

                    # Check if the cart is now empty
                    if not cart.items.exists():
                        cart.subtotal_after_discount = 0  # Ensure this field exists in your model
                        cart.grand_total = 0  # Ensure this field exists in your model
                        cart.save()

                except CartItem.DoesNotExist:
                    pass
        else:
            # For session-based cart, similar logic could be applied
            self.session_cart = [item for item in self.session_cart if item['product_variant_id'] != product_variant_id]
            self.session['cart'] = self.session_cart
            self.session.modified = True  # Make sure the session is saved after modification

    def get_cart_items(self):
        """Retrieve all items in the user's cart, including the related product_variant data."""
        if self.user.is_authenticated:
            cart = Cart.objects.filter(user=self.user, is_paid=False).first()
            # Use select_related to fetch product_variant efficiently with each cart item
            return cart.items.select_related('product_variant').all() if cart else []
        return self.session_cart

    def get_total_items_count(self):
        """Calculate the total quantity of items in the cart."""
        if self.user.is_authenticated:
            cart = Cart.objects.filter(user=self.user, is_paid=False).first()
            if cart:
                return cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
            return 0
        # For session-based cart (unauthenticated user)
        return sum(item.get('quantity', 0) for item in self.session_cart)

    def get_total_price(self):
        """Calculate the total price of items in the cart."""
        total_price = 0
        if self.user.is_authenticated:
            cart = Cart.objects.filter(user=self.user, is_paid=False).first()
            if cart:
                total_price = sum(item.total_price for item in cart.items.all())  # Assuming total_price is a property
        else:
            for item in self.session_cart:
                # Get the price of the product_variant by its ID
                try:
                    product_variant = ProductVariant.objects.get(id=item['product_variant_id'])
                    total_price += product_variant.current_price * item['quantity']
                except ProductVariant.DoesNotExist:
                    continue  # Skip if the product variant does not exist

        return total_price
