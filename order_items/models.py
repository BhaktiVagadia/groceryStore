from django.db import models
from order.models import Order
from product_variants.models import ProductVariant
from products.models import Product
from categories.models import Category
class OrderItem(models.Model):
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    variant_id = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    product_name = models.CharField(max_length=200)
    category_id = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    qty = models.IntegerField()
    price = models.FloatField()
    total_price = models.FloatField()
