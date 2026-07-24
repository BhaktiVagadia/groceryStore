from django.db import models
from order.models import Order
from django.contrib.auth.models import User

class OrderStatusChange(models.Model):
    class Status(models.IntegerChoices):
        PLACED = 1, 'Placed'
        PAYMENT_CONFIRMED = 2, 'Payment Confirmed'
        CONFIRMED = 3, 'Confirmed'
        SHIPPED = 4, 'Shipped'
        DELIVERED = 5, 'Delivered'
        CANCELED = 6, 'Canceled'

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete =models.SET_NULL, null=True,blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.PLACED)
    new_status = models.IntegerField(choices=Status.choices, default=Status.PLACED)
    user_name = models.CharField(max_length=50)
    remark = models.CharField(max_length=200)
    tracking_number = models.CharField(max_length=50,null=True, blank=True, default=None)
    tracking_link = models.CharField(max_length=200,null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)