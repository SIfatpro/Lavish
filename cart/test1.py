from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from products.models import Product, ProductVariant
from accounts.models import ShippingAddress, BillingAddress  # Import your address models
from ecommerce.models import Category, SubCategory

User = get_user_model()

# Coupon Model
from django.db import models
from django.utils import timezone
from django.conf import settings

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.PositiveIntegerField(null=True, blank=True)
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(default=0)  # Maximum number of times this coupon can be used
    uses_count = models.PositiveIntegerField(default=0)  # Total number of times the coupon has been used
    applicable_to = models.ManyToManyField(Product, blank=True)  # Products to which the coupon applies
    applicable_categories = models.ManyToManyField(Category, blank=True)  # Categories for which the coupon is valid
    applicable_subcategories = models.ManyToManyField(SubCategory, blank=True)  # Subcategories for which the coupon is valid
    user_group = models.ManyToManyField(User, blank=True)  # Users for whom the coupon is valid (if needed)
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Minimum purchase amount to use the coupon
    used_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='coupons_used', blank=True)  # Users who have used this coupon

    def is_valid(self, user, cart_total):
        print(f"Checking validity for coupon {self.code}")
        today = timezone.now()  # Current date and time with timezone awareness
    
        # Ensure valid_from and valid_to are aware datetime objects
        if self.valid_from.tzinfo is None:
            valid_from_date = timezone.make_aware(self.valid_from)
        else:
            valid_from_date = self.valid_from
    
        if self.valid_to.tzinfo is None:
            valid_to_date = timezone.make_aware(self.valid_to)
        else:
            valid_to_date = self.valid_to
    
        # Date validity checks
        if valid_from_date > today:
            print("Coupon not valid yet.")
            return False
        if valid_to_date < today:
            print("Coupon has expired.")
            return False

        # Check user usage and other criteria
        if self.used_by.filter(id=user.id).exists():
            print("Coupon has already been used by this user.")
            return False
        if self.max_uses > 0 and self.uses_count >= self.max_uses:
            print("Coupon usage limit has been reached.")
            return False
        if self.minimum_purchase_amount and cart_total < self.minimum_purchase_amount:
            print("Cart total is less than minimum purchase amount.")
            return False

        print("Coupon is valid.")
        return True

    def mark_as_used(self, user, cart_total):
        """Mark the coupon as used by a user after validating with cart_total."""
        if self.is_valid(user, cart_total):  # Ensure `cart_total` is passed here
            self.used_by.add(user)  # Add user to the used_by field
            self.uses_count += 1  # Increment the usage count
            self.save()  # Save changes to the database


    def __str__(self):
        return f"{self.code} - {self.get_discount_display()}"

    def get_discount_display(self):
        """Returns a string representation of the discount."""
        if self.fixed_amount is not None:
            return f"{self.fixed_amount} TK off"
        elif self.discount_percentage is not None:
            return f"{self.discount_percentage}% off"
        return "No discount"

# Cart Model
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    session_id = models.CharField(max_length=50, null=True, blank=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cart for {self.user.user_name}' if self.user else 'Guest Cart'

    def total_price(self):
        """Calculate the total price of the cart items."""
        return float(sum(float(item.total_price()) for item in self.items.all()))

class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')  # related_name='items'
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)  # Allow null for non-variant products
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Ensure this line is present
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}' if self.product else 'Unknown Product'

    def total_price(self):
        """Calculate the total price for this cart item."""
        return self.quantity * self.get_price()

    def get_price(self):
        """Return the price of the product or product variant."""
        if self.product_variant:
            return self.product_variant.product.current_price  # Price from the variant
        return self.product.current_price  # Price from the base product if no variant



# Order Model
PAYMENT_CHOICES = (
    ('cod', 'Cash on Delivery'),
    ('online', 'Online Payment'),
)

ORDER_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.OneToOneField('Cart', on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    # ForeignKey to Address model for shipping address
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    
    # ForeignKey to Address model for billing address
    billing_address = models.ForeignKey(BillingAddress, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    phone_number = models.CharField(max_length=15)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order {self.order_number} by {self.user.user_name}'

# OrderItem Model with Product Variant
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.product_variant.product.name} ({self.product_variant.color}, {self.product_variant.size}) in Order {self.order.order_number}'

    def total_price(self):
        """Calculate the total price for this order item."""
        return self.quantity * self.product_variant.product.current_price
