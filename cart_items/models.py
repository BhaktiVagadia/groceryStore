from django.db import models
from cart.models import Cart
from product_variants.models import ProductVariant
from products.models import Product
from categories.models import Category
class CartItem(models.Model):
    cart_id = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    variant_id = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    product_name = models.CharField(max_length=200)
    category_id = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    qty = models.IntegerField()
    price = models.FloatField()
    total_price = models.FloatField()

    def display_name(self):
        if self.variant_id:
            return f"{self.product_name} ({self.variant_id.attribute_name})"
        return self.product_name
