from django.contrib import admin
from .models import Product, ProductImage, ProductVariant, Review, Rating, Wishlist, Color, Size, Brand, StorageCapacity

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(StorageCapacity)
class StorageCapacityAdmin(admin.ModelAdmin):
    list_display = ('capacity',)
    search_fields = ('capacity',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'disk_price', 'is_flash_sale', 'stock', 'created')
    list_filter = ('brand', 'is_flash_sale', 'product_type', 'is_active')
    search_fields = ('name', 'sku')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'name')
    list_filter = ('product', 'is_primary')
    search_fields = ('product__name',)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'brand', 'capacity', 'stock_quantity')
    list_filter = ('product', 'color', 'size', 'brand', 'capacity')
    search_fields = ('product__name',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'created_at')
    list_filter = ('product', 'user')
    search_fields = ('product__name', 'user__user_name')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating')
    list_filter = ('product', 'rating')
    search_fields = ('product__name', 'user__user_name')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')
    list_filter = ('user', 'product')
    search_fields = ('user__user_name', 'product__name')
