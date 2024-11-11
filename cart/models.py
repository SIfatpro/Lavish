from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from products.models import Product, ProductVariant
from accounts.models import ShippingAddress, BillingAddress  # Import your address models
from ecommerce.models import Category, SubCategory
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

# Coupon Model
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
            return False
        if valid_to_date < today:
            return False

        # Check user usage and other criteria
        if self.used_by.filter(id=user.id).exists():
            return False
        if self.max_uses > 0 and self.uses_count >= self.max_uses:
            return False
        if self.minimum_purchase_amount and cart_total < self.minimum_purchase_amount:
            return False

        return True

    def mark_as_used(self, user):
        """Marks the coupon as used by the user after confirming the order."""
        if user in self.used_by.all():
            raise ValueError("Coupon has already been used by this user.")
        
        self.used_by.add(user)  # Add the user to the used_by field
        self.uses_count += 1     # Increment the usage count
        self.save()


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
class Order(models.Model):
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE)
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

class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')], default='unpaid')
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number} for Order #{self.order.order_number}"

    def generate_pdf(self):
        # Create the PDF invoice
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add title
        p.setFont("Helvetica", 16)
        p.drawString(200, height - 40, f"Invoice #{self.invoice_number}")
        
        # Add order details
        p.setFont("Helvetica", 12)
        p.drawString(30, height - 80, f"Order Number: {self.order.order_number}")
        p.drawString(30, height - 100, f"Customer: {self.order.user.get_full_name()}")
        p.drawString(30, height - 120, f"Shipping Address: {self.order.shipping_address}")
        p.drawString(30, height - 140, f"Payment Method: {self.order.payment_method}")
        
        # Add the items in the order
        y_position = height - 160
        p.drawString(30, y_position, "Products:")
        y_position -= 20
        
        for item in self.order.items.all():
            p.drawString(30, y_position, f"{item.quantity} x {item.product_variant.product.name} ({item.product_variant.color}, {item.product_variant.size})")
            y_position -= 20

        # Add total price and payment status
        p.drawString(30, y_position, f"Total Price: ৳ {self.total_price}")
        p.drawString(30, y_position - 20, f"Payment Status: {self.payment_status.capitalize()}")

        # Save the PDF
        p.showPage()
        p.save()

        # Save the PDF to the FileField
        buffer.seek(0)
        file_name = f"invoice_{self.invoice_number}.pdf"
        self.pdf_file.save(file_name, File(buffer), save=True)
        buffer.close()

    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not set already
        if not self.invoice_number:
            self.invoice_number = f"INV{self.order.order_number}-{self.issued_at.strftime('%Y%m%d%H%M%S')}"
        
        # Set total price (in case it was not set already)
        if not self.total_price:
            self.total_price = self.order.total_price
        
        super().save(*args, **kwargs)

# Signal to automatically create an invoice when the order status is 'paid'
@receiver(post_save, sender=Order)
def create_invoice(sender, instance, created, **kwargs):
    if created and instance.status == 'paid':
        # Create an invoice for the order
        invoice = Invoice.objects.create(order=instance)
        invoice.generate_pdf()  # Generate the PDF after the invoice is created
        invoice.save()  # Save the generated invoice