import json
import logging
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
from cart import models
from cart.utils import CartHandler
from products.models import Product
from accounts.models import Division, City, Area, ShippingAddress, BillingAddress
from django.utils.formats import number_format



# Configure logging
logger = logging.getLogger(__name__)

# 1. Add to Cart
@login_required(login_url='accounts:login')
def add_to_cart(request, product_id):
    if request.method == "POST":
        try:
            product = get_object_or_404(Product, id=product_id)
            data = json.loads(request.body)
            quantity = data.get("quantity", 1)

            cart, _ = models.Cart.objects.get_or_create(user=request.user)

            # Check if a product variant is specified
            product_variant_id = data.get("product_variant_id")
            if product_variant_id:
                product_variant = get_object_or_404(models.ProductVariant, id=product_variant_id)
                cart_item, created = models.CartItem.objects.get_or_create(cart=cart, product_variant=product_variant)
            else:
                cart_item, created = models.CartItem.objects.get_or_create(cart=cart, product=product)

            # Update the quantity and save
            cart_item.quantity += quantity if not created else quantity  # Update or set quantity
            cart_item.save()

            # Recalculate the total quantity in the cart
            cart_total = models.CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantity'))['total'] or 0

            return JsonResponse({'cart_item_count': cart_total})
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

# Apply Coupon View
@require_POST
@login_required(login_url='accounts:login')
def apply_coupon(request):
    try:
        coupon_code = request.POST.get('coupon_code', '').strip()
        cart = models.Cart.objects.filter(user=request.user, is_paid=False).first()
        shipping_cost = 40  # Fixed shipping cost
        
        if not cart:
            return JsonResponse({'success': False, 'error': 'No active cart found.'}, status=400)

        try:
            coupon = models.Coupon.objects.get(code=coupon_code)

            # Check if the coupon has already been used by the user
            if coupon.used_by.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Coupon has already been used by this user.'}, status=400)

            total_price = cart.total_price()  # Calculate the cart's total price

            # Validate the coupon once and store the result
            is_coupon_valid = coupon.is_valid(request.user, total_price)

            # Validate and mark the coupon as used if applicable
            if is_coupon_valid:
                coupon.mark_as_used(request.user, total_price)  # Pass the cart_total here
                discount_amount = 0

                if coupon.fixed_amount:
                    discount_amount = float(coupon.fixed_amount)
                elif coupon.discount_percentage:
                    discount_amount = total_price * (float(coupon.discount_percentage) / 100)

                # Ensure discount doesn't exceed the total price
                discount_amount = min(discount_amount, total_price)

                subtotal_after_discount = round(total_price - discount_amount, 0)  # Convert to integer for JSON response
                total_after_discount = round(subtotal_after_discount + shipping_cost, 0)  # Recalculate grand total

                return JsonResponse({
                    'success': True,
                    'message': f'Coupon applied successfully! You saved ৳ {number_format(discount_amount, 0)}.',
                    'new_subtotal': subtotal_after_discount,
                    'new_total': total_after_discount,
                    'discount_display': coupon.get_discount_display(),
                })
            else:
                return JsonResponse({'success': False, 'error': 'Coupon is invalid or has already been used.'}, status=400)

        except models.Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon does not exist.'}, status=404)

    except Exception as e:
        logger.error(f"Error applying coupon: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Cart View
@login_required(login_url='accounts:login')
def cart(request):
    cart_handler = CartHandler(request.user, request.session)
    cart_items = cart_handler.get_cart_items()

    # Calculate the subtotal and initial grand total
    subtotal = sum(item.total_price() for item in cart_items)
    shipping_cost = 40
    grand_total = subtotal + shipping_cost

    # Apply discount if there's a coupon
    cart = models.Cart.objects.get(user=request.user)
    discount_amount = 0
    cart_total = subtotal

    if cart.coupon and cart.coupon.is_valid(request.user, subtotal):
        if cart.coupon.fixed_amount:
            discount_amount = cart.coupon.fixed_amount
        elif cart.coupon.discount_percentage:
            discount_amount = subtotal * (cart.coupon.discount_percentage / 100)
        
        # Ensure discount doesn't exceed the total price
        discount_amount = min(discount_amount, subtotal)
        cart_total = subtotal - discount_amount

    grand_total = cart_total + shipping_cost

    context = {
        'cart_items': cart_items,
        'total_items': len(cart_items),
        'total_item_count': cart_handler.get_total_items_count(),
        'cart_total': round(cart_total, 0),
        'grand_total': round(grand_total, 0),
        'discount_amount': round(discount_amount, 0),
    }

    if not cart_items:
        messages.info(request, "Your cart is currently empty.")
        return render(request, 'empty_cart.html', context)

    return render(request, 'cart.html', context)

# 3. Update Cart Item Quantity
@require_POST
@login_required(login_url='accounts:login')
def update_cart(request, item_id):
    cart_handler = CartHandler(request.user, request.session)
    qty = int(request.POST.get('qty', 1))

    try:
        cart_item = cart_handler.get_cart_item(item_id)  # Custom method to get the cart item
        if cart_item:
            cart_item.quantity = qty
            cart_item.save()

            # Calculate new totals
            subtotal = sum(item.total_price() for item in cart_handler.get_cart_items())
            shipping_cost = 40  # Adjust this as necessary
            grand_total = subtotal + shipping_cost

            response_data = {
                'success': True,
                'total_cart_count': cart_handler.get_total_items_count(),
                'subtotal': subtotal,
                'grand_total': grand_total,
            }
            return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# 4. Update Cart Count
@login_required
@require_POST
def update_cart_count(request):
    total_cart_count = (
        models.CartItem.objects.filter(cart__user=request.user, cart__is_paid=False)
        .aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    )

    return JsonResponse({'cart_count': total_cart_count})

# 5. Remove from Cart
@login_required(login_url='accounts:login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(models.CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, "Item removed from cart successfully.")
    return redirect('cart:cart')

# 7. Checkout
@login_required(login_url='accounts:login')
def checkout(request):
    cart = get_object_or_404(models.Cart, user=request.user, is_paid=False)
    cart_items = cart.items.all()

    # Calculate cart totals
    subtotal = sum(item.total_price() for item in cart_items)  # Sum of all item prices
    shipping_charge = 50  # Fixed shipping cost
    packaging_charge = 20  # Fixed packaging charge
    grand_total = subtotal + shipping_charge + packaging_charge  # Total cost

    if request.method == 'POST':
        # Fetch address and payment details
        phone_number = request.POST.get('phone_number')
        address_line = request.POST.get('address_line')
        province_id = request.POST.get('division')
        city_id = request.POST.get('city')
        area_id = request.POST.get('area')
        postal_code = request.POST.get('postal_code')
        payment_method = request.POST.get('payment_method', 'cod')

        # Validate payment method
        if payment_method not in dict(models.Order.PAYMENT_CHOICES):
            messages.error(request, "Invalid payment method.")
            return redirect('checkout:checkout')

        # Fetch the division, city, and area objects
        division = Division.objects.get(id=province_id)
        city = City.objects.get(id=city_id)
        area = Area.objects.get(id=area_id)

        # Save the Shipping Address
        shipping_address = ShippingAddress.objects.update_or_create(
            user=request.user,
            defaults={
                'address_line': address_line,
                'division': division,
                'city': city,
                'area': area,
                'phone_number': phone_number,
                'postal_code': postal_code
            }
        )

        # Optionally handle Billing Address
        billing_address_option = request.POST.get("billing_address_option")
        if billing_address_option == "same":
            billing_address = ShippingAddress.objects.get(user=request.user)
        else:
            billing_address_line = request.POST.get("billing_address")
            billing_phone_number = request.POST.get("billing_phone_number")
            billing_division_id = request.POST.get("billing_division")
            billing_city_id = request.POST.get("billing_city")
            billing_area_id = request.POST.get("billing_area")
            billing_postal_code = request.POST.get("billing_postal_code")
            
            billing_division = Division.objects.get(id=billing_division_id)
            billing_city = City.objects.get(id=billing_city_id)
            billing_area = Area.objects.get(id=billing_area_id)

            billing_address = BillingAddress.objects.update_or_create(
                user=request.user,
                defaults={
                    'address_line': billing_address_line,
                    'division': billing_division,
                    'city': billing_city,
                    'area': billing_area,
                    'phone_number': billing_phone_number,
                    'postal_code': billing_postal_code
                }
            )

        # Create the order
        order = models.Order.objects.create(
            user=request.user,
            cart=cart,
            order_number=f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}",
            payment_method=payment_method,
            total_price=grand_total,
            shipping_address=shipping_address[0],
            billing_address=billing_address[0],  # Use the created/updated billing address
            phone_number=phone_number,
        )

        # Create OrderItems
        for cart_item in cart_items:
            models.OrderItem.objects.create(
                order=order,
                product_variant=cart_item.product_variant or None,
                quantity=cart_item.quantity,
            )

        # Mark the cart as paid
        cart.is_paid = True
        cart.save()

        # Show success message and redirect
        messages.success(request, "Checkout completed successfully!")
        return redirect('success_page')  # Redirect to a success page after checkout

    divisions = Division.objects.all()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': subtotal,  # Pass the subtotal
        'delivery_charge': shipping_charge,  # Shipping charge
        'packaging_charge': packaging_charge,  # Packaging charge
        'grand_total': grand_total,  # Grand total
        'divisions': divisions,
    }
    return render(request, 'checkout.html', context)

