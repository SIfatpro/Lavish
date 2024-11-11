import json
import logging
import uuid
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
from cart import models
from cart.utils import CartHandler
from products.models import Product, ProductVariant
from accounts.models import Division, City, Area, ShippingAddress, BillingAddress
from django.utils.formats import number_format
from sslcommerz_lib import SSLCOMMERZ 
from .models import Cart, CartItem, Order, OrderItem

# Configure logging
logger = logging.getLogger(__name__)



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

            # Check if the coupon is valid, but do not mark as used yet
            total_price = cart.total_price()  # Calculate the cart's total price
            is_coupon_valid = coupon.is_valid(request.user, total_price)

            if is_coupon_valid:
                discount_amount = 0

                if coupon.fixed_amount:
                    discount_amount = float(coupon.fixed_amount)
                elif coupon.discount_percentage:
                    discount_amount = total_price * (float(coupon.discount_percentage) / 100)

                # Ensure discount doesn't exceed the total price
                discount_amount = min(discount_amount, total_price)

                subtotal_after_discount = round(total_price - discount_amount, 0)  # Convert to integer for JSON response
                total_after_discount = round(subtotal_after_discount + shipping_cost, 0)  # Recalculate grand total

                # Apply the coupon to the cart but do not mark it as used yet
                cart.coupon = coupon
                cart.save()

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


