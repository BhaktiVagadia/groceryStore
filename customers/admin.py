# from django.contrib import admin
# from customers.models import Customer
# from customer_addresses.admin import CustomerAddressInline
# from django import forms
# from django.utils.safestring import mark_safe
#
# @admin.register(Customer)
# class CustomerAdmin(admin.ModelAdmin):
#     inlines = [CustomerAddressInline]
#
#     list_display = ('name', 'email', 'mo_no', 'display_address_1', 'display_address_2','display_zipcode','display_city','display_state','display_country')
#     search_fields = ('name','email','mo_no')
#     list_filter = ('status',)
#
#     @admin.display(description='Address 1')
#     def display_address_1(self, obj):
#         billing_address = obj.addresses.filter(default_billing=True).first()
#         if billing_address:
#             return billing_address.address_1
#         first_addr = obj.addresses.first()
#         return first_addr.address_1 if first_addr else "—"
#
#     @admin.display(description='Address 2')
#     def display_address_2(self, obj):
#         billing_address = obj.addresses.filter(default_billing=True).first()
#         if billing_address:
#             return  billing_address.address_2 if billing_address.address_2 else "-"
#         first_addr = obj.addresses.first()
#         return first_addr.address_2 if (first_addr and first_addr.address_2) else "—"
#
#     @admin.display(description='City')
#     def display_city(self, obj):
#         billing_address = obj.addresses.filter(default_billing=True).first()
#         if billing_address:
#             return billing_address.city
#         first_addr = obj.addresses.first()
#         return first_addr.city if first_addr else "—"
#
#     @admin.display(description='State')
#     def display_state(self, obj):
#         billing_address = obj.addresses.filter(default_billing=True).first()
#         if billing_address:
#             return billing_address.state
#         first_addr = obj.addresses.first()
#         return first_addr.state if first_addr else "—"
#
#     @admin.display(description='Country')
#     def display_country(self, obj):
#         billing_address = obj.addresses.filter(default_billing=True).first()
#         if billing_address:
#             return billing_address.country
#         first_addr = obj.addresses.first()
#         return first_addr.country if first_addr else "—"
#
#     @admin.display(description='Zipcode')
#     def display_zipcode(self, obj):
#         billing_address = obj.addresses.filter(default_billing=True).first()
#         if billing_address:
#             return billing_address.zip_code
#         first_addr = obj.addresses.first()
#         return first_addr.zip_code if first_addr else "—"
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.prefetch_related('addresses')
#
#     def get_form(self, request, obj=None, change=False, **kwargs):
#         form = super().get_form(request, obj, change, **kwargs)
#         for field_name, field in form.base_fields.items():
#             if isinstance(field.widget, forms.Select) or isinstance(field, (forms.ChoiceField, forms.ModelChoiceField)):
#                 current_label = field.label or field_name.replace('_', ' ').title()
#                 field.label = mark_safe(f'<span style="font-weight: bold;">{current_label}</span>')
#             if field_name == 'status':
#                 form.base_fields['status'].widget = forms.Select(choices=[(True, 'Enable'), (False, 'Disable')])
#         return form
