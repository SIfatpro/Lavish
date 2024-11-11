from datetime import timedelta
import random
from django.utils import timezone  # type: ignore
from django.db import models  # type: ignore
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin  # type: ignore
from django.conf import settings  # type: ignore
from django.db.models.signals import post_save  # type: ignore
from django.dispatch import receiver  # type: ignore

from accounts.managers import UserManager



class User(AbstractBaseUser, PermissionsMixin):
    user_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # OTP fields
    otp_code = models.CharField(max_length=6, null=True, blank=True)  # OTP code for verification
    otp_created_at = models.DateTimeField(null=True, blank=True)  # Timestamp for OTP creation

    # Verification field
    is_verified = models.BooleanField(default=False)

    objects = UserManager()  # Use custom manager

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    def __str__(self):
        return self.user_name  # or self.email, depending on your preference
    
    def generate_otp(self):
        """Generates a random 6-digit OTP and stores it with the current timestamp."""
        self.otp_code = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
        self.otp_created_at = timezone.now()  # Set the creation time
        self.save()  # Save to database

    def verify_otp(self, otp_input):
        """Check if the provided OTP is valid and within the 5-minute window."""
        if self.otp_created_at is None:
            return False  # No OTP was generated

        if self.otp_code != otp_input:
            return False  # OTP doesn't match

        # Check if OTP was created within the last 5 minutes
        expiration_time = self.otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiration_time:
            return False  # OTP has expired

        self.is_verified = True  # Mark as verified
        self.clear_otp()  # Clear the OTP
        self.save()  # Save changes
        return True  # OTP is valid

    def clear_otp(self):
        """Clears the OTP after successful verification."""
        self.otp_code = None
        self.otp_created_at = None
        self.save()


class Division(models.Model):
    division_name = models.CharField(max_length=100)

    def __str__(self):
        return self.division_name


class City(models.Model):
    division = models.ForeignKey(Division, on_delete=models.CASCADE)  # Singular 'province'
    city_name = models.CharField(max_length=100)

    def __str__(self):
        return self.city_name


class Area(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)  # References City
    area_name = models.CharField(max_length=100)

    def __str__(self):
        return self.area_name


class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address_line = models.CharField(max_length=255)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)  # Add phone number field

    def __str__(self):
        return f"{self.address_line}, {self.city}, {self.division}"

class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address_line = models.CharField(max_length=255)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)  # Add phone number field

    def __str__(self):
        return f"{self.address_line}, {self.city}, {self.division}"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    billing_address = models.ForeignKey(BillingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    preferences = models.JSONField(null=True, blank=True)
    order_history = models.TextField(null=True, blank=True)

    # Relationships to new models
    product_ratings = models.ManyToManyField('products.Product', blank=True, related_name='rated_by')  # Assuming product ratings are linked to Product
    coupon_codes = models.ManyToManyField('cart.Coupon', related_name='user_profiles', blank=True)  # Corrected reference & Use string reference
    wishlist_products = models.ManyToManyField('products.Wishlist', blank=True, related_name='wished_by')  # Use string reference

    def __str__(self):
        return f"{self.user.user_name}'s Profile"


# Signal handlers for creating and saving UserProfile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
