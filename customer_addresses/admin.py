from django.contrib import admin

from customer_addresses.models import CustomerAddress

class CustomerAddressInline(admin.StackedInline):
    model = CustomerAddress
    extra = 0