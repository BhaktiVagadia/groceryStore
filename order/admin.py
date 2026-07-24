from unittest import result

from django.contrib import admin
from order.models import Order
from django.utils import timezone


class OrderDateFilter(admin.SimpleListFilter):
    title = 'Date Range'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        # 1. Start with base database records
        counting_qs = Order.objects.all()

        # 2. Safely read standard parameters from URL instead of instantiating ChangeList
        status_filter = request.GET.get('status')
        if status_filter:
            counting_qs = counting_qs.filter(status=status_filter)

        search_query = request.GET.get('q')
        if search_query:
            counting_qs = counting_qs.filter(order_number__icontains=search_query)

        # 3. Calculate separate time splits safely without recursion loops
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = counting_qs.filter(created_at__gte=today_start).count()
        older_count = counting_qs.filter(created_at__lt=today_start).count()

        return (
            ('today', f"Today's Orders ({today_count})"),
            ('older', f"Older Orders ({older_count})"),
        )

    def queryset(self, request, queryset):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if self.value() == 'today':
            return queryset.filter(created_at__gte=today_start)
        if self.value() == 'older':
            return queryset.filter(created_at__lt=today_start)
        return queryset

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request,obj=None):
        return False

    list_display = ('order_number','status','row_total','shipping_amount','order_total','payment_type','shipping_method','tracking_number','tracking_link','created_at')
    list_filter = (OrderDateFilter,'status','payment_type')
    order_readonly_fields = ('order_number', 'row_total', 'shipping_amount', 'order_total', 'shipping_method', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.order_readonly_fields

        if obj.status == 5 or obj.status == 6:
            return self.order_readonly_fields + ('status', 'tracking_number', 'tracking_link')

        if obj.tracking_number:
            return self.order_readonly_fields + ('tracking_number', 'tracking_link')


        return self.order_readonly_fields
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'row_total', 'shipping_amount', 'order_total', 'shipping_method', 'created_at')
        }),
        ('Shipping Information', {
            'fields': ('status', 'tracking_number', 'tracking_link'),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        cl = self.get_changelist_instance(request)
        filtered_queryset = cl.get_queryset(request)

        # Define the time boundary
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Fetch the two distinct querysets
        todays_orders = filtered_queryset.filter(created_at__gte=today_start).order_by('-created_at')
        older_orders = filtered_queryset.filter(created_at__lt=today_start).order_by('-created_at')
        extra_context['todays_orders'] = todays_orders
        extra_context['older_orders'] = older_orders

        date_filter_value = request.GET.get('date_range')
        if date_filter_value == 'today':
            cl.result_count = todays_orders.count()
        elif date_filter_value == 'older':
            cl.result_count = older_orders.count()
        else:
            # If "All" is selected, the total count is the sum of both active grids
            cl.result_count = todays_orders.count() + older_orders.count()

        # Update the context with our adjusted changelist object
        extra_context['cl'] = cl

        return super().changelist_view(request, extra_context=extra_context)