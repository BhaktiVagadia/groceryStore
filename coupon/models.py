from django.db import models
from django.core.validators import MinValueValidator, ValidationError
from django.utils import timezone


class Coupon(models.Model):
    class DiscountType(models.Choices):
        PERCENTAGE = 'Percentage'
        FIXED = 'Fixed'
    class Status(models.IntegerChoices):
        ENABLED = 1, 'Enabled'
        DISABLED = 0, 'Disabled'

    coupon_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(default='', blank=True, null=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount_type = models.CharField(max_length=15,choices=DiscountType.choices,default=DiscountType.PERCENTAGE)
    discount_value = models.FloatField(validators=[MinValueValidator(0)])
    min_total = models.FloatField(validators=[MinValueValidator(0)], default=0.0,null=True, blank=True)
    status = models.IntegerField(choices=Status.choices,default=Status.ENABLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.discount_type == 'percentage' and self.discount_value > 100:
            raise ValidationError({
                'discount_value': 'Percentage discount cannot be greater than 100%.'
            })

        if self.valid_from and self.valid_to:
            if self.valid_to <= self.valid_from:
                raise ValidationError({
                    'valid_to': 'Valid To must be later than Valid From.'
                })

    @classmethod
    def get_available_coupons(cls):
        now = timezone.now()
        return cls.objects.filter(status=1,valid_from__lte=now,valid_to__gte=now)


