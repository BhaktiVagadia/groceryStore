from django.db import models

# Create your models here.
class Customer(models.Model):
    class Status(models.IntegerChoices):
        ENABLED = 1, 'Enabled'
        DISABLED = 0, 'Disabled'
    name = models.CharField(max_length=200)
    email = models.EmailField()
    mo_no = models.CharField(max_length=20)
    password = models.CharField(max_length=200)
    status = models.BooleanField(choices=Status.choices,default=Status.ENABLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)