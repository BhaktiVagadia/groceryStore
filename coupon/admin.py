from django.contrib import admin
from coupon.models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code','status','discount_type','discount_value')
    search_fields = ('coupon_code','discount_value')
    list_filter = ('status',)