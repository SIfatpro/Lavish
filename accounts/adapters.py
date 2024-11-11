import random
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter # type: ignore

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """Populates the user object with data from the social login."""
        user = sociallogin.user
        
        # Set email
        user.email = data.get('email', '')

        # Extract user's full name or generate a username based on email
        name = data.get('name', '')
        if name:
            user.user_name = name
        else:
            email = user.email
            if email:
                user.user_name = email.split('@')[0]  # Use part before '@' as the username
            else:
                # If no email, create a random username
                user.user_name = self.generate_random_username()

        return user

    def generate_random_username(self):
        """Generates a random username if needed."""
        return f'user_{random.randint(1000, 9999)}'
