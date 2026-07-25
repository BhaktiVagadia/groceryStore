from django.shortcuts import render,get_object_or_404,redirect

from categories.models import Category
from notify_customers.models import NotifyCustomers
from products.models import Product
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from cryptography.fernet import Fernet
from django.conf import settings

# NOTE: adjust this import to match the actual app label the ProductVariant model lives in
from product_variants.models import ProductVariant



def list(request):
    all_products_count = Product.objects.filter(status=1).count()

    products = Product.objects.select_related('category_id').prefetch_related(
        Prefetch(
            'productvariant_set',
            queryset=ProductVariant.objects.filter(status=True).order_by('sort_order'),
            to_attr='active_variants'
        )
    ).all()
    products = products.filter(status=1)

    query_keyword = request.GET.get('keywords')
    if query_keyword:
        products = products.filter(
            Q(name__icontains=query_keyword) |
            Q(sku__icontains=query_keyword) |
            Q(category_id__name__icontains=query_keyword)
        )

    category_sku = request.GET.get('category_sku')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort')
    if category_sku and category_sku!='all_category':
        products = products.filter(
            Q(category_id__sku=category_sku) |
            Q(category_id__parent_id__sku=category_sku)
        )
    if max_price:
        products = products.filter(price__lte=max_price)
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-id')


    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    context = {'products': products,'all_products_count':all_products_count}
    return render(request, 'products/products.html',context)


def productDetail(request, sku):
    product = get_object_or_404(
        Product.objects.select_related('category_id').prefetch_related(Prefetch(
            'productvariant_set',
            queryset=ProductVariant.objects.filter(status=True).order_by('sort_order'),
            to_attr='active_variants'
        )),
        sku=sku
    )
    context = {
        'product': product
    }

    return render(request, 'products/product_detail.html', context)

def notifyMe(request,product_id):
    clean_value = str(request.POST.get('email')).strip().lower()
    cipher = Fernet(settings.ENCRYPTION_KEY)
    encrypted_bytes = cipher.encrypt(clean_value.encode('utf-8'))
    hashemail = encrypted_bytes.decode('utf-8')
    notifyCustomer = NotifyCustomers.objects.create(
        product = Product.objects.get(id=product_id),
        email = hashemail
    )
    return redirect('products')