from django.db import models

from product_variants.models import ProductVariant
from products.models import Product


class NotifyCustomers(models.Model):
    class IsNotiFied(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 0, 'No'
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,default=None,null=True,blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    is_notified = models.BooleanField(choices=IsNotiFied.choices,default=IsNotiFied.NO)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
