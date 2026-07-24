from django.contrib.auth.models import User
from django.db import models
from categories.models import Category
from products.models import Product
from product_variants.models import ProductVariant

class Inventory(models.Model):
    class Status(models.IntegerChoices):
        IN_STOCK = 1, 'IN Stock'
        OUT_STOCK = 0, 'Out Stock'

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,null=True,blank=True )
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True,blank=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.OUT_STOCK)
    qty = models.IntegerField()
    available_qty = models.IntegerField()
    reserved_qty = models.IntegerField()
    remark = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Inventory"
        verbose_name_plural = "Inventories"
