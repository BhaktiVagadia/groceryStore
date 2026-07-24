from django.db import models
from cart.models import Cart

class CartPayment(models.Model):
    class Status(models.Choices):
        CREATED = 'Created'
        SUCCESS = 'Success'
        FAILED = 'Failed'
    class PaymentMethod(models.Choices):
        ONLINE = 'Online'
        COD = 'Cod'
    cart_id = models.ForeignKey(Cart, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100,blank=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField()
    status = models.CharField(max_length=50,choices=Status.choices,default=Status.CREATED)  # Created, Success, Failed
    payment_method = models.CharField(max_length=50,choices=PaymentMethod.choices, default=PaymentMethod.ONLINE)
    created_at = models.DateTimeField(auto_now_add=True)