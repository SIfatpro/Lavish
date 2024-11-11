from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.core import serializers
from ecommerce.models import Category, MainCategory, SliderImage, SubCategory
from products.models import Product, ProductImage, Rating  # Correct import
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def index(request):
    main_cat = MainCategory.objects.all().order_by('id')
    slider_images = SliderImage.objects.filter(active=True).order_by('order')
    
    # Corrected line: Change 'created_at' to 'created'
    new_product = Product.objects.prefetch_related('images').all().order_by('-created')[:6]  # Adjust based on your model
    
    flash_sale = Product.objects.filter(product_type='2').order_by('id')
    just_for_you = Product.objects.filter(product_type='3').order_by('id')
    just_for_you_total_count = just_for_you.count()

    # Fetch all categories
    categories = Category.objects.all()

    # Function to calculate rating for a list of products
    def calculate_product_ratings(products):
        for product in products:
            product.average_rating = Rating.get_average_rating(product.id)  # Calculate average rating
            product.total_ratings = Rating.get_total_ratings(product.id)  # Calculate total ratings
            
            # Calculate full stars and check for half stars
            product.full_stars = int(product.average_rating)  # Full stars (integer part)
            product.is_half_rating = product.average_rating % 1 >= 0.5  # Check if there's a half star
    
    # Calculate ratings for new_product, flash_sale, and just_for_you
    calculate_product_ratings(new_product)
    calculate_product_ratings(flash_sale)
    calculate_product_ratings(just_for_you)

    context = {
        'main_cat': main_cat,
        'slider_images': slider_images,
        'new_product': new_product,
        'flash_sale': flash_sale,
        'just_for_you': just_for_you,
        'just_for_you_total_count': just_for_you_total_count,
        'categories': categories,
    }

    return render(request, 'index.html', context)

def track(request):
    return render(request, 'track.html')

def category_detail(request, category_slug, subcategory_slug=None):
    category = get_object_or_404(Category, slug=category_slug)
    main_cat = MainCategory.objects.all().order_by('id')
    products = Product.objects.filter(is_active=True, sub_category__category=category).select_related('sub_category')

    # Count total products in the category
    total_category_products = products.count()

    # If a subcategory is specified, filter products by subcategory
    if subcategory_slug:
        subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
        products = products.filter(sub_category=subcategory)
        total_subcategory_products = products.count()
    else:
        subcategory = None
        total_subcategory_products = None

    # Loop through products and calculate ratings for each product
    for product in products:
        product.average_rating = Rating.get_average_rating(product.id)
        product.total_ratings = Rating.get_total_ratings(product.id)
        product.full_stars = int(product.average_rating)
        product.is_half_rating = product.average_rating % 1 >= 0.5

    # Pagination logic
    paginator = Paginator(products, 4)
    page = request.GET.get('page')
    try:
        products_paginated = paginator.page(page)
    except PageNotAnInteger:
        products_paginated = paginator.page(1)
    except EmptyPage:
        products_paginated = paginator.page(paginator.num_pages)

    context = {
        'main_cat': main_cat,
        'category': category,
        'subcategory': subcategory,
        'products': products_paginated,
        'total_category_products': total_category_products,
        'total_subcategory_products': total_subcategory_products,
        'cat_name': category.cat_name,
    }

    return render(request, 'category.html', context)


def subcategory_detail(request, category_slug, subcategory_slug):
    category = get_object_or_404(Category, slug=category_slug)
    subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
    main_cat = MainCategory.objects.all().order_by('id')

    products = Product.objects.filter(is_active=True, sub_category=subcategory).select_related('sub_category')

    # Count total products in the subcategory
    total_subcategory_products = products.count()

    for product in products:
        product.average_rating = Rating.get_average_rating(product.id)
        product.total_ratings = Rating.get_total_ratings(product.id)
        product.full_stars = int(product.average_rating)
        product.is_half_rating = product.average_rating % 1 >= 0.5

    paginator = Paginator(products, 4)
    page = request.GET.get('page')
    try:
        products_paginated = paginator.page(page)
    except PageNotAnInteger:
        products_paginated = paginator.page(1)
    except EmptyPage:
        products_paginated = paginator.page(paginator.num_pages)

    context = {
        'main_cat': main_cat,
        'category': category,
        'subcategory': subcategory,
        'products': products_paginated,
        'total_subcategory_products': total_subcategory_products,
        'cat_name': category.cat_name,
        'sub_name': subcategory.sub_name,
    }

    return render(request, 'subcategory.html', context)

def load_more(request):
    offset = int(request.POST.get('offset', 0))  # Default to 0 if offset not provided
    limit = 6
    posts = Product.objects.all()[offset:offset + limit]  # Adjusted slicing logic
    total_data = Product.objects.count()
    
    posts_json = serializers.serialize('json', posts)
    
    return JsonResponse(data={
        'posts': posts_json,
        'totalResult': total_data
    })
