from django.db import models

from products.models import Product

class ProductImage(models.Model):
    class Status(models.IntegerChoices):
        ENABLED = 1, 'Enabled'
        DISABLED = 0, 'Disabled'
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='')
    sort_order = models.IntegerField(default=0)
    status = models.BooleanField(choices=Status.choices,default=Status.ENABLED)
    is_base = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)