from categories.models import Category
from products.models import Product
from cart.models import Cart
from django.db.models import Subquery, OuterRef, Sum, Count, Q, OuterRef
from django.db.models.functions import Concat,Coalesce
from django.db.models import Value

def global_site_data(request):
    # categories = Category.objects.annotate(total_products=Count('product', filter=Q(product__status=True)))

    categories = Category.objects.annotate(
        total_products=Count('products', distinct=True) + Count('subcategories__products', distinct=True)
    ).order_by('path')

    session_id = request.session.session_key
    context = { 'categories': categories}
    if session_id:
        cart = Cart.objects.filter(session_id=session_id, status=1).first()
        context['cart'] = cart

    return context
