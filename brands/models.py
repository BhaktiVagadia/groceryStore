from django.db import models

class Brand(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    sku = models.CharField(max_length=200,default=None,null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    image_url = models.ImageField(upload_to='')
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name