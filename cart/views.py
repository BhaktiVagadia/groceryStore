import hashlib
import json

import razorpay
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render,get_object_or_404,redirect
from django.utils import timezone
from google.api import billing_pb2

import cart_payment
import inventory
from cart.models import Cart
from cart_address.models import CartAddress
from cart_items.models import CartItem
from cart_payment.models import CartPayment
from coupon.models import Coupon
from inventory.models import Inventory
from order.models import Order
from order_address.models import OrderAddress
from order_items.models import OrderItem
from order_payment.models import OrderPayment

from products.models import Product
from product_variants.models import ProductVariant
from django.http import JsonResponse,Http404
from django.db import models
from .forms import OrderCheckoutForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponse
from cryptography.fernet import Fernet

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def make_secure_hash(value):
    if not value:
        return ""

    # Convert string to lowercase, strip spaces, and encode to bytes
    clean_value = str(value).strip().lower()
    cipher = Fernet(settings.ENCRYPTION_KEY)
    encrypted_bytes = cipher.encrypt(clean_value.encode('utf-8'))
    return  encrypted_bytes.decode('utf-8')


def empty_cart(request):
    return render(request, 'cart/empty_cart.html')

def cartDetail(request):
    session_id = request.session.session_key
    if not session_id:
        return redirect('empty_cart')
    try:
        context = {}
        cart = Cart.objects.prefetch_related(models.Prefetch('cartitem_set',queryset=CartItem.objects.select_related('product_id', 'variant_id'))).get(session_id=session_id,status=1)
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')
    available_coupons = Coupon.get_available_coupons()
    context['cart'] = cart
    context['available_coupons'] = available_coupons
    return render(request, 'cart/cart.html',context)

