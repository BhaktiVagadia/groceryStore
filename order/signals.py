from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F

from order.models import Order
from inventory.models import Inventory
from order_items.models import OrderItem
from django.conf import settings
from cryptography.fernet import Fernet

def getPlainData(value):
    cipher = Fernet(settings.ENCRYPTION_KEY)
    decrypted_bytes = cipher.decrypt(value.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')

@receiver(pre_save, sender=Order)
def track_order_status_before_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_order = Order.objects.get(pk=instance.id)
            instance._old_status = old_order.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def process_order_status_change(sender, instance, created, **kwargs):
    if created:  # Ensures it only runs when a new order is created
        subject = f"Order Confirmation - #{instance.order_number}"

        message = (
            f"Hi {getPlainData(instance.customer_name)},\n\n"
            f"Thank you for your order! We have received it and are processing it.\n\n"
            f"Order Number: {instance.order_number}\n"
            f"Total Amount: ${instance.order_total}\n\n"
            f"We will notify you once your order ships."
        )

        email = getPlainData(instance.customer_email)

        try:
            sent_count = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,  # Set to True in prod if you don't want email failures to crash the app
            )
            if sent_count == 1:
                print(f"SUCCESS: Email successfully sent to {email} for Order {instance.id}")
            else:
                print(f"FAILED: Email was not accepted by the mail server for Order {instance.id}")
        except Exception as e:
            print(f"Error sending email for order {instance.id}: {e}")

    old_status = getattr(instance, '_old_status', None)
    current_status = instance.status
    print(old_status)
    print(current_status)

    # If status hasn't changed, do absolutely nothing
    if old_status == current_status:
        return

    # when shipped change qty
    with transaction.atomic():
        if current_status == 4:
            order_items = OrderItem.objects.filter(order_id=instance)

            for item in order_items:
                Inventory.objects.select_for_update().filter(
                    product_id=item.product_id
                ).update(
                    qty=F('qty') - item.qty,
                    reserved_qty=F('reserved_qty') - item.qty
                )
            subject = f"Your Order #{instance.order_number} Has Been Dispatched! 🚀"

            # Fallback checking if fields are left blank by the administrator
            tracking_no = getattr(instance, 'tracking_number', None) or 'N/A'
            tracking_link = getattr(instance, 'tracking_link',
                                    None) or f"{settings.SITE_URL}/order/track_order"

            # Resolve the nested address reference cleanly
            address_instance = instance.orderaddress_set.filter(address_type="SHIPPING").first()
            if address_instance:
                shipping_address = f"{address_instance.address_1}, {address_instance.city}, {address_instance.state} - {address_instance.zip_code}"
            else:
                shipping_address = "Provided at checkout parameters"

            message = (
                f"Dear {getPlainData(instance.customer_name)},\n\n"
                f"Great news! Your order #{instance.order_number} has been processed, packed, and has officially "
                f"left our main hub.\n\n"
                f"Live Tracking Details:\n"
                f"* Tracking Number: {tracking_no}\n"
                f"* Track Your Progress: {tracking_link}\n\n"
                f"Order Summary:\n"
                f"* Total Amount Paid: Rs. {instance.order_total}\n"
                f"* Fulfillment Method: {instance.shipping_method}\n\n"
                f"Delivery Address:\n"
                f"{shipping_address}\n\n"
                f"You can click the tracking link above at any time to monitor the progress of your delivery route.\n\n"
                f"If you have any questions, simply reply directly to this email.\n\n"
                f"Thank you for shopping with us!\n\n"
                f"Best regards,\n"
                f"The Fulfillment Team\n"
                f"{settings.SITE_URL}"
            )
            email = getPlainData(instance.customer_email)

            try:
                sent_count = send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,  # Set to True in prod if you don't want email failures to crash the app
                )
                if sent_count == 1:
                    print(f"SUCCESS: Email successfully sent to {email} for Order {instance.id}")
                else:
                    print(f"FAILED: Email was not accepted by the mail server for Order {instance.id}")
            except Exception as e:
                print(f"Error sending email for order {instance.id}: {e}")

        elif current_status == 6:
            order_items = OrderItem.objects.filter(order_id=instance)

            for item in order_items:
                Inventory.objects.select_for_update().filter(
                    product_id=item.product_id
                ).update(
                    reserved_qty=F('reserved_qty') - item.qty,
                    available_qty=F('available_qty') + item.qty
                )
            subject = f"Order Cancelled - #{instance.order_number}"
            payment_record = instance.orderpayment_set.first()
            if payment_record and getattr(payment_record, 'refund_id', None):
                refund_details_block = (
                    f"Refund Details:\n"
                    f"* Total Refund Amount: Rs. {instance.order_total}\n"
                    f"* Payment Method: Online Payment (Razorpay)\n"
                    f"* Refund Reference ID: {getattr(payment_record, 'refund_id')}\n\n"
                    f"The refund has been initiated automatically through Razorpay. Please quote the Refund Reference ID "
                    f"above if you need to follow up with your bank. The amount will be credited back "
                    f"to your original payment method within 5-7 business days.\n\n"
                )
            else:
                refund_details_block = (
                    f"Refund Details:\n"
                    f"* Total Cancelled Amount: Rs. {instance.order_total}\n\n"
                    f"If you have already paid for this order through an alternative method, "
                    f"our support team will reach out to you shortly to process your reversal.\n\n"
                )
            subject = f"Order Cancelled - #{instance.order_number}"
            message = (
                f"Dear {getPlainData(instance.customer_name)},\n\n"
                f"This email confirms that your order #{instance.order_number} has been cancelled.\n\n"
                f"If this cancellation was unintended, or if you would like to look for alternative items, "
                f"you can head back to our store at any time: {settings.SITE_URL}\n\n"
                f"{refund_details_block}"  # Injects the custom dynamic block here
                f"If you have any questions, simply reply directly to this email.\n\n"
                f"Best regards,\n"
                f"The Customer Support Team\n"
                f"{settings.SITE_URL}"
            )

            email = getPlainData(instance.customer_email)

            try:
                sent_count = send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,  # Set to True in prod if you don't want email failures to crash the app
                )
                if sent_count == 1:
                    print(f"SUCCESS: Email successfully sent to {email} for Order {instance.id}")
                else:
                    print(f"FAILED: Email was not accepted by the mail server for Order {instance.id}")
            except Exception as e:
                print(f"Error sending email for order {instance.id}: {e}")

        elif current_status == 5:
            subject = f"Order Delivered - #{instance.order_number}"
            message = (
                f"Dear {getPlainData(instance.customer_name)},\n\n"
                f"This email confirms that your order #{instance.order_number} has been Delivered.\n\n"
                f"If you have any questions, simply reply directly to this email.\n\n"
                f"Best regards,\n"
                f"The Customer Support Team\n"
                f"{settings.SITE_URL}"
            )

            email = getPlainData(instance.customer_email)

            try:
                sent_count = send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,  # Set to True in prod if you don't want email failures to crash the app
                )
                if sent_count == 1:
                    print(f"SUCCESS: Email successfully sent to {email} for Order {instance.id}")
                else:
                    print(f"FAILED: Email was not accepted by the mail server for Order {instance.id}")
            except Exception as e:
                print(f"Error sending email for order {instance.id}: {e}")
