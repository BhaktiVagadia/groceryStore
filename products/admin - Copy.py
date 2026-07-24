import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.conf import settings
from django.contrib import admin
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils.text import slugify

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.results import RowResult
from import_export.widgets import Widget

from product_variants.admin import ProductVariantInline
from products.models import Product  # NOTE: adjust `Category` import to your actual app/model
from product_images.admin import ProductImageInline
from categories.models import Category
from brands.models import Brand
from product_images.models import ProductImage
from product_attributes.models import ProductAttribute
from product_variants.models import ProductVariant  # NOTE: adjust to your actual app path if different

logger = logging.getLogger(__name__)

QUANTITY_ATTRIBUTE_CODE = 'quantity'

# How many images to fetch in parallel after the row-import loop finishes.
# Keep this modest - it's bounded by the remote hosts' tolerance, not just ours.
IMAGE_FETCH_WORKERS = 8
IMAGE_FETCH_TIMEOUT = 8  # seconds per request; fail fast, don't hold a thread open for 10s x 8000


def _generate_unique_sku(name, existing_skus, max_length=64):
    """Build a slug-based SKU, appending -2, -3, ... until it's unique against
    the `existing_skus` set. Mutates `existing_skus` to include the result so
    repeated calls within the same import stay consistent without re-querying
    the DB every time."""
    base_slug = slugify(name)[:max_length] or "item"
    sku = base_slug
    suffix = 1
    while sku in existing_skus:
        suffix += 1
        candidate_suffix = f"-{suffix}"
        sku = f"{base_slug[:max_length - len(candidate_suffix)]}{candidate_suffix}"
    existing_skus.add(sku)
    return sku


