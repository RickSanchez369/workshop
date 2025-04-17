from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Invoice

# 📌 وقتی فاکتور جدید ذخیره میشه یا تغییر می‌کنه
@receiver(post_save, sender=Invoice)
def update_customer_financials_after_invoice_save(sender, instance, **kwargs):
    if instance.customer:
        instance.customer.recalculate_financials()

# 📌 وقتی فاکتور حذف میشه
@receiver(post_delete, sender=Invoice)
def update_customer_financials_after_invoice_delete(sender, instance, **kwargs):
    if instance.customer:
        instance.customer.recalculate_financials()

from .models import CustomerPayment, Invoice

# 📌 بعد از ثبت یا ویرایش پرداخت
@receiver(post_save, sender=CustomerPayment)
def update_after_payment_save(sender, instance, created, **kwargs):
    if instance.invoice:
        invoice = instance.invoice
        # بازمحاسبه بدهی فاکتور
        total_paid = sum(p.amount for p in CustomerPayment.objects.filter(invoice=invoice))
        invoice.remaining_debt = invoice.total_price - total_paid
        invoice.save()
        # بروزرسانی مالی مشتری
        if invoice.customer:
            invoice.customer.recalculate_financials()

# 📌 بعد از حذف پرداخت
@receiver(post_delete, sender=CustomerPayment)
def update_after_payment_delete(sender, instance, **kwargs):
    if instance.invoice:
        invoice = instance.invoice
        total_paid = sum(p.amount for p in CustomerPayment.objects.filter(invoice=invoice))
        invoice.remaining_debt = invoice.total_price - total_paid
        invoice.save()
        # بروزرسانی مالی مشتری
        if invoice.customer:
            invoice.customer.recalculate_financials()

from .models import InventoryTransaction, Stone

# 📌 بعد از ثبت یا ویرایش تراکنش انبار
@receiver(post_save, sender=InventoryTransaction)
def update_stone_stock_on_save(sender, instance, created, **kwargs):
    # اگر تراکنش جدید باشه، فقط مقدار جدید رو اعمال کن
    if created:
        if instance.type == 'buy':
            instance.stone.stock_box += instance.quantity_box
        elif instance.type == 'consume':
            instance.stone.stock_box -= instance.quantity_box
        instance.stone.save()
    else:
        # ویرایش تراکنش: باید اول مقدار قبلی رو حذف کنیم، بعد جدید رو اعمال کنیم
        try:
            old = InventoryTransaction.objects.get(pk=instance.pk)
            if old.type == 'buy':
                instance.stone.stock_box -= old.quantity_box
            elif old.type == 'consume':
                instance.stone.stock_box += old.quantity_box
        except InventoryTransaction.DoesNotExist:
            pass

        # حالا مقدار جدید رو اعمال کن
        if instance.type == 'buy':
            instance.stone.stock_box += instance.quantity_box
        elif instance.type == 'consume':
            instance.stone.stock_box -= instance.quantity_box
        instance.stone.save()

# 📌 بعد از حذف تراکنش انبار
@receiver(post_delete, sender=InventoryTransaction)
def update_stone_stock_on_delete(sender, instance, **kwargs):
    if instance.type == 'buy':
        instance.stone.stock_box -= instance.quantity_box
    elif instance.type == 'consume':
        instance.stone.stock_box += instance.quantity_box
    instance.stone.save()
