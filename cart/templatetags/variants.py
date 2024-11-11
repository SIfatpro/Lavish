from django import template

register = template.Library()

@register.filter
def get_variant_value_and_parent_name(product_variant, variant_type):
    # Check for each possible variant type and return the appropriate value along with its parent name
    if variant_type == 'color' and product_variant.color:
        return f"Color: {product_variant.color.name}"
    elif variant_type == 'size' and product_variant.size:
        return f"Size: {product_variant.size.name}"
    elif variant_type == 'brand' and product_variant.brand:
        return f"Brand: {product_variant.brand.name}"
    elif variant_type == 'capacity' and product_variant.capacity:
        return f"Capacity: {product_variant.capacity.capacity} GB"
    return None