def checkout(request):
    # request.session.flush()
    session_id = request.session.session_key
    if not session_id:
        return redirect('empty_cart')
    try:
        cart = Cart.objects.prefetch_related(models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id', 'variant_id'))).prefetch_related('cartaddress_set').get(session_id=session_id,status=1)
        out_of_stock = []
        for cart_item in cart.cartitem_set.all():
            inventory_filter = {'product_id': cart_item.product_id}
            if cart_item.variant_id:
                # NOTE: adjust 'variant_id' below if your Inventory model's FK field is named differently
                inventory_filter['variant_id'] = cart_item.variant_id
            inventory = Inventory.objects.filter(**inventory_filter).first()

            if not inventory or not inventory.product.is_available or inventory.available_qty < cart_item.qty:
                out_of_stock.append(cart_item.product_name)
        if out_of_stock:
                form = OrderCheckoutForm()
                unavailable_products = ",".join(out_of_stock)
                context = {'cart': cart,
                    'form': form,
                    'error': f"Sorry, '{unavailable_products}' is/are currently out of stock(s) or unavailable."
                }
                return render(request, 'cart/checkout.html', context)
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')

    form = OrderCheckoutForm()

    cart_total = cart.cart_total
    razorpay_amount = int(cart_total * 100)
    currency = 'INR'

    cartPayment = CartPayment.objects.filter(cart_id=cart, status='Created').first()

    if cartPayment:
        razorpay_order_id = cartPayment.razorpay_order_id
    else:
        try:
            razorpay_order = razorpay_client.order.create(dict(
                amount=razorpay_amount,
                currency=currency,
                receipt=f"receipt_cart_{cart.id}",
                payment_capture='0'
            ))
            razorpay_order_id = razorpay_order['id']

            # Save the record into your database
            CartPayment.objects.create(
                cart_id=cart,
                razorpay_order_id=razorpay_order_id,
                amount=cart.cart_total,
                status='Created'
            )
        except Exception as e:
            return render(request, 'cart/checkout.html',
                          {'error': 'Payment Gateway unavailable. Please try again later.'})
    context = {
        'cart': cart,
        'form' : form,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': razorpay_amount,  # Passed in paise for checkout.js
        'currency': currency,
    }
    return render(request, 'cart/checkout.html', context)

def saveAddress(request):
    session_id = request.session.session_key
    try:
        cart = Cart.objects.prefetch_related(
            models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id', 'variant_id'))).get(
            session_id=session_id,status=1)
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')

    form = OrderCheckoutForm(request.POST)
    if form.is_valid():
        postData = form.cleaned_data

        cart.customer_name = make_secure_hash(postData.get('customer_name'))
        cart.customer_email = make_secure_hash(postData.get('email'))
        cart.customer_mo_no = postData.get('mo_no')
        cart.save()

        isShipDiff = postData.get('is_ship_diff')

        cartBillingAddress =  CartAddress.objects.create(
            cart_id = cart,
            address_1 = postData.get('billing_address_1'),
            address_2 =  postData.get('billing_address_2'),
            city =  postData.get("billing_city"),
            state = postData.get('billing_state'),
            country =  postData.get('billing_country'),
            zip_code =  postData.get('billing_zip_code'),
            address_type = 'BILLING'
        )

        if isShipDiff:
            cartShippingAddress = CartAddress.objects.create(
                cart_id=cart,
                address_1=postData.get('shipping_address_1'),
                address_2=postData.get('shipping_address_2'),
                city=postData.get("shipping_city"),
                state=postData.get('shipping_state'),
                country=postData.get('shipping_country'),
                zip_code=postData.get('shipping_zip_code'),
                address_type='SHIPPING'
            )
        else:
            cartShippingAddress = CartAddress.objects.create(
                cart_id=cart,
                address_1=postData.get('billing_address_1'),
                address_2=postData.get('billing_address_2'),
                city=postData.get("billing_city"),
                state=postData.get('billing_state'),
                country=postData.get('billing_country'),
                zip_code=postData.get('billing_zip_code'),
                address_type='SHIPPING'
            )
        return redirect('checkout')
    else:
        context = {
            'cart': cart,
            'form': form
        }
        return render(request, 'cart/checkout.html', context)


def addToCart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    variant_id_input = request.POST.get('variant_id') or request.GET.get('variant_id')
    variant = None
    if variant_id_input:
        # 404s if someone tampers with the variant id or picks one from a different product
        variant = get_object_or_404(ProductVariant, id=variant_id_input, product_id=product, status=True)

    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key

    qty_input = request.POST.get('quantity') or request.GET.get('quantity') or '1'
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        qty = int(qty_input)
        if qty < 1:
            qty = 1
    except ValueError:
        qty = 1

    cart, created = Cart.objects.get_or_create(
        session_id=session_id,status=1,
        defaults={'row_total': 0.0, 'cart_total': 100.0,'shipping_method':'Flate rate','shipping_amount':99.00}
    )

    item_price = float(variant.price) if variant else float(product.price)

    # variant_id is part of the lookup so each variant of a product gets its own line item
    cart_item, item_created = CartItem.objects.get_or_create(
        cart_id=cart,
        product_id=product,
        variant_id=variant,
        category_id=product.category_id,
        defaults={
            'product_name': product.name,
            'qty': 0,
            'price': item_price,
            'total_price': 0.0
        }
    )
    old_qty = cart_item.qty
    if is_ajax:
        cart_item.qty = qty
    else:
        cart_item.qty += qty

    cart_item.total_price = float(cart_item.qty) * float(cart_item.price)
    cart_item.save()
    discount_amount = cart.discount_amount if cart.discount_amount else 0

    all_items = CartItem.objects.filter(cart_id=cart)
    cart.row_total = sum(float(item.total_price) for item in all_items)
    cart.discount_amount = discount_amount
    cart.tax_amount = (cart.row_total + cart.shipping_amount - discount_amount) * 0.18
    cart.cart_total = cart.row_total + cart.shipping_amount + cart.tax_amount - discount_amount
    cart.save()

    if is_ajax:
        # Return raw data back to your JavaScript background call
        return JsonResponse({
            'status': 'success',
            'item_total_price': cart_item.total_price,
            'cart_total': cart.cart_total,
            'row_total': cart.row_total,
            'tax_amount': cart.tax_amount,
            'discount_amount': cart.discount_amount,
            'shipping_amount': cart.shipping_amount,
            'current_qty': cart_item.qty
        })
    else:
        return redirect('cartDetail')


def deleteCartItem(request,item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_id = cart_item.cart_id.id
    cart_item.delete()


    cart = get_object_or_404(Cart, id=cart_id)
    discount_amount = cart.discount_amount if cart.discount_amount else 0
    cart.row_total = (cart.row_total or 0.0) - float(cart_item.total_price)
    cart.tax_amount = (cart.row_total + cart.shipping_amount - discount_amount) * 0.18
    cart.cart_total = cart.row_total + cart.shipping_amount + cart.tax_amount - discount_amount
    cart.save()

    return redirect('cartDetail')

@csrf_exempt
def placeOrder(request):
    session_id = request.session.session_key if request.session.session_key else request.GET.get('session_id')

    if not session_id:
        return redirect('empty_cart')
    try:
        cart = (Cart.objects.prefetch_related(
            models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id', 'variant_id'))).
            prefetch_related('cartaddress_set').
            prefetch_related('cartpayment_set').
            get(session_id=session_id,status=1))
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')

    if request.method == "POST":
        payment_type = 1
        try:
            # Extract attributes from Razorpay POST request payload
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # Verify the signature authenticity to prevent tampering
            razorpay_client.utility.verify_payment_signature(params_dict)

            payment = CartPayment.objects.get(razorpay_order_id=razorpay_order_id)

            razorpay_client.payment.capture(payment_id, payment.amount * 100)

            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.status = 'Success'
            payment.save()

        except razorpay.errors.SignatureVerificationError:
            # Signature verification failed; fraud or bad request
            error_metadata = json.loads(request.POST.get('error[metadata]', '{}'))
            CartPayment.objects.filter(razorpay_order_id=error_metadata['order_id']).update(status='Failed')
            return redirect('checkout');
    else:
        payment_type = 0
        payment = CartPayment.objects.get(cart_id=cart)
        payment.delete()

    order = Order.objects.create(
        cart_id= cart,
        row_total = cart.row_total,
        order_total = cart.cart_total,
        discount_rate = cart.discount_rate,
        discount_amount = cart.discount_amount,
        shipping_amount = cart.shipping_amount,
        shipping_method = cart.shipping_method,
        order_number = 'INV-'+str(cart.id),
        status = 1,
        customer_name= cart.customer_name,
        customer_email = cart.customer_email,
        customer_mo_no = cart.customer_mo_no,
        payment_type=payment_type,
        tax_amount=cart.tax_amount,
    )
    now = timezone.now()
    if cart.coupon_id:
        coupon = Coupon.objects.get(
            id = cart.coupon_id.id,
            valid_from__lte=now,
            valid_to__gte=now,
            status=1
        )
        if coupon and coupon.min_total <= order.row_total:
            order.coupon_id = cart.coupon_id
            order.coupon_code = coupon.coupon_code
            order.discount_amount = cart.discount_amount
            order.discount_rate = cart.discount_rate
            order.save()


    order_items = []
    for cart_item in cart.cartitem_set.all():
        order_items.append(
            OrderItem(
                order_id= order,
                product_id=cart_item.product_id,
                # NOTE: requires a variant_id FK field on OrderItem mirroring CartItem
                variant_id=cart_item.variant_id,
                product_name = cart_item.product_name,
                category_id = cart_item.category_id,
                qty = cart_item.qty,
                price = cart_item.price,
                total_price = cart_item.total_price
            )
        )

        inventory_filter = {'product_id': cart_item.product_id}
        if cart_item.variant_id:
            inventory_filter['variant_id'] = cart_item.variant_id
        inventory = Inventory.objects.select_for_update().filter(**inventory_filter).first()

        if inventory:
            inventory.reserved_qty += cart_item.qty
            inventory.available_qty -= cart_item.qty
            inventory.save()
    OrderItem.objects.bulk_create(order_items)

    order_address = []
    for address in cart.cartaddress_set.all():
        order_address.append(
            OrderAddress(
                order_id=order,
                address_1=address.address_1,
                address_2 = address.address_2,
                city = address.city,
                state = address.state,
                country = address.country,
                zip_code = address.zip_code,
                address_type = address.address_type
            )
        )
    OrderAddress.objects.bulk_create(order_address)

    order_payment = []
    for cartPayment in cart.cartpayment_set.all().iterator():
        order_payment.append(
            OrderPayment(
                order_id=order,
                order_number = order.order_number,
                razorpay_order_id = cartPayment.razorpay_order_id,
                razorpay_payment_id = cartPayment.razorpay_payment_id,
                razorpay_signature = cartPayment.razorpay_signature,
                amount =cartPayment.amount,
                status = 'Created'
            )
        )
    OrderPayment.objects.bulk_create(order_payment)

    cart.status = 0
    cart.save()
    if order.payment_type == 1:
        order.status = 2
        order.save()
    request.session.flush()
    request.session['session_order_id'] = order.id
    return redirect('track_order')


def apply_cart_coupon(request):

    session_id = request.session.session_key if request.session.session_key else request.GET.get('session_id')

    if not session_id:
        return redirect('empty_cart')
    try:
        cart = (Cart.objects.prefetch_related(
            models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id', 'variant_id'))).
                prefetch_related('cartaddress_set').
                prefetch_related('cartpayment_set').
                get(session_id=session_id, status=1))
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')

    row_total = cart.row_total
    now = timezone.now()
    coupon_code = request.POST.get('coupon_code', '').strip()

    try:
        coupon = Coupon.objects.get(
            coupon_code__iexact=coupon_code,
            valid_from__lte=now,
            valid_to__gte=now,
            status=1
        )

        if row_total <= coupon.min_total:
            messages.error(request, f"Coupon '{coupon_code}' requires a minimum subtotal of Rs. {coupon.min_total}.")
            request.session['coupon_id'] = None
        else:
            cart.coupon_code = coupon_code
            cart.coupon_id = coupon
            cart.save()
            messages.success(request, f"Coupon '{coupon_code}' applied successfully!")

    except Coupon.DoesNotExist:
        request.session['coupon_id'] = None
        messages.error(request, "This coupon code is invalid or has expired.")

    return redirect('cartDetail')