import hashlib
import json

import razorpay
from django.conf import settings
from django.shortcuts import render,get_object_or_404,redirect
from google.api import billing_pb2

from cart.models import Cart
from cart_address.models import CartAddress
from cart_items.models import CartItem
from cart_payment.models import CartPayment
from order.models import Order
from order_address.models import OrderAddress
from order_items.models import OrderItem
from order_payment.models import OrderPayment

from products.models import Product
from django.http import JsonResponse,Http404
from django.db import models
import urllib.parse
from django.utils.crypto import get_random_string
from .forms import OrderCheckoutForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponse

def make_secure_hash(value):
    if not value:
        return ""
    # Convert string to lowercase, strip spaces, and encode to bytes
    clean_value = str(value).strip().lower()
    return hashlib.sha256(clean_value.encode('utf-8')).hexdigest()


def empty_cart(request):
    return render(request, 'cart/empty_cart.html')

def cartDetail(request):
    session_id = request.session.session_key
    if not session_id:
        return redirect('empty_cart')
    try:
        context = {}
        cart = Cart.objects.prefetch_related(models.Prefetch('cartitem_set',queryset=CartItem.objects.select_related('product_id'))).get(session_id=session_id,status=1)
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')
    context['cart'] = cart
    return render(request, 'cart/cart.html',context)

def checkout(request):
    session_id = request.session.session_key
    if not session_id:
        return redirect('empty_cart')
    try:
        context = {}
        cart = Cart.objects.prefetch_related(models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id'))).prefetch_related('cartaddress_set').get(session_id=session_id)
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')
    form = OrderCheckoutForm()
    amount = 100
    currency = 'INR'

    # Create the order on Razorpay's servers
    razorpay_order = razorpay_client.order.create(dict(
        amount=amount,
        currency=currency,
        receipt='order_rcptid_11',
        payment_capture='1'  # 1 means auto-capture payment immediately
    ))

    # Pass order details and public key to frontend template
    context = {
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'currency': currency,
    }
    context = {
        'cart': cart,
        'form' : form
    }
    return render(request, 'cart/checkout.html', context)

def saveAddress(request):


def addToCart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

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
        defaults={'row_total': 0.0, 'cart_total': 100.0,'shipping_method':'Flate rate','shipping_amount':100.0}
    )

    cart_item, item_created = CartItem.objects.get_or_create(
        cart_id=cart,
        product_id=product,
        category_id=product.category_id,
        defaults={
            'product_name': product.name,
            'qty': 0,
            'price': float(product.price),
            'total_price': 0.0
        }
    )
    if is_ajax:
        cart_item.qty = qty
    else:
        cart_item.qty += qty

    cart_item.total_price = float(cart_item.qty) * float(cart_item.price)
    cart_item.save()

    all_items = CartItem.objects.filter(cart_id=cart)
    cart.row_total = sum(float(item.total_price) for item in all_items)
    cart.cart_total = cart.row_total + 100
    cart.save()

    if is_ajax:
        # Return raw data back to your JavaScript background call
        return JsonResponse({
            'status': 'success',
            'item_total_price': cart_item.total_price,
            'cart_total': cart.cart_total,
            'row_total': cart.row_total,
            'current_qty': cart_item.qty
        })
    else:
        return redirect('cartDetail')


