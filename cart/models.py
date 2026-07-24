from django.db import models

from coupon.models import Coupon
from customers.models import Customer
from django.utils import timezone


class Cart(models.Model):
    class Status(models.IntegerChoices):
        DEACTIVE = 0, 'Deactive'
        ACTIVE  = 1, 'Active'
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True, default=None)
    customer_name = models.CharField(max_length=200,null=True, blank=True, default=None)
    customer_email = models.EmailField(max_length=200, null=True, blank=True, default=None)
    customer_mo_no = models.CharField(max_length=200, null=True, blank=True, default=None)
    row_total = models.FloatField(null=True, blank=True, default=None)
    cart_total = models.FloatField(null=True, blank=True, default=None)
    discount_rate = models.FloatField(null=True, blank=True, default=None)
    discount_amount = models.FloatField(null=True, blank=True, default=None)
    shipping_amount = models.FloatField(null=True, blank=True, default=100)
    shipping_method = models.CharField(max_length=200,null=True, blank=True, default='Flate Rate')
    session_id = models.CharField(max_length=200)
    status = models.BooleanField(choices=Status.choices,default=Status.ACTIVE)
    coupon_code = models.CharField(max_length=200,null=True, blank=True, default=None)
    coupon_id = models.ForeignKey(Coupon, on_delete=models.SET_NULL,null=True, blank=True, default=None)
    tax_amount = models.FloatField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):

        if self.coupon_id:
            now = timezone.now()

            is_valid = (self.coupon_id.status == 1 and self.coupon_id.valid_from <= now and self.coupon_id.valid_to >= now and self.row_total >= self.coupon_id.min_total)
            if is_valid:
                if self.coupon_id.discount_type == 'Percentage':
                    self.discount_amount = self.row_total * self.coupon_id.discount_value /100
                    self.discount_rate = self.coupon_id.discount_value
                else:
                    self.discount_amount = self.coupon_id.discount_value
                    self.discount_rate = 0

                if self.discount_amount > self.row_total:
                    self.discount_amount = self.row_total
            else:
                self.coupon_id = None
                self.discount_amount = 0.00
                self.discount_rate = 0
                self.coupon_code = None
        else:
            self.discount_amount = 0.00
            self.discount_rate = 0
        super().save(*args, **kwargs)