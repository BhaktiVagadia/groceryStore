from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from django.urls import reverse

from inventory.models import Inventory
from notify_customers.models import NotifyCustomers
from django.conf import settings
from cryptography.fernet import Fernet

from products.models import Product
from django.core.mail import send_mass_mail



def getPlainData(value):
    cipher = Fernet(settings.ENCRYPTION_KEY)
    decrypted_bytes = cipher.decrypt(value.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')

def send_restock_emails(product):
    customers = NotifyCustomers.objects.filter(product=product,is_notified=False)

    if not customers.exists():
        return

    product_url = f"{settings.SITE_URL}{reverse('product_detail', kwargs={'sku': product.sku})}"
    subject = f"Product Availability - {product.name}"

    message = (
        f"Dear Customer,\n\n"
        f"Great news! The item you've been waiting for is available again.\n"
        f"Item: {product.name}\n"
        f"Price: Rs. {product.selling_price}\n\n"
        f"Get yours before it sells out again by clicking the link below:\n"
        f"{product_url}\n\n"
        f"Best regards,\nYour Store Team"
    )

    from_email = settings.DEFAULT_FROM_EMAIL
    emails = []

    for customer in customers:
        raw_email = getattr(customer, 'email', None)
        if raw_email:
            recipient_list = [getPlainData(raw_email)]
            emails.append((subject, message, from_email, recipient_list))
    print(emails)
    if emails:
        send_mass_mail(emails, fail_silently=False)
        customers.update(is_notified=True)

@receiver(pre_save, sender=Product)
def track_availability_before_product_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = Product.objects.get(pk=instance.id)
            instance._was_available = old_instance.is_available
        except Product.DoesNotExist:
            instance._was_available = False
    else:
        instance._was_available = False

@receiver(post_save, sender=Product)
def  track_availability_after_product_save(sender, instance, created, **kwargs):
    was_available = getattr(instance, '_was_available', False)
    print(was_available,instance.is_available)
    if instance.is_available and not was_available:
        send_restock_emails(instance)

@receiver(pre_save, sender=Inventory)
def  track_availability_before_inventory_save(sender, instance, **kwargs):
    if instance.id:
        try:
            product = instance.product
            instance._was_available = product.is_available
        except product.DoesNotExist:
            instance._was_available = False
    else:
        instance._was_available = False

@receiver(post_save, sender=Inventory)
def track_availability_after_inventory_save(sender, instance, created, **kwargs):
    was_available = getattr(instance, '_was_available', False)
    product = instance.product
    if product.is_available and not was_available:
        send_restock_emails(product)




