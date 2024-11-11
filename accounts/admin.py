from django.contrib import admin  # type: ignore
from .models import BillingAddress, ShippingAddress, User, City, Area, Division, UserProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'email', 'phone_number', 'is_active', 'is_staff', 'is_verified', 'is_superuser')
    search_fields = ('email', 'user_name', 'phone_number')
    list_filter = ('is_active', 'is_staff', 'is_verified')
    ordering = ('user_name',)

    fieldsets = (
        (None, {
            'fields': ('user_name', 'email', 'phone_number', 'password')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_name', 'email', 'phone_number', 'password1', 'password2')  # Use password1 and password2 for new users
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # New user
            obj.set_password(form.cleaned_data['password1'])  # Hash the password
        super().save_model(request, obj, form, change)

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('division_name',)
    search_fields = ('division_name',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('city_name',)
    search_fields = ('city_name',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('area_name',)
    search_fields = ('area_name',)

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line', 'city', 'division', 'area', 'postal_code')
    search_fields = ('user__user_name', 'address_line')  # Allow searching by user name and address line

@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line', 'city', 'division', 'area', 'postal_code')
    search_fields = ('user__user_name', 'address_line')  # Allow searching by user name and address line
@admin.register(UserProfile)  # Register UserProfile model
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'shipping_address', 'billing_address', 'preferences', 'order_history')
    search_fields = ('user__user_name',)  # Allow searching by user name

    # You can customize the fieldsets for UserProfile if needed
    fieldsets = (
        (None, {
            'fields': ('user', 'shipping_address', 'billing_address', 'preferences', 'order_history')
        }),
    )