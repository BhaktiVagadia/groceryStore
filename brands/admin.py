from django.contrib import admin
from brands.models import Brand
from django import forms
from django.utils.safestring import mark_safe

# class StatusCustomFilter(admin.SimpleListFilter):
#     title = 'Status'
#     parameter_name = 'status'
#
#     def lookups(self, request, model_admin):
#         return (
#             ('true', 'Enable'),
#             ('false', 'Disable'),
#         )
#
#     def queryset(self, request, queryset):
#         if self.value() == 'true':
#             return queryset.filter(status=True)
#         if self.value() == 'false':
#             return queryset.filter(status=False)
#         return queryset
#
# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'display_status', 'display_image', 'sort_order')
#     search_fields = ('name', 'description')
#     list_filter = (StatusCustomFilter,)
#
#     @admin.display(description='Status')
#     def display_status(self, obj):
#         return "Enable" if obj.status else "Disable"
#
#     @admin.display(description='Image')
#     def display_image(self, obj):
#         if obj.image_url:
#             url = obj.image_url.url
#             url = url.replace('//', '/').replace('/brand_images/brand_images/', '/brand_images/')
#             if not url.startswith('/'):
#                 url = f"/{url}"
#
#             return mark_safe(
#                 f'<img src="{url}" style="max-height: 50px; width: 50px; object-fit: contain; '
#                 f'border-radius: 4px; border: 1px solid #ddd; background: #fafafa;" '
#                 f'onerror="this.onerror=null; this.src=\'/static/admin/img/icon-unknown.svg\';" />'
#             )
#         return "No Image"
#
#
#     def formfield_for_dbfield(self, db_field, request, **kwargs):
#         if db_field.name == 'status':
#             kwargs['widget'] = forms.Select(choices=[(True, 'Enable'), (False, 'Disable')])
#         return super().formfield_for_dbfield(db_field, request, **kwargs)
#
#     def get_form(self, request, obj=None, change=False, **kwargs):
#         form = super().get_form(request, obj, change, **kwargs)
#         if 'status' in form.base_fields:
#             form.base_fields['status'].label = mark_safe('<span style="font-weight: bold;">Status</span>')
#             form.base_fields['status'].widget = forms.Select(choices=[(True, 'Enable'), (False, 'Disable')])
#         return form