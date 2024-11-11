from django.contrib import admin
from ecommerce import models
# Register your models here.
class MainCategory(admin.ModelAdmin):
    list_display    = ('main_name','slug')
    search_fields   = ('main_name',)
    list_filter     = ('main_name',)
    list_per_page = 15

class Category(admin.ModelAdmin):
    list_display    = ('cat_name','slug','logo','banner')
    search_fields   = ('cat_name',)
    list_filter     = ('cat_name',)
    list_per_page = 15

class SubCategory(admin.ModelAdmin):
    list_display    = ('sub_name','slug','banner')
    search_fields   = ('sub_name',)
    list_filter     = ('sub_name',)
    list_per_page = 15


admin.site.register(models.MainCategory)
admin.site.register(models.Category)
admin.site.register(models.SubCategory)
admin.site.register(models.SliderImage)

