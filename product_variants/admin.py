from django.contrib import admin
from product_variants.models import ProductVariant


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    fk_name = 'product_id'
    extra = 0
    fields = ('attribute_id', 'attribute_name', 'sku', 'price', 'sort_order', 'status')
    autocomplete_fields = ('attribute_id',)