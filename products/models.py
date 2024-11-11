from django.db import models  # type: ignore
from autoslug import AutoSlugField  # type: ignore
from ecommerce.models import SubCategory
from accounts.models import User
from django.core.exceptions import ValidationError  # type: ignore
from django.utils import timezone  # type: ignore
from colorful.fields import RGBColorField  # type: ignore

class Color(models.Model):
    name = models.CharField(max_length=50)
    code = RGBColorField(help_text='HTML color code (e.g. #000000)')  # Color picker

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Enter size")

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
class StorageCapacity(models.Model):
    capacity = models.FloatField(unique=True, help_text="Enter storage capacity in GB (e.g., 128, 256)")

    def __str__(self):
        return f"{self.capacity}"

class Product(models.Model):
    name = models.CharField(max_length=255)
    brand = models.ForeignKey('Brand', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    feature = models.TextField(blank=True, help_text="Key features of the product")
    sub_category = models.ForeignKey(SubCategory, related_name='products', on_delete=models.CASCADE)  # renamed for clarity
    
    PRODUCT_TYPE_CHOICES = [
        ('1', 'New Product'),
        ('2', 'Flash Sale'),
        ('3', 'Just For You'),
    ]
    product_type = models.CharField(max_length=1, choices=PRODUCT_TYPE_CHOICES)
    
    slug = AutoSlugField(populate_from='name', unique=True)
    sku = models.CharField(max_length=100, unique=True)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Full product description")
    
    price = models.DecimalField(max_digits=10, decimal_places=0)
    disk_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_sale = models.IntegerField(default=0)
    stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField()

    is_flash_sale = models.BooleanField(default=False)
    flash_sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    flash_sale_start = models.DateTimeField(blank=True, null=True)
    flash_sale_end = models.DateTimeField(blank=True, null=True)
    
    colors = models.ManyToManyField('Color', through='ProductVariant')
    sizes = models.ManyToManyField('Size', through='ProductVariant')
    
    is_active = models.BooleanField(default=True)
    status = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-created',)

    def __str__(self):
        return self.name

    def clean(self):
        if self.disk_price and self.disk_price > self.price:
            raise ValidationError('Discount price cannot be greater than the original price.')
        if self.is_flash_sale:
            if not self.flash_sale_start or not self.flash_sale_end:
                raise ValidationError('Flash sale must have a start and end time.')
            if self.flash_sale_price and self.flash_sale_price > self.price:
                raise ValidationError('Flash sale price cannot be greater than the original price.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_flash_sale_active(self):
        if self.is_flash_sale and self.flash_sale_start and self.flash_sale_end:
            now = timezone.now()
            return self.flash_sale_start <= now <= self.flash_sale_end
        return False

    @property
    def current_price(self):
        if self.is_flash_sale_active and self.flash_sale_price:
            return self.flash_sale_price
        elif self.disk_price:
            return self.disk_price
        return self.price

    @property
    def discount_percentage(self):
        if self.price > 0 and self.disk_price is not None:
            discount_percentage = ((self.price - self.disk_price) / self.price) * 100
            return round(discount_percentage, 0)
        return 0

    @property
    def variants(self):
        return self.productvariant_set.all()

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()  # Fetch the primary image

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    name = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    variants = models.ManyToManyField('ProductVariant', related_name='images', blank=True)  # New field

    class Meta:
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"{self.product.name} - {'Primary' if self.is_primary else 'Secondary'} Image"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set all other images for the same product to non-primary
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)
    capacity = models.ForeignKey(StorageCapacity, on_delete=models.CASCADE, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ('product', 'color', 'size', 'brand', 'capacity')

    def __str__(self):
        details = [self.product.name]
        if self.color:
            details.append(self.color.name)
        if self.size:
            details.append(self.size.name)
        if self.brand:
            details.append(self.brand.name)
        if self.capacity:
            details.append(f"{self.capacity.capacity}")
        return " - ".join(details)
    @property
    def related_images(self):
        # Return images related to this variant's color and size
        return self.product.images.filter(variants=self).distinct()

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review {self.id} - {self.product.name} by {self.user.user_name}'


class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.FloatField(default=0)

    class Meta:
        unique_together = ('product', 'user')  # Ensure one rating per user per product

    def __str__(self):
        return f'Rating {self.rating} for {self.product.name} by {self.user.user_name}'

    @classmethod
    def get_average_rating(cls, product_id):
        ratings = cls.objects.filter(product_id=product_id)
        total_ratings = sum(rating.rating for rating in ratings)
        num_ratings = ratings.count()
        if num_ratings > 0:
            average = total_ratings / num_ratings
            return round(average, 1)  # Return only the average
        return 0  # Return zero if no ratings

    @classmethod
    def get_total_ratings(cls, product_id):
        return cls.objects.filter(product_id=product_id).count()


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f'Wishlist - {self.user.user_name} - {self.product.name}'
