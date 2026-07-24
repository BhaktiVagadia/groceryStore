from django.db import models
from order.models import Order

class OrderPayment(models.Model):
    class Status(models.Choices):
        CREATED = 'Created'
        SUCCESS = 'Success'
        FAILED = 'Failed'
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=100,blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100,blank=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    refund_id = models.CharField(max_length=200, null=True, blank=True, default=None)
    amount = models.FloatField()
    status = models.CharField(choices=Status.choices,max_length=50, default=Status.CREATED)  # Created, Success, Failed
    created_at = models.DateTimeField(auto_now_add=True)