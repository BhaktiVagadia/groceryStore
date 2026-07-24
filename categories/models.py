from django.db import models

class Category(models.Model):
    class Status(models.IntegerChoices):
        ENABLED = 1,'Enabled'
        DISABLED = 0,'Disabled'
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=200)
    description = models.TextField()
    parent_id = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,related_name='subcategories')
    path = models.CharField(max_length=200)
    status = models.BooleanField(choices=Status.choices,default=Status.ENABLED)
    image_url = models.ImageField(upload_to='')
    sort_order = models.IntegerField(default=0,null=True, blank=True)
    meta_title = models.CharField(max_length=200,null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        force_insert = kwargs.pop('force_insert', False)
        if not self.id:
            super(Category, self).save(*args, force_insert=force_insert, **kwargs)
        if self.parent_id:
            self.path = f"{self.parent_id.path}/{self.id}"
        else:
            self.path = str(self.id)
        super(Category, self).save(*args, **kwargs)


