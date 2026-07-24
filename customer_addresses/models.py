from django.db import models

from customers.models import Customer

class CustomerAddress(models.Model):
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE,related_name='addresses' )
    address_1 = models.CharField(max_length=200)
    address_2 = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=200)
    default_billing = models.BooleanField(default=False)
    default_shipping = models.BooleanField(default=False)
    mo_no = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)