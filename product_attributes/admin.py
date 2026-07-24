from django.contrib import admin
from product_attributes.models import ProductAttribute


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'is_filterable', 'status')
    list_filter = ('type', 'status', 'is_filterable')
    search_fields = ('name', 'code')