# 1. Add to Cart
@login_required(login_url='accounts:login')
def add_to_cart(request, product_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            quantity = data.get("quantity", 1)
            product = get_object_or_404(Product, id=product_id)

            # Create or get the user's cart
            cart, _ = Cart.objects.get_or_create(user=request.user)

            # Create a dictionary for filtering product variants
            variant_filters = {}
            variant_labels = {}  # Dictionary to store labels for each variant
            variant_types = ['color', 'size', 'brand', 'capacity']
            for variant_type in variant_types:
                selected_variant = data.get(f"{variant_type}_id")
                if selected_variant:
                    variant_filters[f"{variant_type}_id"] = selected_variant
                    variant_labels[variant_type] = selected_variant  # Add to variant labels dictionary
                    print(f"Selected {variant_type}: {selected_variant}")

            # Try to get the product variant based on selected filters
            product_variant = None
            if variant_filters:
                product_variant = ProductVariant.objects.filter(product_id=product_id, **variant_filters).first()

            # If product_variant is selected, check for its existence in cart
            if product_variant:
                cart_item = CartItem.objects.filter(cart=cart, product_variant=product_variant).first()
                if cart_item:
                    cart_item.quantity += quantity
                else:
                    cart_item = CartItem.objects.create(
                        cart=cart,
                        product_variant=product_variant,
                        product=product,
                        quantity=quantity
                    )
            else:
                cart_item = CartItem.objects.filter(cart=cart, product=product, product_variant=None).first()
                if cart_item:
                    cart_item.quantity += quantity
                else:
                    cart_item = CartItem.objects.create(
                        cart=cart,
                        product=product,
                        product_variant=None,
                        quantity=quantity
                    )

            cart_item.save()

            # Get the total cart item quantity
            cart_total = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantity'))['total'] or 0

            # Response includes variant labels for front-end use
            return JsonResponse({
                'cart_item_count': cart_total,
                'variant_labels': variant_labels
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
    

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

    variant_types = ['color', 'size', 'brand', 'capacity'] 

    # Add variant labels to each cart item
    for item in cart_items:
        variant_labels = {}
        if item.product_variant:
            for variant_type in variant_types:
                selected_variant = getattr(item.product_variant, variant_type, None)
                if selected_variant:
                    variant_labels[variant_type] = str(selected_variant.name)
        item.variant_labels = variant_labels  # Add variant_labels directly to the cart item

    context = {
        'cart_items': cart_items,  # Cart items with variant labels
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

# 7. Checkoutfrom django.
@login_required(login_url='accounts:login')
def checkout(request):
    # Fetch the user's cart and its items
    cart = get_object_or_404(Cart, user=request.user, is_paid=False)
    cart_items = cart.items.all()

    # Calculate cart totals
    subtotal = sum(item.total_price() for item in cart_items)
    shipping_charge = 40  # Fixed shipping cost
    grand_total = subtotal + shipping_charge  # Total cost

    if request.method == 'POST':
        # Fetch address and payment details
        phone_number = request.POST.get('phone_number')
        address_line = request.POST.get('address_line')
        division_id = request.POST.get('division')
        city_id = request.POST.get('city')
        area_id = request.POST.get('area')
        payment_method = request.POST.get('payment_method', 'cod')

        # Check for missing required fields
        if not address_line or not phone_number or not division_id or not city_id or not area_id:
            messages.error(request, "Please fill in all required fields.")
            return redirect('cart:checkout')

        # Validate payment method
        if payment_method not in dict(Order.PAYMENT_CHOICES):
            messages.error(request, "Invalid payment method.")
            return redirect('cart:checkout')

        # Fetch the division, city, and area objects
        try:
            division = Division.objects.get(id=division_id)
            city = City.objects.get(id=city_id)
            area = Area.objects.get(id=area_id)
        except Division.DoesNotExist:
            messages.error(request, "Invalid division.")
            return redirect('cart:checkout')
        except City.DoesNotExist:
            messages.error(request, "Invalid city.")
            return redirect('cart:checkout')
        except Area.DoesNotExist:
            messages.error(request, "Invalid area.")
            return redirect('cart:checkout')

        # Save the Shipping Address
        shipping_address, created = ShippingAddress.objects.update_or_create(
            user=request.user,
            defaults={
                'address_line': address_line,
                'division': division,
                'city': city,
                'area': area,
                'phone_number': phone_number,
            }
        )

        # Optionally handle Billing Address
        billing_address_option = request.POST.get("billing_address_option")
        if billing_address_option == "same":
            # Create a BillingAddress from the ShippingAddress
            billing_address = BillingAddress.objects.create(
                user=request.user,
                address_line=shipping_address.address_line,
                division=shipping_address.division,
                city=shipping_address.city,
                area=shipping_address.area,
                phone_number=shipping_address.phone_number,
            )
        else:
            billing_address_line = request.POST.get("billing_address")
            billing_phone_number = request.POST.get("billing_phone_number")
            billing_division_id = request.POST.get("billing_division")
            billing_city_id = request.POST.get("billing_city")
            billing_area_id = request.POST.get("billing_area")


            # Check for missing billing address fields
            if not billing_address_line or not billing_phone_number or not billing_division_id or not billing_city_id or not billing_area_id:
                messages.error(request, "Please fill in all billing address fields.")
                return redirect('cart:checkout')

            billing_division = Division.objects.get(id=billing_division_id)
            billing_city = City.objects.get(id=billing_city_id)
            billing_area = Area.objects.get(id=billing_area_id)

            billing_address, created = BillingAddress.objects.update_or_create(
                user=request.user,
                defaults={
                    'address_line': billing_address_line,
                    'division': billing_division,
                    'city': billing_city,
                    'area': billing_area,
                    'phone_number': billing_phone_number,
                }
            )

        # Create the order
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            order_number=f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}",
            payment_method=payment_method,
            total_price=grand_total,
            shipping_address=shipping_address,
            billing_address=billing_address,
            phone_number=phone_number,
        )

        # Create OrderItems
        for cart_item in cart_items:
            OrderItem.objects.create(
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

    # Get divisions for the address form
    divisions = Division.objects.all()

    # Context for the template
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': subtotal,  # Pass the subtotal
        'delivery_charge': shipping_charge,  # Shipping charge
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

def payment_gateway(request):
    user = request.user
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

    settings = { 'store_id': 'lavis67261be965432', 'store_pass': 'lavis67261be965432@ssl', 'issandbox': True } 

    sslcz = SSLCOMMERZ(settings)
    
    tran_id = str(uuid.uuid4())  # Generate a unique transaction ID

    post_body = {}
    post_body['total_amount'] = grand_total
    post_body['currency'] = "BDT"
    post_body['tran_id'] = tran_id
    post_body['success_url'] = "your success url"
    post_body['fail_url'] = "your fail url"
    post_body['cancel_url'] = "your cancel url"
    post_body['emi_option'] = 0
    post_body['cus_name'] = user.user_name
    post_body['cus_email'] = user.email
    post_body['cus_phone'] = "01700000000"
    post_body['cus_add1'] = "customer address"
    post_body['cus_city'] = "Dhaka"
    post_body['cus_country'] = "Bangladesh"
    post_body['shipping_method'] = "NO"
    post_body['multi_card_name'] = ""
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Test"
    post_body['product_category'] = "Test Category"
    post_body['product_profile'] = "general"

    
    # Send the request to SSLCOMMERZ
    response = sslcz.createSession(post_body) # API response

    return redirect(response['GatewayPageURL'])

def payment_success(request):
    # Handle success (e.g., save order, show confirmation)
    return HttpResponse('Payment successful')

def payment_fail(request):
    # Handle failure (e.g., show an error message)
    return HttpResponse('Payment failed')

def payment_cancel(request):
    # Handle cancellation (e.g., show a message)
    return HttpResponse('Payment cancelled')

@login_required(login_url='accounts:login')
def complete_order(request):
    """Complete the order and mark the coupon as used."""
    cart = models.Cart.objects.get(user=request.user, is_paid=False)

    # Check if cart has a coupon applied and validate the coupon
    if cart.coupon:
        coupon = cart.coupon

        # Ensure the coupon is valid before marking it as used
        if coupon.is_valid(request.user, cart.total_price()):
            # Mark the coupon as used after the order is completed
            coupon.mark_as_used(request.user)
            cart.is_paid = True  # Mark cart as paid
            cart.save()

            return JsonResponse({'success': True, 'message': "Order completed successfully!"})

        else:
            return JsonResponse({'success': False, 'error': "Coupon is invalid."})
    
    # Complete the order if no coupon was applied
    cart.is_paid = True
    cart.save()

    return JsonResponse({'success': True, 'message': "Order completed without coupon."})
