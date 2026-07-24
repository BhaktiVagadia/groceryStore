import hashlib

from django.shortcuts import render, redirect,get_object_or_404

from order_payment.models import OrderPayment
from .forms import TrackOrderForm
from .models import Order
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib import messages
import razorpay


def track_order(request):
    order = None
    error_message = None

    session_order_id = request.session.pop('session_order_id', None)
    # session_order_id = request.session.get('session_order_id', None)

    if session_order_id:
        order = Order.objects.filter(id=session_order_id).first()
        if order:
            return render(request, 'order/order_detail.html', {'order': order})
    if request.method == 'POST':
        form = TrackOrderForm(request.POST)
        if form.is_valid():
            order_num = form.cleaned_data['order_number'].strip()
            email = str(form.cleaned_data['email']).strip().lower()

            order = Order.objects.filter(order_number=order_num).first()
            if order:
                cipher = Fernet(settings.ENCRYPTION_KEY)
                decrypted_bytes = cipher.decrypt(order.customer_email.encode('utf-8'))
                dbemail = decrypted_bytes.decode('utf-8')

            if not order or dbemail !=email:
                error_message = "No order found with those details. Please check and try again."
            else:
                request.session['session_order_id'] = order.id
                return redirect('track_order')
    else:
        form = TrackOrderForm()

    context = {
        'form': form,
        'order': order,
        'error_message': error_message
    }
    return render(request, 'order/track_order.html', context)

def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    reason = request.POST.get('cancellation_reason', '').strip()

    payment = OrderPayment.objects.filter(order_id=order).first()
    if order.payment_type and payment.razorpay_payment_id:
        try:

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            refund_payload = {
                "amount": int(order.order_total * 100),
                "speed": "optimum",  # Optimum speed processes refunds instantly if eligible
                "notes": {
                    "reason": reason,
                    "order_number": order.order_number
                }
            }

            razorpay_refund = client.payment.refund(payment.razorpay_payment_id, refund_payload)

            payment.refund_id = razorpay_refund['id']
            payment.save()

            order.status = 6
            order.cancellation_reason = reason
            order.save()

            messages.success(request,f"Order cancelled. Refund of Rs.{order.order_total} initiated successfully via Razorpay.")

        except Exception  as e:
            messages.error(request, f"Razorpay refund automation failed: {str(e)}")
    else:
        order.status = 6
        order.cancellation_reason = reason
        order.save()
        messages.success(request, "Your order has been cancelled successfully.")

    request.session['session_order_id'] = order.id
    return redirect('track_order')