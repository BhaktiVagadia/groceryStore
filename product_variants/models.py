from django.db import models

from products.models import Product
from product_attributes.models import ProductAttribute

class ProductVariant(models.Model):
    class Status(models.IntegerChoices):
        ENABLED = 1, 'Enabled'
        DISABLED = 0, 'Disabled'
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute_id = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    attribute_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=200)
    status = models.BooleanField(choices=Status.choices,default=Status.ENABLED)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_id.name} ({self.attribute_name})"
