from django.db import models

from categories.models import Category
from brands.models import Brand

class Product(models.Model):
    class Status(models.IntegerChoices):
        ENABLED = 1, 'Enabled'
        DISABLED = 0, 'Disabled'
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=200)
    description = models.TextField()
    status = models.BooleanField(choices=Status.choices,default=Status.ENABLED)
    sort_order = models.IntegerField(null=True, blank=True,default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reseller_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    category_id = models.ForeignKey(Category,related_name='products',  on_delete=models.CASCADE)
    brand_id = models.ForeignKey(Brand, on_delete=models.CASCADE,null=True, blank=True,default=None)
    meta_title = models.CharField(max_length=200,null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_available(self):
        if not getattr(self, 'status', True):
            return False

        return self.inventory_set.filter(
            status=1,
            available_qty__gt=0
        ).exists()

    def get_display_image_url(self):
        # Look for the image marked as base
        base_image = self.productimage_set.filter(is_base=1).first()
        if base_image and base_image.image:
            return base_image.image.url

        # Fallback to the first image if no base image exists
        first_image = self.productimage_set.first()
        if first_image and first_image.image:
            return first_image.image.url

        return ""

    def get_ordered_images(self):
        # Sorts by is_base descending (1 before 0), then by id
        return self.productimage_set.all().order_by('-is_base', 'id')