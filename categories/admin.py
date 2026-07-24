from django.contrib import admin
from categories.models import Category
from django import forms
from django.utils.safestring import mark_safe

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku' , 'description', 'status', 'display_image','parent_category','display_path_name')
    search_fields = ('name','sku', 'description')
    list_filter = ('status',)
    fields = ('name','sku' ,'description', 'parent_id', 'status','image_url','sort_order','meta_title','meta_description')

    @admin.display(description='Parent Category')
    def parent_category(self, obj):
        return "-" if not obj.parent_id else obj.parent_id.name

    @admin.display(description='Category Path')
    def display_path_name(self, obj):
        if not obj.path:
            return "—"
        try:
            id_list = [int(x) for x in obj.path.split('/') if x.strip().isdigit()]
            if not id_list:
                return obj.path
            categories = Category.objects.filter(id__in=id_list)
            category_map = {cat.id: cat.name for cat in categories}
            named_segments = [category_map[cat_id] for cat_id in id_list if cat_id in category_map]
            return " / ".join(named_segments)
        except Exception:
            return obj.path

    @admin.display(description='Image')
    def display_image(self, obj):
        if obj.image_url:
            url = obj.image_url.url
            url = url.replace('//', '/').replace('/category_images/category_images/', '/category_images/')
            if not url.startswith('/'):
                url = f"/{url}"

            return mark_safe(
                f'<img src="{url}" style="max-height: 50px; width: 50px; object-fit: contain; '
                f'border-radius: 4px; border: 1px solid #ddd; background: #fafafa;" '
                f'onerror="this.onerror=null; this.src=\'/static/admin/img/icon-unknown.svg\';" />'
            )
        return "No Image"