@login_required(login_url='accounts:login')
def save_address(request):
    if request.method == "POST":
        # Fetch common fields
        full_name = request.POST.get("full_name")
        phone_number = request.POST.get("phone_number")
        division_id = request.POST.get("division")
        city_id = request.POST.get("city")
        area_id = request.POST.get("area")
        address_line = request.POST.get("address")

        # Shipping Address
        division = Division.objects.get(id=division_id)
        city = City.objects.get(id=city_id)
        area = Area.objects.get(id=area_id)

        ShippingAddress.objects.update_or_create(
            user=request.user,
            defaults={
                "address_line": address_line,
                "division": division,
                "city": city,
                "area": area,
                "phone_number": phone_number,
            }
        )

        # Billing Address - Check if the same as Shipping or Different
        billing_address_option = request.POST.get("billing_address_option")
        
        if billing_address_option == "same":
            BillingAddress.objects.update_or_create(
                user=request.user,
                defaults={
                    "address_line": address_line,
                    "division": division,
                    "city": city,
                    "area": area,
                    "phone_number": phone_number,
                }
            )
        else:
            # If different, fetch and use billing-specific fields
            billing_division_id = request.POST.get("billing_division")
            billing_city_id = request.POST.get("billing_city")
            billing_area_id = request.POST.get("billing_area")
            billing_address_line = request.POST.get("billing_address")
            billing_phone_number = request.POST.get("billing_phone_number")
            billing_division = Division.objects.get(id=billing_division_id)
            billing_city = City.objects.get(id=billing_city_id)
            billing_area = Area.objects.get(id=billing_area_id)
            
            BillingAddress.objects.update_or_create(
                user=request.user,
                defaults={
                    "address_line": billing_address_line,
                    "division": billing_division,
                    "city": billing_city,
                    "area": billing_area,
                    "phone_number": billing_phone_number,
                }
            )
        
        messages.success(request, "Address saved successfully.")
        return redirect(request.path)  # Redirect to the same page

    divisions = Division.objects.all()
    return render(request, "checkout.html", {"divisions": divisions})

def get_cities(request, division_id):
    # Fetch cities based on division
    cities = City.objects.filter(division_id=division_id)
    city_data = [{'id': city.id, 'city_name': city.city_name} for city in cities]
    return JsonResponse({'cities': city_data})

def get_areas(request, city_id):
    # Fetch areas based on city
    areas = Area.objects.filter(city_id=city_id)
    area_data = [{'id': area.id, 'area_name': area.area_name} for area in areas]
    return JsonResponse({'areas': area_data})

def initiate_payment(request):
    return render(request, 'checkout.html')  # Adjust the template as needed