class CategoryOrIdWidget(Widget):
    """
    Accepts either:
    - a numeric string -> treated as an existing Category's pk
    - a string matching an existing Category's sku -> that Category
    - a plain name -> get_or_create'd by name, auto-assigning a new sku if created

    `resource` (set by ProductResource before use) supplies a cached
    `_category_skus` set so we don't hit the DB for every new category.
    """

    def __init__(self, resource=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = resource

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return None
        value = str(value).strip()
        if value.isdigit():
            try:
                return Category.objects.get(pk=int(value))
            except Category.DoesNotExist:
                return None
        try:
            return Category.objects.get(sku=value)
        except Category.DoesNotExist:
            pass
        try:
            category, created = Category.objects.get_or_create(name=value)
            if created and not category.sku:
                existing = self.resource._category_skus if self.resource is not None else set(
                    Category.objects.values_list('sku', flat=True)
                )
                category.sku = _generate_unique_sku(value, existing)
                category.save(update_fields=['sku'])
        except Exception as e:
            logger.exception("CategoryOrIdWidget.clean failed for %r", value)
            raise e
        return category

    def render(self, value, obj=None):
        return value.sku if value else ''


class BrandOrIdWidget(Widget):
    """
    Accepts either:
    - a numeric string -> treated as an existing Brand's pk
    - a string matching an existing Brand's sku -> that Brand
    - a plain name -> get_or_create'd by name, auto-assigning a new sku if created

    `resource` (set by ProductResource before use) supplies a cached
    `_brand_skus` set so we don't hit the DB for every new brand.
    """

    def __init__(self, resource=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = resource

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return None
        value = str(value).strip()
        if value.isdigit():
            try:
                return Brand.objects.get(pk=int(value))
            except Brand.DoesNotExist:
                return None
        try:
            return Brand.objects.get(sku=value)
        except Brand.DoesNotExist:
            pass
        try:
            brand, created = Brand.objects.get_or_create(name=value)
            if created and not brand.sku:
                existing = self.resource._brand_skus if self.resource is not None else set(
                    Brand.objects.values_list('sku', flat=True)
                )
                brand.sku = _generate_unique_sku(value, existing)
                brand.save(update_fields=['sku'])
        except Exception as e:
            logger.exception("BrandOrIdWidget.clean failed for %r", value)
            raise e
        return brand

    def render(self, value, obj=None):
        return value.sku if value else ''


class ProductResource(resources.ModelResource):

    # NOTE: use_transactions = False is the single most important change here.
    # With the default (True), import-export wraps ALL rows in one DB
    # transaction, so nothing commits until every row - and every synchronous
    # network call inside after_import_row - has finished. On an 8000-row
    # file that's easily long enough to hit a gunicorn/nginx/DB timeout,
    # which kills the request and rolls back the entire import, even rows
    # that were already fully processed. With this off, each row commits as
    # it's processed, so a timeout only loses what hasn't run yet.
    class Meta:
        model = Product
        use_transactions = False
        skip_unchanged = True
        report_skipped = False
        chunk_size = 200
        fields = ('id', 'name', 'sku', 'description', 'status', 'sort_order', 'price', 'reseller_price',
                   'selling_price', 'category_id', 'brand_id', 'meta_title', 'meta_description', 'images')

    images = fields.Field(column_name='images')
    category_id = fields.Field(attribute='category_id', column_name='Category', widget=CategoryOrIdWidget())
    brand_id = fields.Field(attribute='brand_id', column_name='Brand', widget=BrandOrIdWidget())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._used_skus = set()
        self._catalog_group_skus = {}
        self._category_skus = set()
        self._brand_skus = set()
        self._quantity_attribute_cache = None
        # Deferred work collected during the row loop, executed once after
        # all rows have been processed (see after_import).
        self._pending_image_downloads = []  # list of (product_id, image_url)

        # Wire the widgets to this resource instance so they can use the
        # cached sku sets above instead of re-querying the DB per row.
        self.fields['category_id'].widget.resource = self
        self.fields['brand_id'].widget.resource = self

    def dehydrate_images(self, product):
        product_images = ProductImage.objects.filter(product_id=product)
        paths = []
        if settings.DEBUG:
            base_url = "http://127.0.0.1:8000"
        else:
            live_domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
            live_domain = live_domain.lstrip('.')
            base_url = f"https://{live_domain}"
        for pi in product_images:
            if pi.image:
                paths.append(f"{base_url}{pi.image.url}")
        return ", ".join(paths)

    def before_import(self, dataset, **kwargs):
        self._used_skus = set(Product.objects.values_list('sku', flat=True))
        self._catalog_group_skus = {}
        self._category_skus = set(Category.objects.values_list('sku', flat=True))
        self._brand_skus = set(Brand.objects.values_list('sku', flat=True))
        self._quantity_attribute_cache = None
        self._pending_image_downloads = []
        super().before_import(dataset, **kwargs)

    def after_import(self, dataset, result, **kwargs):
        """Run once, after every row has been processed. This is where we do
        the slow, network-bound work (image downloads) instead of doing it
        synchronously inside each row - and we do it in parallel instead of
        one request at a time."""
        super().after_import(dataset, result, **kwargs)

        if kwargs.get('dry_run'):
            self._pending_image_downloads = []
            return

        if not self._pending_image_downloads:
            return

        self._run_pending_image_downloads()

    def get_instance(self, instance_loader, row):
        if 'ProductName' in row:
            try:
                return Product.objects.get(sku=row.get('sku'))
            except Product.DoesNotExist:
                return None
        return super().get_instance(instance_loader, row)

    def before_import_row(self, row, row_number=None, **kwargs):
        if 'ProductName' in row:
            self._normalize_catalog_row(row)
            self._ensure_subcategory(row)

    def _normalize_catalog_row(self, row):
        """Rewrite a BigBasket-style row into this resource's own field names."""
        name = (row.get('ProductName') or '').strip()
        brand = (row.get('Brand') or '').strip()

        row['name'] = name[:255]
        row['sku'] = self._get_group_sku(name, brand)
        row['description'] = brand[:500]
        row['price'] = row.get('Price')
        row['reseller_price'] = row.get('Price')
        row['selling_price'] = row.get('DiscountPrice') or row.get('Price')
        row['status'] = True
        row['sort_order'] = 0
        row['meta_title'] = name[:255]
        row['meta_description'] = f"{name} - {brand}".strip()[:255]
        # NOTE: row['Brand'] is left untouched here - the brand_id field
        # (column_name='Brand') reads it separately via BrandOrIdWidget.

    def _ensure_subcategory(self, row):
        subcategory_name = (row.get('SubCategory') or '').strip()
        category_name = (row.get('Category') or '').strip()

        # Persist BOTH the top-level Category and the SubCategory as their
        # own rows in the Category table, regardless of which one ends up
        # being linked to the product below.
        category = None
        subcategory = None

        if category_name:
            category, created = Category.objects.get_or_create(name=category_name)
            if created and not category.sku:
                category.sku = _generate_unique_sku(category_name, self._category_skus)
                category.save(update_fields=['sku'])

        if subcategory_name:
            subcategory, created = Category.objects.get_or_create(
                name=subcategory_name,
                defaults={'parent_id': category} if category else {},
            )
            if created and not subcategory.sku:
                subcategory.sku = _generate_unique_sku(subcategory_name, self._category_skus)
                subcategory.save(update_fields=['sku'])
            # If the subcategory already existed but didn't have this
            # category set as its parent yet, link it now.
            if category and subcategory.parent_id_id != category.pk:
                subcategory.parent_id = category
                subcategory.save(update_fields=['parent_id'])

        # The product itself links to the SubCategory when one was provided,
        # otherwise it falls back to the Category.
        category_to_link = subcategory if subcategory else category

        if not category_to_link:
            row['Category'] = ''
            return

        # NOTE: the category_id field's column_name is 'Category', so
        # import-export reads the value from row['Category'] - not
        # row['category_id']. Writing to the wrong key silently falls
        # back to the raw, untouched Category column text.
        row['Category'] = str(category_to_link.pk)

    def _get_group_sku(self, name, brand):
        key = (slugify(name), slugify(brand))
        if key in self._catalog_group_skus:
            return self._catalog_group_skus[key]

        base_slug = slugify(f"{name}-{brand}") or slugify(name) or "product"
        base_slug = base_slug[:45]
        sku = base_slug
        suffix = 1
        while sku in self._used_skus:
            suffix += 1
            sku = f"{base_slug}-{suffix}"

        self._used_skus.add(sku)
        self._catalog_group_skus[key] = sku
        return sku

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        if row_result.import_type not in (RowResult.IMPORT_TYPE_NEW, RowResult.IMPORT_TYPE_UPDATE):
            return

        # Skip side effects (variant creation, image download) during the
        # dry-run preview pass - only act once the import is actually committed.
        if kwargs.get('dry_run'):
            return

        try:
            product = Product.objects.get(sku=row.get('sku'))
        except Product.DoesNotExist:
            return

        if 'ProductName' in row:
            quantity_value = (row.get('Quantity') or '').strip()
            if quantity_value:
                variant_price = row.get('selling_price') or row.get('price')
                self._create_quantity_variant(product, quantity_value, variant_price)

            image_url = (row.get('Image_Url') or '').strip()
            if image_url and not ProductImage.objects.filter(product_id=product).exists():
                # Defer the actual network fetch - just queue it. See after_import().
                self._pending_image_downloads.append((product.pk, image_url))
        else:
            folder_path_string = row.get('images')
            if folder_path_string:
                self._attach_images_from_folder(product, folder_path_string)

    def _get_quantity_attribute(self):
        if self._quantity_attribute_cache is None:
            self._quantity_attribute_cache, _ = ProductAttribute.objects.get_or_create(
                code=QUANTITY_ATTRIBUTE_CODE,
                defaults={'name': 'Quantity', 'type': 'select', 'is_filterable': True, 'status': True},
            )
        return self._quantity_attribute_cache

    def _create_quantity_variant(self, product, quantity_value, price=None):
        attribute = self._get_quantity_attribute()
        variant_sku = f"{product.sku}-{slugify(quantity_value)}"[:200]

        ProductVariant.objects.update_or_create(
            product_id=product,
            attribute_id=attribute,
            attribute_name=quantity_value,
            defaults={
                'sku': variant_sku,
                'status': True,
                'sort_order': 0,
                'price': price or 0,
            },
        )

    def _attach_images_from_folder(self, product, folder_path_string):
        clean_folder_path = folder_path_string.strip().replace('\\', '/')

        if not (os.path.exists(clean_folder_path) and os.path.isdir(clean_folder_path)):
            logger.warning("Folder path not found or invalid: %s", clean_folder_path)
            return

        ProductImage.objects.filter(product_id=product).delete()

        for file_name in os.listdir(clean_folder_path):
            clean_path = os.path.join(clean_folder_path, file_name).replace('\\', '/')

            if os.path.isfile(clean_path):
                is_cover_image = 'cover' in file_name.lower()

                try:
                    with open(clean_path, 'rb') as local_file:
                        product_image = File(local_file, name=file_name)

                        ProductImage.objects.get_or_create(
                            product_id=product,
                            image=product_image,
                            defaults={
                                'is_base': is_cover_image,
                                'status': True
                            }
                        )
                except Exception as e:
                    logger.warning("Failed to open/save local image %s: %s", clean_path, e)

    def _run_pending_image_downloads(self):
        """Fetch all queued product images in parallel, once, after the row
        loop has finished. Each fetch is isolated in its own try/except so
        one bad host never blocks or breaks the rest of the batch."""
        tasks = self._pending_image_downloads
        self._pending_image_downloads = []

        logger.info("Fetching %d product images after import", len(tasks))

        with ThreadPoolExecutor(max_workers=IMAGE_FETCH_WORKERS) as executor:
            futures = {
                executor.submit(self._download_and_attach_image, product_id, image_url): (product_id, image_url)
                for product_id, image_url in tasks
            }
            for future in as_completed(futures):
                product_id, image_url = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.warning("Image fetch failed for product %s (%s): %s", product_id, image_url, e)

    def _download_and_attach_image(self, product_id, image_url):
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Referer': 'https://www.bigbasket.com/',
        }
        response = requests.get(image_url, timeout=IMAGE_FETCH_TIMEOUT, headers=headers)
        response.raise_for_status()

        file_name = image_url.split('/')[-1].split('?')[0] or f"{product_id}.jpg"

        # Re-fetch the product here rather than passing the instance across
        # threads - keeps each thread's DB usage self-contained.
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return

        # Guard against a race where two threads/rows targeted the same
        # product (shouldn't normally happen, but cheap to check).
        if ProductImage.objects.filter(product_id=product).exists():
            return

        product_image = ProductImage(product_id=product, is_base=True, status=True)
        product_image.image.save(file_name, ContentFile(response.content), save=True)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute_id':
            kwargs['queryset'] = ProductAttribute.objects.filter(status=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    inlines = [ProductImageInline, ProductVariantInline]
    resource_classes = [ProductResource]
    exclude = ('type',)
    list_display = ('name', 'sku', 'description', 'status', 'price', 'display_category', 'display_brand')
    search_fields = ('name', 'sku')
    list_filter = ('status',)

    @admin.display(description='Category')
    def display_category(self, obj):
        return obj.category_id.name

    @admin.display(description='Brand')
    def display_brand(self, obj):
        return obj.brand_id.name if obj.brand_id else '-'