from django.utils import timezone # type: ignore
import re
import logging
from django.utils.crypto import get_random_string # type: ignore
from accounts.forms import SignUpForm
from .models import User
from django.urls import reverse # type: ignore
from django.core.cache import cache # type: ignore
from django.contrib.auth import logout # type: ignore
from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth import authenticate, login as auth_login # type: ignore
from django.http import JsonResponse # type: ignore
from django.core.mail import send_mail # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode # type: ignore
from django.utils.encoding import force_bytes # type: ignore
from django.template.loader import render_to_string # type: ignore
from django.conf import settings # type: ignore
from django.contrib.auth.tokens import default_token_generator # type: ignore
from django.contrib.sites.shortcuts import get_current_site # type: ignore
from django.core.exceptions import ValidationError # type: ignore
from accounts.is_valid_otp import is_valid_otp  # Import the is_valid_otp function from is_valid_otp.py
from cart.models import OrderItem
from accounts.models import BillingAddress, ShippingAddress 




User = get_user_model()

# Set up logging
logger = logging.getLogger(__name__)



User = get_user_model()

# Set up logging
logger = logging.getLogger(__name__)


def is_valid_phone_number(phone_number):
    """Validate Bangladeshi mobile number format."""
    pattern = re.compile(r'^01[3-9]\d{8}$')  # Matches format: 01XXXXXXXXX
    return pattern.match(phone_number) is not None

def is_valid_password(password):
    """Validate password strength requirements."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            # Create the user instance without saving to the database yet
            user = form.save(commit=False)
            user.otp_code = get_random_string(length=6)  # Generate OTP
            user.is_active = False  # Deactivate account until OTP verification
            user.otp_created_at = timezone.now()  # Set OTP creation time
            user.set_password(form.cleaned_data['password'])  # Hash the password
            user.save()  # Save user to the database

            print(f"User ID: {user.id}")  # Print user ID for debugging

            # Save user data in the session
            request.session['user_data'] = {
                'user_name': user.user_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'password': user.password,  # Hashed password
                'otp_code': user.otp_code,
                'otp_created_at': str(user.otp_created_at),  # Store as string
            }

            # Send OTP email
            send_otp_email(user)

            # Log success and send JSON response for AJAX requests
            logger.info('Registration successful for user: %s', user.email)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Registration successful. OTP sent to your email.',
                    'user_id': user.id  # Include the user_id in the response
            }, status=200)


            # Redirect to the OTP verification page with user_id as URL param
            messages.success(request, 'OTP sent to your email. Please verify.')
            return redirect('accounts:verify_otp', user_id=user.id)  # Use correct namespace

        else:
            # Log form errors
            logger.error(f"Form validation errors: {form.errors}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})


def send_otp_email(user):
    """Sends OTP email to the user."""
    subject = "Your OTP Code"
    message = (
        f"Dear {user.user_name},\n\n"
        f"Your OTP code is {user.otp_code}.\n"
        "Please enter it within 5 minutes to verify your email address.\n\n"
        "Thank you for joining us!\n"
        "Best regards,\n"
        "Lavish Bangladesh"
    )
    
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
    except Exception as e:
        print(f"Error sending OTP email: {e}")

def verify_otp(request, user_id):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        user = get_object_or_404(User, id=user_id)

        # Validate OTP
        if is_valid_otp(user, otp_code):
            user.is_active = True
            user.is_verified = True  # Set is_verified to True
            user.save()  # Save changes to the user
            messages.success(request, "OTP verification successful. You can now log in.")
            return redirect('accounts:login')  # Redirect to the login page
        else:
            messages.error(request, "Invalid OTP code.")
            return redirect('accounts:verify_otp', user_id=user.id)

    return render(request, 'verify_otp.html', {'user_id': user_id})


def login(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect(reverse('accounts:user_accounts'))  # Redirect if already logged in
    
    next_url = request.GET.get('next', reverse('accounts:user_accounts'))  # Default redirect URL
    if request.method == 'POST':
        user_email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')  # Remember me checkbox

        # Rate limiting to avoid brute force attacks
        attempts = cache.get(user_email, 0)

        if attempts >= 5:
            return JsonResponse({'status': 'error', 'message': "Too many login attempts. Please try again later."}, status=429)

        # Authenticate the user
        user = authenticate(request, username=user_email, password=password)

        if user is not None:
            if user.is_superuser:
                return JsonResponse({'status': 'error', 'message': "Admin users must log in via the admin panel."}, status=403)

            if user.is_active:
                auth_login(request, user)  # Log the user in
                cache.delete(user_email)  # Reset login attempts

                # Set session expiration
                request.session.set_expiry(1209600 if remember else 0)

                return JsonResponse({'status': 'success', 'message': "You have logged in successfully.", 'next_url': next_url}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': "Your account is inactive. Please contact support."}, status=403)
        else:
            # Increment login attempts
            cache.set(user_email, attempts + 1, timeout=300)
            return JsonResponse({'status': 'error', 'message': "Invalid email or password."}, status=401)

    return render(request, 'login.html')



def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('accounts:login')


def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Get the current domain and protocol
            current_site = get_current_site(request)
            domain = current_site.domain
            protocol = 'https' if request.is_secure() else 'http'

            # Render the email subject and body
            email_subject = render_to_string('password_reset_subject.html', {'user': user}).strip()
            email_body = render_to_string('password_reset_email.html', {
                'protocol': protocol,
                'domain': domain,
                'uid': uid,
                'token': token,
                'user': user,
            })

            # Send the password reset email
            send_mail(
                email_subject,
                email_body,
                'Lavish Bangladesh <' + settings.DEFAULT_FROM_EMAIL + '>',  # Custom sender name
                [user.email],
                fail_silently=False,
                html_message=email_body  # Send HTML email
            )
            messages.success(request, 'Password reset email sent!')
            return redirect('accounts:password_reset_done')
        except User.DoesNotExist:
            messages.error(request, 'Email does not exist.')
    
    return render(request, 'forgot_password.html')

def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation."""
    try:
        # Decode the user ID and retrieve the user object
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_object_or_404(User, pk=uid)

        # Validate the token
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                errors = {}

                # Validate passwords
                if not new_password:
                    errors['new_password'] = 'Please enter a new password.'
                if not confirm_password:
                    errors['confirm_password'] = 'Please confirm your new password.'

                if new_password and confirm_password:
                    new_password = new_password.strip()
                    confirm_password = confirm_password.strip()

                    # Check if new password matches the old password
                    if user.check_password(new_password):
                        errors['new_password'] = 'New password cannot be the same as the old password.'
                    else:
                        # Validate the new password against custom rules
                        try:
                            is_valid_password(new_password)  # Custom password validation
                            if new_password != confirm_password:
                                errors['confirm_password'] = 'Passwords do not match.'
                        except ValidationError as e:
                            errors['new_password'] = str(e)  # Capture specific validation errors

                # Return JSON response if there are errors
                if errors:
                    return JsonResponse({'status': 'error', 'errors': errors}, status=400)

                # If no errors, proceed to reset the password
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been reset successfully.')
                return JsonResponse({'status': 'success', 'message': 'Password reset successfully.'})

            # Return the password reset form with uidb64 and token
            return render(request, 'password_reset_confirm.html', {
                'valid_link': True,
                'uidb64': uidb64,
                'token': token
            })

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Invalid password reset link.'}, status=400)

    # If the link is not valid, return to the same template
    return render(request, 'password_reset_confirm.html', {
        'valid_link': False,
        'uidb64': uidb64,
        'token': token
    })


