"""
Django settings for Marazzo project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os  # Importing the os module to handle environment variables and file paths
from pathlib import Path  # Importing Path to handle file paths in an OS-independent way
from dotenv import load_dotenv  # type: ignore # To load environment variables from a .env file
from django.contrib.messages import constants as messages  # type: ignore # Importing message constants for custom message tags

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key for the Django application (must be kept secret in production)
SECRET_KEY = 'django-insecure-rot^t=q^y+^w!o0=o#*=id37g)8o$p%0l)=795lait=)@vc!tb'

# Debug mode flag (should be False in production for security reasons)
DEBUG = True

# List of allowed hosts (empty means no restrictions, should be set in production)
ALLOWED_HOSTS = []

# Application definition
SITE_ID = 1  # Defines the ID of the site in the database (useful for multi-site apps)
INSTALLED_APPS = [
    'django.contrib.admin',  # Admin site app
    'django.contrib.auth',  # Authentication system
    'django.contrib.contenttypes',  # Content type framework
    'django.contrib.sessions',  # Session framework
    'django.contrib.messages',  # Messaging framework
    'django.contrib.staticfiles',  # Static files management
    
    'tinymce',  # Rich text editor (TinyMCE)

    # Custom apps
    'ecommerce',  # E-commerce app
    'accounts',  # User account management app
    'cart',  # Shopping cart app
    'footer',  # Footer app
    'customadmin',  # Custom admin app
    'products',  # Product management app
    'colorful',

    'allauth.socialaccount.providers.google',  # Ensure this is correct
    'social_django',  # Django social authentication via social_core
    'allauth',  # Django allauth for authentication and account management
    'allauth.account',  # Allauth account management
    'allauth.socialaccount',  # Allauth social account integration

    'debug_toolbar',  # Django debug toolbar for performance monitoring
]

# Middleware definition
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # Security-related middleware
    'django.contrib.sessions.middleware.SessionMiddleware',  # Middleware for session handling
    'django.middleware.common.CommonMiddleware',  # Common HTTP middleware
    'django.middleware.csrf.CsrfViewMiddleware',  # Protects against Cross-Site Request Forgeries
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Handles authentication for users
    'django.contrib.messages.middleware.MessageMiddleware',  # Handles messages in the app
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Protects against clickjacking

    'allauth.account.middleware.AccountMiddleware',  # Middleware for allauth account
    'social_django.middleware.SocialAuthExceptionMiddleware',  # Handles exceptions in social authentication

    'debug_toolbar.middleware.DebugToolbarMiddleware',  # Middleware for Django debug toolbar
]

# List of internal IPs (used by the debug toolbar)
INTERNAL_IPS = ['http://127.0.0.1:8000']

# Root URL configuration for the project
ROOT_URLCONF = 'Marazzo.urls'

# Custom user model configuration
AUTH_USER_MODEL = 'accounts.User'

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Template engine
        'DIRS': [BASE_DIR, "templates"],  # List of directories to search for templates
        'APP_DIRS': True,  # Enable template loading from app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',  # Debug context processor
                'django.template.context_processors.request',  # Request context processor
                'django.contrib.auth.context_processors.auth',  # Auth context processor
                'django.contrib.messages.context_processors.messages',  # Message context processor
                'cart.context_processors.cart_item_count', # Custom cart context processor
                
            ],
        },
    },
]

# WSGI application path
WSGI_APPLICATION = 'Marazzo.wsgi.application'

# Database configuration
# DATABASES = {
#    'default': {
#    'ENGINE': 'django.db.backends.sqlite3',  # SQLite database engine (commented out)
#    'NAME': BASE_DIR / 'db.sqlite3',  # SQLite database file (commented out)
#    }
# }

# MySQL database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # MySQL database engine
        'NAME': 'lavish',  # Name of the MySQL database
        'USER': 'root',  # MySQL username
        'PASSWORD': '',  # MySQL password (empty in this case)
        'HOST ': "localhost",  # MySQL host (localhost)
        'PORT ': '3306',  # MySQL port (default 3306)
    }
}

# PostgreSQL database configuration
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'lavish',
#        'USER': 'root',
#        'PASSWORD': '',
#        'HOST': '127.0.0.1',
#        'PORT': '5432',
#    }
#}


# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # Prevents passwords that are similar to user attributes
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # Enforces a minimum password length
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # Prevents common, easily guessable passwords
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # Prevents all-numeric passwords
    },
]

# Internationalization settings
LANGUAGE_CODE = 'en-us'  # Default language
TIME_ZONE = 'Asia/Dhaka'  # Set the correct time zone for Bangladesh
USE_TZ = True  # Enable timezone support

USE_I18N = True  # Enable Django’s translation system

# Static file settings
MEDIA_URL = '/media/'  # URL for serving media files
MEDIA_ROOT = '/lavish/static/media/'  # Root directory for media files

# CKEditor (TinyMCE) settings
CKEDITOR_UPLOAD_PATH = 'uploads/'  # Path for CKEditor uploads
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': None,  # No toolbar configuration for the default editor
    },
}

# Static file URL and directories
STATIC_URL = '/static/'  # URL for serving static files
STATICFILES_DIRS = [BASE_DIR / 'static']  # Directories where static files are stored
STATIC_ROOT = 'staticfiles'  # Root directory for collecting static files

# Message tags customization
MESSAGE_TAGS = {
    messages.INFO: 'alert alert-info',  # Custom class for info messages
    messages.SUCCESS: 'alert alert-success',  # Custom class for success messages
    messages.WARNING: 'alert alert-warning',  # Custom class for warning messages
    messages.ERROR: 'alert alert-danger',  # Custom class for error messages
    messages.DEBUG: 'alert alert-info',  # Custom class for debug messages
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication backends

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2', # Google OAuth2 backend
    'social_core.backends.facebook.FacebookOAuth2', # Facebook OAuth2 backend
    'accounts.backends.EmailOrPhoneBackend',  # Updated import path  Custom email/phone authentication backend
    'django.contrib.auth.backends.ModelBackend', # Default Django authentication backend
    'allauth.account.auth_backends.AuthenticationBackend',
)

# URL configuration for login, logout, and redirection after authentication
LOGIN_URL = '/accounts/user_account/'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = '/accounts/user_accounts/'
LOGOUT_REDIRECT_URL = "/"

# Google OAuth2 configuration   
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '588308411495-6oqjqjb1o5mb3lb9fg9ofbsk9lf4npci.apps.googleusercontent.com' #your-google-client-id  # Google client ID
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'  # Google client secret

# Google OAuth এর জন্য প্রয়োজনীয় স্কোপ
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

# Facebook OAuth2 configuration
SOCIAL_AUTH_FACEBOOK_KEY = '347774747615244'  # Facebook app ID
SOCIAL_AUTH_FACEBOOK_SECRET = 'd832728e607ac0abe0e0e6eace8bdae8'  # Facebook app secret

# Specify the custom social account adapter to handle user population and additional data
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,  # Use PKCE if required
    }
}


# TinyMCE configuration for rich text editor
TINYMCE_DEFAULT_CONFIG = {
    'height': 360,  # Height of the editor
    'width': 750,  # Width of the editor
    'cleanup_on_startup': True,  # Cleanup the content when starting
    'custom_undo_redo_levels': 20,  # Number of undo/redo levels
    'selector': 'textarea',  # Selects the textarea for TinyMCE
    'theme': 'modern',  # Theme for the editor
    'plugins': '''
        textcolor save link image media preview codesample contextmenu
        table code lists fullscreen insertdatetime nonbreaking
        directionality searchreplace wordcount visualblocks
        visualchars code fullscreen autolink lists charmap print hr
        anchor pagebreak
    ''',  # Plugins used in TinyMCE
    'toolbar1': '''
        fullscreen preview bold italic underline | fontselect,
        fontsizeselect | forecolor backcolor | alignleft alignright |
        aligncenter alignjustify | indent outdent | bullist numlist table |
        | link image media | codesample |
    ''',  # Toolbar configuration for TinyMCE
    'toolbar2': '''
        visualblocks visualchars |
        charmap hr pagebreak nonbreaking anchor | code |
    ''',  # Additional toolbar options
}

# Logging configuration for debugging
LOGGING = {
    'version': 1,  # Version of the logging configuration
    'disable_existing_loggers': False,  # Do not disable existing loggers
    'handlers': {
        'file': {
            'level': 'DEBUG',  # Log level for this handler
            'class': 'logging.FileHandler',  # File handler class
            'filename': 'debug.log',  # File where logs will be written
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],  # Use the file handler for the Django logger
            'level': 'DEBUG',  # Log level for the Django logger
            'propagate': True,  # Propagate logs to higher-level loggers
        },
    },
}

# Caching configuration for improved performance
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',  # Use in-memory caching
        'LOCATION': 'unique-snowflake',  # Unique identifier for the cache location
    }
}

# Load environment variables from .env file
load_dotenv()

# Email configuration for sending emails through Gmail

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'aminulpcp@gmail.com'
EMAIL_HOST_PASSWORD = 'zxkh cpza ugiz wwzc'
DEFAULT_FROM_EMAIL = 'aminulpcp@gmail.com' 