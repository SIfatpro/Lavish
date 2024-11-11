import random
from django.contrib.auth.base_user import BaseUserManager # type: ignore

class UserManager(BaseUserManager):
    def create_user(self, email, user_name=None, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        # Generate username from email if not provided
        if not user_name:
            user_name = self.generate_username_from_email(email)
        
        # Delay the import of the User model until it's actually needed
        from accounts.models import User

        user = self.model(
            email=self.normalize_email(email),
            user_name=user_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, user_name=None, password=None, phone_number=None):
        """Creates and returns a superuser with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set.")
        if password is None:
            raise ValueError("The Password field must be set.")
        
        # Generate username from email if not provided
        if not user_name:
            user_name = self.generate_username_from_email(email)
    
        # Delay the import of the User model until it's actually needed
        from accounts.models import User
    
        user = self.model(
            email=self.normalize_email(email),
            user_name=user_name,
            phone_number=phone_number,  # Set phone number
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def generate_username_from_email(self, email):
        """Generates a username from the email if not provided."""
        if email:
            return email.split('@')[0]  # Use part before '@' as username
        return self.generate_random_username()  # Fallback to a random username if email is unavailable

    def generate_random_username(self):
        """Generates a random username if no other method works."""
        return f'user_{random.randint(1000, 9999)}'
