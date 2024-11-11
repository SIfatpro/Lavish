from django.utils import timezone  # type: ignore
from datetime import timedelta

def is_valid_otp(user, provided_otp):
    try:
        # Get the OTP and its creation time from the user model
        otp_instance = user.otp_code  # Ensure the 'otp_code' field exists in your User model
        otp_created_at = user.otp_created_at  # Ensure 'otp_created_at' exists

        # Check if the provided OTP matches the stored OTP
        if otp_instance == provided_otp:
            # Check the expiration time (valid for 5 minutes)
            expiration_time = otp_created_at + timedelta(minutes=5)
            if timezone.now() <= expiration_time:
                user.is_verified = True  # Set is_verified to True
                user.save()  # Save the user instance to persist changes
                return True  # OTP is valid

    except AttributeError as e:
        print(f"Error verifying OTP - attribute missing: {e}")  # Specific error for attribute issues
    except Exception as e:
        print(f"Error verifying OTP: {e}")  # General error handling for debugging

    return False  # OTP is invalid
