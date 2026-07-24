from django.db import models
from order.models import Order

SHIPPING = 'SHIPPING'
BILLING = 'BILLING'

class OrderAddress(models.Model):
    class AddressType(models.TextChoices):
        SHIPPING = 'SHIPPING','Shipping Address'
        BILLING = 'BILLING','Billing Address'
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE,null=True, blank=True, default=None)
    address_1 = models.CharField(max_length=200)
    address_2 = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=200)
    address_type = models.CharField(max_length=10,choices=AddressType.choices,default=AddressType.BILLING)