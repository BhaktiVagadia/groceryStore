from django.db import models

from cart.models import Cart
from coupon.models import Coupon
from customers.models import Customer

class Order(models.Model):
    class Status(models.IntegerChoices):
        PLACED = 1, 'Placed'
        PAYMENT_CONFIRMED = 2, 'Payment Confirmed'
        CONFIRMED = 3, 'Confirmed'
        SHIPPED = 4, 'Shipped'
        DELIVERED = 5, 'Delivered'
        CANCELED = 6, 'Canceled'

    class PaymentType(models.IntegerChoices):
        COD = 0, 'Cod'
        ONLINE = 1, 'Online'

    cart_id = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True, default=None)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, default=None)
    customer_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    customer_email = models.EmailField(max_length=200, null=True, blank=True, default=None)
    customer_mo_no = models.CharField(max_length=200, null=True, blank=True, default=None)
    row_total = models.FloatField(null=True, blank=True, default=None)
    order_total = models.FloatField(null=True, blank=True, default=None)
    discount_rate = models.FloatField(null=True, blank=True, default=None)
    discount_amount = models.FloatField(null=True, blank=True, default=None)
    shipping_amount = models.FloatField(null=True, blank=True, default=100)
    shipping_method = models.CharField(max_length=200, null=True, blank=True, default='Flate Rate')
    order_number = models.CharField(max_length=200)
    status = models.IntegerField(choices=Status.choices, default=Status.PLACED)
    coupon_code = models.CharField(max_length=200, null=True, blank=True, default=None)
    coupon_id = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    tracking_number = models.CharField(max_length=200, null=True, blank=True, default=None)
    tracking_link = models.CharField(max_length=200, null=True, blank=True, default=None)
    cancellation_reason = models.TextField(blank=True, null=True)
    payment_type = models.IntegerField(choices=PaymentType.choices,default=PaymentType.COD)
    tax_amount = models.FloatField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