def deleteCartItem(request,item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_id = cart_item.cart_id.id
    cart_item.delete()


    cart = get_object_or_404(Cart, id=cart_id)
    cart.row_total = (cart.row_total or 0.0) - float(cart_item.total_price)
    cart.cart_total = (cart.cart_total or 0.0) - float(cart_item.total_price)
    cart.save()

    return redirect('cartDetail')


def placeOrder(request):
    session_id = request.session.session_key
    if not session_id:
        return redirect('empty_cart')
    try:
        cart = Cart.objects.prefetch_related(
            models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id'))).get(
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
        )

        order_items_to_create = []
        for cart_item in cart.cartitem_set.all():
            order_items_to_create.append(
                OrderItem(
                    order_id= order,
                    product_id=cart_item.product_id,
                    product_name = cart_item.product_name,
                    category_id = cart_item.category_id,
                    qty = cart_item.qty,
                    price = cart_item.price,
                    total_price = cart_item.total_price
                )
            )
        OrderItem.objects.bulk_create(order_items_to_create)

        orderPayment = OrderPayment.objects.create(
            order_id=order,
            order_number = order.order_number,
            payment_id = 'xyz',
            transaction_id = 'xyz',
            amount = order.order_total,
            status = 'Created'
        )

        orderBillingAddress = OrderAddress.objects.create(
            order_id=order,
            address_1=postData.get('billing_address_1'),
            address_2=postData.get('billing_address_2'),
            city=postData.get("billing_city"),
            state=postData.get('billing_state'),
            country=postData.get('billing_country'),
            zip_code=postData.get('billing_zip_code'),
            address_type='BILLING'
        )

        if isShipDiff:
            orderShippingAddress = OrderAddress.objects.create(
                order_id=order,
                address_1=postData.get('shipping_address_1'),
                address_2=postData.get('shipping_address_2'),
                city=postData.get("shipping_city"),
                state=postData.get('shipping_state'),
                country=postData.get('shipping_country'),
                zip_code=postData.get('shipping_zip_code'),
                address_type='SHIPPING'
            )
        else:
            orderShippingAddress = OrderAddress.objects.create(
                order_id=order,
                address_1=postData.get('billing_address_1'),
                address_2=postData.get('billing_address_2'),
                city=postData.get("billing_city"),
                state=postData.get('billing_state'),
                country=postData.get('billing_country'),
                zip_code=postData.get('billing_zip_code'),
                address_type='SHIPPING'
            )

        cart.status = 0
        cart.save()
        request.session.flush()
        context = {
            'order': order
        }
        return render(request, 'order/order_detail.html', context)
    else:
        context = {
            'cart': cart,
            'form': form
        }
        return render(request, 'cart/checkout.html', context)


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def initiate_payment(request):
    """Creates a Razorpay order and renders the payment checkout page."""
    # Razorpay expects amounts in currency subunits (e.g., Paise for INR).
    # ₹100.00 becomes 10000 Paise

    session_id = request.session.session_key
    if not session_id:
        return redirect('empty_cart')
    try:
        context = {}
        cart = Cart.objects.prefetch_related(
            models.Prefetch('cartitem_set', queryset=CartItem.objects.select_related('product_id'))).get(
            session_id=session_id, status=1)
    except Cart.DoesNotExist:
        return redirect('empty_cart')
    if not cart.cartitem_set.exists():
        return redirect('empty_cart')

    amount = cart.cart_total
    currency = 'INR'

    # Create the order on Razorpay's servers
    razorpay_order = razorpay_client.order.create(
        dict(amount=amount, currency=currency, payment_capture='0')
    )

    # Save order in database
    cartPayment = CartPayment.objects.create(
        cart_id = cart,
        razorpay_order_id=razorpay_order['id'],
        amount=amount,
        status='Created'
    )
    print(cartPayment.id,cartPayment.razorpay_order_id)
    # Pass order details and public key to frontend template
    context = {
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'currency': currency,
    }
    return render(request, 'cart/payment.html', context=context)


@csrf_exempt
def payment_callback(request):
    """Handles the post-payment signature verification from Razorpay."""
    if request.method == "POST":
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
            print(request.POST)
            print('razorpay_order_id',razorpay_order_id)

            # Verify the signature authenticity to prevent tampering
            razorpay_client.utility.verify_payment_signature(params_dict)

            payment = CartPayment.objects.get(razorpay_order_id=razorpay_order_id)

            razorpay_client.payment.capture(payment_id, payment.amount)

            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.status = 'Success'
            payment.save()

            # Perform database actions here (e.g., updating OrderStatus to 'Success')
            return HttpResponse("Payment Successful! Thank you.")

        except razorpay.errors.SignatureVerificationError:
            # Signature verification failed; fraud or bad request
            error_metadata = json.loads(request.POST.get('error[metadata]', '{}'))
            CartPayment.objects.filter(razorpay_order_id=error_metadata['order_id']).update(status='Failed')
            return HttpResponseBadRequest("Payment verification failed. Invalid signature.")
    else:
        return HttpResponseBadRequest("Invalid request method.")



