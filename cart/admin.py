from django.contrib import admin
from .models import Coupon, Cart, CartItem, Order, OrderItem, Invoice
from django.utils.html import format_html

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'get_discount_display', 'valid_from', 'valid_to', 'is_active', 'max_uses', 'uses_count')
    search_fields = ('code',)
    list_filter = ('is_active', 'valid_from', 'valid_to')

    def get_discount_display(self, obj):
        return obj.get_discount_display()
    get_discount_display.short_description = 'Discount'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'is_paid', 'created_at', 'total_price')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('user__username', 'session_id')

    def total_price(self, obj):
        return obj.total_price()
    total_price.short_description = 'Total Price'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'product_variant', 'quantity', 'get_price', 'total_price')
    list_filter = ('cart',)
    search_fields = ('product__name', 'product_variant__color', 'product_variant__size')

    def get_price(self, obj):
        return obj.get_price()
    get_price.short_description = 'Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_price', 'ordered_at', 'payment_method', 'shipping_address', 'billing_address')
    list_filter = ('status', 'ordered_at', 'payment_method')
    search_fields = ('order_number', 'user__username', 'phone_number')

    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Total Price'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_variant', 'quantity', 'get_total_price')
    list_filter = ('order',)
    search_fields = ('order__order_number', 'product_variant__product__name')

    def get_total_price(self, obj):
        return obj.total_price()
    get_total_price.short_description = 'Total Price'

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'issued_at', 'total_price', 'payment_status', 'pdf_file', 'generate_pdf_link')
    list_filter = ('payment_status', 'issued_at')
    search_fields = ('invoice_number', 'order__order_number')

    def generate_pdf_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Download PDF</a>', obj.pdf_file.url)
        return "No PDF"
    generate_pdf_link.short_description = 'Invoice PDF'
