import re
from django import forms # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from django.core.exceptions import ValidationError

User = get_user_model()

class SignUpForm(forms.ModelForm):
    user_name = forms.CharField(
        label="Full Name",
        required=True,
        error_messages={
            'required': "Full Name is required."
        }
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        error_messages={
            'required': "Email is required.",
        }
    )
    password = forms.CharField(widget=forms.PasswordInput,label="Password",required=True,
        error_messages={
            'required': "Password is required."
        }
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password",required=True,
        error_messages={
            'required': "Confirm Password is required."
        }
    )
    terms = forms.BooleanField(
        label="I agree to the Terms of Use and Privacy Policy",
        required=True,
        error_messages={
            'required': "You must agree to the terms and conditions."
        }
    )

    class Meta:
        model = User
        fields = ['user_name', 'email', 'phone_number', 'password', 'confirm_password', 'terms']

    def clean_user_name(self):
        user_name = self.cleaned_data.get('user_name')

        # Check if username is not empty
        if not user_name:
            raise ValidationError("Username is required.")
        
        # Check if username is at least 3 characters long
        if len(user_name) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        
        # Check if username contains only letters and spaces
        if not all(char.isalpha() or char.isspace() for char in user_name):
            raise ValidationError("Username can only contain letters and spaces.")

        # Check if username has more than one word (i.e., full name)
        if len(user_name.split()) < 2:
            raise ValidationError("Username must be a full name (at least two words).")

        # Check if username is already taken
        if User.objects.filter(user_name=user_name).exists():
            raise ValidationError("Username already exists.")
        
        return user_name

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check if email is not empty
        if not email:
            raise ValidationError("Email is required.")
        
        # Check if email is valid
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            raise ValidationError("Enter a valid email address.")
        
        # Check if email is already taken
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        # Check if phone number is not empty
        if not phone_number:
            raise ValidationError("Phone number is required.")
        
        # Check if phone number is all digits
        if not phone_number.isdigit():
            raise ValidationError("Phone number must be an integer.")
        
        # Check if phone number is a valid Bangladeshi mobile number
        if not re.match(r'^01[3-9]\d{8}$', phone_number):
            raise ValidationError("Phone number must be a valid Bangladeshi mobile number.")
        
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Check if the password is at least 8 characters long
        if password and len(password) < 8:
            self.add_error('password', "Password must be at least 8 characters long.")
    
        # Check if the password contains at least one digit
        if password and not any(char.isdigit() for char in password):
            self.add_error('password', "Password must contain at least one digit.")
    
        # Check if the password contains at least one uppercase letter
        if password and not any(char.isupper() for char in password):
            self.add_error('password', "Password must contain at least one uppercase letter.")
    
        # Check if the password contains at least one lowercase letter
        if password and not any(char.islower() for char in password):
            self.add_error('password', "Password must contain at least one lowercase letter.")
    
        # Check if the password contains at least one special character (@, #, $, %, &, *)
        if password and not re.search(r'[!@#$%^&*]', password):
            self.add_error('password', "Password must contain at least one special character (@, #, $, %, &, *).")
    
        # Check if the password and confirm password match
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data

class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        label="OTP Code",
        max_length=6,
        required=True,
        error_messages={
            'required': "OTP Code is required.",
        }
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        user = self.initial.get('user')  # Get user from initial data

        if not user:
            raise ValidationError("User not found.")

        if not user.is_otp_valid(otp_code):
            raise ValidationError("Invalid or expired OTP code.")
        
        return otp_code

