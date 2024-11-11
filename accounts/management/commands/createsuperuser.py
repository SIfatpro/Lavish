from django.core.management.base import BaseCommand # type: ignore
from django.contrib.auth import get_user_model # type: ignore

class Command(BaseCommand):
    help = 'Create a superuser with email, phone number, username, and password'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        email = input('Email: ')
        phone_number = input('Phone number: ')
        user_name = input('Username: ')
        password = input('Password: ')

        try:
            user = User.objects.create_superuser(
                email=email,
                phone_number=phone_number,
                user_name=user_name,
                password=password
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
