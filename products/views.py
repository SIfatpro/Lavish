from django.shortcuts import render, get_object_or_404 # type: ignore
from .models import Product, Rating  # Ensure Rating is imported
from django.db.models import Prefetch # type: ignore

def product_detail(request, product_slug):
    # Fetch the product with related data using Prefetch to optimize queries
    product = get_object_or_404(
        Product.objects.prefetch_related(
            Prefetch('reviews'),
            Prefetch('productvariant_set__color'),
            Prefetch('productvariant_set__size'),
            Prefetch('images')
        ),
        slug=product_slug
    )

    # Fetch reviews, product variants, and product images from pre-fetched data
    reviews = product.reviews.all()
    product_variants = product.productvariant_set.all()
    product_images = product.images.all()

    # Separate primary and secondary images
    primary_image = product_images.filter(is_primary=True).first()  # Get the primary image
    secondary_images = product_images.filter(is_primary=False)  # Get all secondary images

    # Modify color codes and fetch sizes
    colors_with_modified_code = [
        {'name': color.name, 'code': color.code.replace('#', '')}
        for color in product.colors.all()
    ]
    sizes = product.sizes.all()

    # Calculate average rating and total ratings using Rating model
    average_rating = Rating.get_average_rating(product.id)
    total_ratings = Rating.get_total_ratings(product.id)

    # Check for half rating
    is_half_rating = average_rating % 1 >= 0.5  # True if average_rating has a half
    full_stars = int(average_rating)  # Get the integer part for full stars

    # Create a dictionary to hold the first image for each color
    color_images = {}
    for color in product.colors.all():
        image = product.images.filter(variants__color=color).first()
        if image:
            color_images[color.id] = image.image.url

    # Build the context for rendering the template
    context = {
        'product': product,
        'colors_with_modified_code': colors_with_modified_code,
        'sizes': sizes,
        'reviews': reviews,
        'product_variants': product_variants,
        'primary_image': primary_image,  # Pass the primary image
        'secondary_images': secondary_images,  # Pass the secondary images
        'average_rating': average_rating,
        'total_ratings': total_ratings,
        'full_stars': full_stars,  # Add this to context
        'is_half_rating': is_half_rating,  # Add this to context
        'color_images': color_images,
    }

    # Render the template with the context
    return render(request, 'product_detail.html', context)
