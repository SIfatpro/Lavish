from django.contrib.auth.backends import ModelBackend # type: ignore
from django.contrib.auth import get_user_model # type: ignore

User = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        
        user = None
        if username:
            try:
                if '@' in username:  # Email login
                    user = User.objects.get(email=username)
                else:  # Phone number login
                    user = User.objects.get(phone_number=username)
                
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