def password_reset_done(request):
    """Display a message indicating that the password reset email has been sent."""
    return render(request, 'password_reset_done.html')


def password_reset_complete(request):
    """ Display password reset complete message. """
    return render(request, 'password_reset_complete.html')

@login_required(login_url='login')  # Protect this view by requiring login
def user_accounts(request):
    """ Render the user accounts page. """
    current_user = request.user

    # Fetch recent orders for the logged-in user through the Order model
    recent_orders = OrderItem.objects.filter(order__user=current_user).order_by('-order__ordered_at')

    # Fetch the billing address for the logged-in user, getting the first record if multiple exist
    billing_address = BillingAddress.objects.filter(user=current_user).first()

    # Fetch the shipping address for the logged-in user, getting the first record if multiple exist
    shipping_address = ShippingAddress.objects.filter(user=current_user).first()

    context = {
        'user': current_user,
        'recent_orders': recent_orders,
        'billing_address': billing_address,
        'shipping_address': shipping_address,
    }

    return render(request, 'user_accounts.html', context)

@login_required
def updateuser_accounts(request):
    if request.method == 'POST':
        user = request.user
        
        # Update user fields with new values from the form
        user.user_name = request.POST.get('user_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')  # Add this line
        user.save()

        # Add a success message
        messages.success(request, "Profile updated successfully")

        # Redirect to the user accounts page
        return redirect('accounts:user_accounts')

    return render(request, 'user_accounts.html')  # Return the user accounts page for GET requests

@login_required(login_url='login')  # Protect this view
def user_order(request):
    """ Render user order page. """
    return render(request, 'user_order.html')

@login_required(login_url='login')  # Protect this view
def user_wishlist(request):
    """ Render user wishlist page. """
    return render(request, 'user_wishlist.html')

@login_required(login_url='login')  # Protect this view
def user_review(request):
    """ Render user review page. """
    return render(request, 'user_review.html')

@login_required(login_url='login')  # Protect this view
def user_ratings(request):
    """ Render user ratings page. """
    return render(request, 'user_ratings.html')

@login_required(login_url='login')  # Protect this view
def user_coupon(request):
    """ Render user coupon page. """
    return render(request, 'user_coupon.html')
