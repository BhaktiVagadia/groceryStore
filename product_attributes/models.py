from django.db import models

class ProductAttribute(models.Model):

    TYPE_CHOICES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('select', 'Dropdown Select'),
        ('multiselect', 'Multi-Select Checkboxes'),
        ('boolean', 'Yes / No Toggle'),
        ('color', 'Color Swatch'),
    ]

    class Types(models.TextChoices):
        TEXT = 'text', 'Text',
        TEXTAREA = 'textarea', 'Text Area',
        NUMBER = 'number', 'Number',
        select = 'select', 'Dropdown Select',
        multiselect = 'multiselect', 'Yes / No Toggle',
        boolean = 'boolean', 'Yes / No Toggle',
        color = 'color', 'Color Swatch',

    class Status(models.IntegerChoices):
        ENABLED = 1, 'Enabled'
        DISABLED = 0, 'Disabled'

    class IsFilterable(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 0, 'No'

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    type = models.CharField(max_length=50, choices=Types.choices, default=Types.TEXT)
    is_filterable = models.BooleanField(choices=IsFilterable.choices,default=IsFilterable.YES)
    status = models.BooleanField(choices=Status.choices,default=Status.ENABLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name