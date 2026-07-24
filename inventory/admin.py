from django import forms
from django.contrib import admin
from inventory.models import Inventory
from product_variants.models import ProductVariant
from products.models import Product


# =========================================================================
# 1. Custom Form Configuration
# =========================================================================
class InventoryAdminForm(forms.ModelForm):
    product_choice = forms.ChoiceField(label="Product (Variant)", choices=[], required=True)

    class Meta:
        model = Inventory
        exclude = ('product', 'variant', 'sku', 'category', 'user', 'available_qty', 'reserved_qty')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', '---------')]

        # 1. Fetch IDs of products and variants that are ALREADY in the Inventory table
        assigned_product_ids = list(Inventory.objects.values_list('product_id', flat=True))
        assigned_variant_ids = list(
            Inventory.objects.exclude(variant__isnull=True).values_list('variant_id', flat=True))

        # 2. Handle list exclusion during edits
        if self.instance and self.instance.pk:
            if self.instance.product_id in assigned_product_ids:
                assigned_product_ids.remove(self.instance.product_id)
            if self.instance.variant_id in assigned_variant_ids:
                assigned_variant_ids.remove(self.instance.variant_id)

        # 3. Pull variants EXCLUDING the ones already assigned to inventory
        variants = ProductVariant.objects.select_related('product_id') \
            .exclude(id__in=assigned_variant_ids) \
            .order_by('product_id__name', 'attribute_name')
        for v in variants:
            choices.append((f"v_{v.id}", f"{v.product_id.name} ({v.attribute_name})"))

        # 4. Pull standalone products EXCLUDING the ones already assigned to inventory
        standalone_products = Product.objects.filter(productvariant__isnull=True) \
            .exclude(id__in=assigned_product_ids) \
            .order_by('name')
        for p in standalone_products:
            choices.append((f"p_{p.id}", p.name))

        self.fields['product_choice'].choices = choices

        # 5. Populate initial values correctly when editing an existing item
        if self.instance and self.instance.pk:
            if self.instance.variant:
                self.initial['product_choice'] = f"v_{self.instance.variant.id}"
            elif self.instance.product:
                self.initial['product_choice'] = f"p_{self.instance.product.id}"

            # 6. FIXED: Safely disable the field on the form level instead of using readonly_fields
            self.fields['product_choice'].disabled = True


# =========================================================================
# 2. Main Admin Grid Configuration
# =========================================================================
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    form = InventoryAdminForm

    exclude = ('sku', 'category', 'user', 'available_qty', 'reserved_qty')
    list_display = ('display_product', 'sku', 'display_category', 'qty', 'available_qty', 'reserved_qty', 'status',
                    'remark')
    search_fields = ('product__name', 'category__name', 'sku', 'qty')
    list_filter = ('status',)

    add_fields = ('product_choice', 'status', 'qty', 'remark')
    edit_fields = ('product_choice', 'status', 'qty', 'remark')

    @admin.display(description='Category')
    def display_category(self, obj):
        return obj.category.name if obj.category else "-"

    @admin.display(description='Product (Variant)')
    def display_product(self, obj):
        if obj.product and obj.variant:
            return obj.variant
        return str(obj.product) if obj.product else "-"

    def get_fields(self, request, obj=None):
        if obj:
            return self.edit_fields
        return self.add_fields

    # 7. FIXED: Cleaned up this method so it doesn't cause lookup AttributeErrors
    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.user = request.user

        # Calculate availability metrics
        if not change:
            obj.reserved_qty = 0
            obj.available_qty = obj.qty
        else:
            obj.available_qty = obj.qty - obj.reserved_qty

        # Intercept virtual key selection data string
        selected_choice = form.cleaned_data.get('product_choice')
        if selected_choice:
            if selected_choice.startswith('v_'):
                variant_id = selected_choice.replace('v_', '')
                variant_obj = ProductVariant.objects.get(id=variant_id)
                obj.variant = variant_obj
                obj.product = variant_obj.product_id

            elif selected_choice.startswith('p_'):
                product_id = selected_choice.replace('p_', '')
                obj.product = Product.objects.get(id=product_id)
                obj.variant = None

        # Auto-populate metadata snapshots from selected item before commit
        if obj.product:
            obj.category = obj.product.category_id
            obj.sku = obj.product.sku

        super().save_model(request, obj, form, change)
