from django.db import models # type: ignore
from autoslug import AutoSlugField # type: ignore

class MainCategory(models.Model):
    main_name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from='main_name', unique=True, blank=True, null=True)

    def __str__(self):
        return self.main_name

class Category(models.Model):
    main_name = models.ForeignKey(MainCategory, on_delete=models.CASCADE)
    cat_name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from='cat_name', unique=True, blank=True, null=True)
    logo = models.ImageField(upload_to='category_logos/', null=True, blank=True)  # Field for category logo
    banner = models.ImageField(upload_to='category_banners/', null=True, blank=True)  # Field for category banner

    def __str__(self):
        return f'{self.main_name} - {self.cat_name}'

class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    sub_name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from='sub_name', unique=True, blank=True, null=True)
    banner = models.ImageField(upload_to='category_banners/', null=True, blank=True)  # Field for category banner

    def __str__(self):
        return f'{self.category.cat_name} - {self.sub_name}'

class SliderImage(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='slider_images/')
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class SearchHistory(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)  # Delayed import
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

class PopularSearch(models.Model):
    term = models.CharField(max_length=255)
    count = models.IntegerField(default=0)

class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
