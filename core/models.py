from django.db import models
from django.contrib.auth.models import User
import django_jalali.db.models as jmodels  # ✅ اضافه کن اگر هنوز نذاشتی
from django.core.exceptions import ValidationError
from core.models import Invoice, Expense, InventoryTransaction
from django.db.models import Sum
from decimal import Decimal  # بالای فایل




# Create your models here.


# ----------------------------
# 1. مدل مشتری (Customers)
# ----------------------------
class Customer(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام مشتری")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    total_debt = models.IntegerField(default=0)      # مجموع بدهی فعال
    total_paid = models.IntegerField(default=0)      # مجموع پرداختی کل


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتری‌ها"
        ordering = ['name']

    def recalculate_financials(self):
        from core.models import Invoice, CustomerPayment

        # جمع کل بدهی فاکتورها
        invoices = Invoice.objects.filter(customer=self)
        self.total_debt = sum(i.remaining_debt for i in invoices)

        # جمع کل پرداختی‌ها
        payments = CustomerPayment.objects.filter(invoice__customer=self)
        self.total_paid = sum(p.amount for p in payments)

        self.save()

# ----------------------------
# 2. مدل طرح (Designs)
# ----------------------------
class Design(models.Model):
    title = models.CharField(max_length=100, verbose_name="نام طرح")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "طرح"
        verbose_name_plural = "طرح‌ها"
        ordering = ['title']
        
    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if self.invoice_set.exists():
            raise ValidationError("❌ این طرح در فاکتورهای فروش استفاده شده و قابل حذف نیست.")
        super().delete(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.price <= 0:
            raise ValidationError("❌ قیمت طرح باید بیشتر از صفر باشد.")

    def save(self, *args, **kwargs):
        if self.pk and self.invoice_set.exists():
            raise ValueError("❌ نمی‌توان طرحی که در فاکتور استفاده شده را ویرایش کرد.")
        super().save(*args, **kwargs)


# ----------------------------
# 3. مدل سنگ (Stones)
# ----------------------------
class Stone(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام سنگ")
    price_per_box_usd = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قیمت هر کارتن (دلار)")
    stock_box = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="موجودی (کارتن)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "سنگ"
        verbose_name_plural = "سنگ‌ها"
        ordering = ['name']
    
    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if self.inventorytransaction_set.exists():
            raise ValidationError("❌ این سنگ دارای تراکنش‌های ثبت‌شده است و نمی‌توان آن را حذف کرد.")
        super().delete(*args, **kwargs)
        

# ----------------------------
# 4. مدل تراکنش انبار (Inventory Transactions)
# ----------------------------
class InventoryTransaction(models.Model):
    TRANSACTION_TYPE = (
        ('buy', 'خرید'),
        ('consume', 'مصرف'),
    )

    stone = models.ForeignKey(Stone, on_delete=models.CASCADE, verbose_name="نوع سنگ")
    date = jmodels.jDateField(verbose_name="تاریخ تراکنش")  # <-- تاریخ شمسی
    quantity_box = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="مقدار (کارتن)")
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE, verbose_name="نوع تراکنش")

    def __str__(self):
        return f"{self.get_type_display()} - {self.stone.name} - {self.quantity_box}box"

    class Meta:
        verbose_name = "تراکنش انبار"
        verbose_name_plural = "تراکنش‌های انبار"
        ordering = ['-date']
        
    
    def save(self, *args, **kwargs):
        # آیا تراکنش جدید است یا ویرایش؟
        is_new = self._state.adding
        old_quantity = None
        old_type = None
        old_stone_id = None

        if not is_new:
            try:
                old = InventoryTransaction.objects.get(pk=self.pk)
                old_quantity = old.quantity_box
                old_type = old.type
                old_stone_id = old.stone_id
            except InventoryTransaction.DoesNotExist:
                pass  # برای اطمینان بیشتر

        super().save(*args, **kwargs)

        # اگر تراکنش جدید بود
        if is_new:
            if self.type == 'buy':
                self.stone.stock_box += self.quantity_box
            elif self.type == 'consume':
                self.stone.stock_box -= self.quantity_box
        else:
            # اول اثر تراکنش قبلی رو خنثی کن
            if old_type == 'buy':
                Stone.objects.filter(pk=old_stone_id).update(stock_box=F('stock_box') - old_quantity)
            elif old_type == 'consume':
                Stone.objects.filter(pk=old_stone_id).update(stock_box=F('stock_box') + old_quantity)

            # حالا اثر جدید رو اعمال کن
            if self.type == 'buy':
                self.stone.stock_box += self.quantity_box
            elif self.type == 'consume':
                self.stone.stock_box -= self.quantity_box

        self.stone.save()

    def delete(self, *args, **kwargs):
        # قبل از حذف، موجودی را اصلاح کن
        if self.type == 'buy':
            self.stone.stock_box -= self.quantity_box
        elif self.type == 'consume':
            self.stone.stock_box += self.quantity_box

        self.stone.save()
        super().delete(*args, **kwargs)
    

# ----------------------------
# 5. مدل فاکتور فروش (Invoices)
# ----------------------------
class Invoice(models.Model):
    PAYMENT_TYPE = (
        ('cash', 'نقدی'),
        ('check', 'چک'),
    )

    date = jmodels.jDateField(verbose_name="تاریخ فاکتور")  # <-- تاریخ شمسی
    invoice_number = models.CharField(max_length=20, unique=True, verbose_name="شماره فاکتور")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="مشتری")
    design = models.ForeignKey(Design, on_delete=models.CASCADE, verbose_name="طرح")
    stone = models.ForeignKey(Stone, on_delete=models.CASCADE, verbose_name="نوع سنگ")
    
    design_price_per_piece = models.PositiveIntegerField(verbose_name="قیمت هر قواره")
    quantity = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="تعداد قواره")
    discount = models.PositiveIntegerField(default=0, verbose_name="تخفیف")
    total_price = models.PositiveIntegerField(verbose_name="جمع کل (محاسبه‌شده)")

    issuer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="صادرکننده")
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE, verbose_name="نوع پرداخت")
    check_due_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ چک (در صورت وجود)")  # <-- تاریخ شمسی
    note = models.CharField(max_length=100, blank=True, null=True, verbose_name="توضیح چک")

    amount_paid = models.PositiveIntegerField(verbose_name="مبلغ پرداخت‌شده")
    remaining_debt = models.PositiveIntegerField(verbose_name="بدهی باقی‌مانده")

    def __str__(self):
        return f"فاکتور {self.invoice_number}"

    class Meta:
        verbose_name = "فاکتور فروش"
        verbose_name_plural = "فاکتورهای فروش"
        ordering = ['-date']
        
        
    def save(self, *args, **kwargs):
        # محاسبه مبلغ کل فاکتور بر اساس طرح‌ها و قیمت‌ها
        if not self.total_price or self.total_price == 0:
            try:
                # اگر طرح انتخاب شده، قیمتش × تعداد
                self.total_price = self.quantity * self.design.price
            except:
                self.total_price = 0

        # محاسبه باقی‌مانده بدهی
        if self.amount_paid is None:
            self.amount_paid = 0
        self.remaining_debt = self.total_price - self.amount_paid

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # ✅ کم کردن بدهی از مشتری (در آینده دقیق‌تر می‌شه)
        if self.customer and self.remaining_debt:
            try:
                # فرض بر اینه که بدهی مشتری در جای دیگری ذخیره یا جمع زده می‌شه
                pass  # اینجا می‌تونیم بدهی مشتری را در مدل Customer کاهش بدیم در صورت نیاز
            except:
                pass

        # ✅ کم کردن فروش ثبت‌شده کاربر در آمار (در گزارش‌های مالی یا user_report محاسبه می‌شه)
        if self.issuer:
            try:
                # در حال حاضر لازم نیست چیزی کم کنیم چون فروش از مجموع فاکتورهای کاربر حساب می‌شه
                pass
            except:
                pass

        # ✅ حذف فاکتور واقعی
        super().delete(*args, **kwargs)


# ----------------------------
# 6. مدل هزینه‌ها (Expenses)
# ----------------------------
class Expense(models.Model):

    date = jmodels.jDateField(verbose_name="تاریخ هزینه")  # <-- تاریخ شمسی
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ثبت‌کننده")
    amount = models.PositiveIntegerField(verbose_name="مبلغ (تومان)")
    note = models.TextField(blank=True, null=True, verbose_name="توضیح اضافی")

    def __str__(self):
        return f"{self.user} - {self.amount} تومان"

    class Meta:
        verbose_name = "هزینه"
        verbose_name_plural = "هزینه‌ها"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # جلوگیری از ثبت مبلغ منفی یا صفر
        if self.amount is None or self.amount <= 0:
            raise ValueError("❌ مبلغ هزینه باید بیشتر از صفر باشد.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # اینجا می‌تونی شرط بزاری مثلاً اگر هزینه تو گزارش اومده، اجازه حذف نده
        super().delete(*args, **kwargs)

# ----------------------------
# 7. مدل گزارش مالی (Financial Reports)
# ----------------------------
class FinancialReport(models.Model):
    start_date = jmodels.jDateField(verbose_name="از تاریخ")  # <-- تاریخ شمسی
    end_date = jmodels.jDateField(verbose_name="تا تاریخ")  # <-- تاریخ شمسی
    usd_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="نرخ دلار")

    total_pieces_sold = models.PositiveIntegerField(verbose_name="تعداد قواره‌ها")
    total_sales_amount = models.PositiveIntegerField(verbose_name="جمع فروش")
    total_stone_cost = models.PositiveIntegerField(verbose_name="هزینه سنگ‌ها")
    total_expenses = models.PositiveIntegerField(verbose_name="جمع هزینه‌ها")
    net_profit = models.IntegerField(verbose_name="سود خالص")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def __str__(self):
        return f"گزارش {self.start_date} تا {self.end_date}"

    class Meta:
        verbose_name = "گزارش مالی"
        verbose_name_plural = "گزارش‌های مالی"
        ordering = ['-created_at']

    def clean(self):
        if self.total_sales_amount < 0 or self.net_profit < 0:
            raise ValidationError("مقادیر فروش یا سود نمی‌تواند منفی باشد.")

    is_locked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk and self.is_locked:
            raise ValueError("این گزارش قفل شده و قابل تغییر نیست.")
        super().save(*args, **kwargs)

    def recalculate_from_data(self):

        invoices = Invoice.objects.filter(date__range=(self.start_date, self.end_date))
        expenses = Expense.objects.filter(date__range=(self.start_date, self.end_date))
        stones = InventoryTransaction.objects.filter(date__range=(self.start_date, self.end_date), type='consume')

        self.total_sales_amount = invoices.aggregate(Sum('total_price'))['total_price__sum'] or 0
        self.total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        self.total_pieces_sold = invoices.aggregate(Sum('quantity'))['quantity__sum'] or 0

        stone_cost = 0
        for s in stones:
            stone_cost += s.quantity_box * s.stone.price_per_box_usd * self.usd_rate
        self.total_stone_cost = int(stone_cost)
        self.net_profit = self.total_sales_amount - self.total_expenses - self.total_stone_cost
        self.save()


# ----------------------------
# 8. مدل پرداخت بدهی مشتری (Customer Payments)
# ----------------------------
class CustomerPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="مشتری")
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.CASCADE, verbose_name="فاکتور مرتبط")
    amount = models.PositiveIntegerField(verbose_name="مبلغ پرداختی")
    date = jmodels.jDateField(verbose_name="تاریخ پرداخت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ثبت‌کننده", related_name="payments_registered")
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="دریافت‌کننده", related_name="payments_received")

    def __str__(self):
        return f"{self.customer.name} - {self.amount} تومان"

    class Meta:
        verbose_name = "پرداخت مشتری"
        verbose_name_plural = "پرداخت‌های مشتریان"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_amount = None
        old_invoice_id = None

        if not is_new:
            try:
                old = CustomerPayment.objects.get(pk=self.pk)
                old_amount = old.amount
                old_invoice_id = old.invoice_id
            except:
                pass
        self.customer.recalculate_financials()


        super().save(*args, **kwargs)

        # ✅ اصلاح بدهی فاکتور در صورت وجود
        if self.invoice:
            # اگر ویرایش شده:
            if not is_new and old_invoice_id == self.invoice_id:
                # اختلاف پرداختی جدید و قبلی
                diff = self.amount - old_amount
                self.invoice.remaining_debt -= diff
            else:
                # اگر پرداخت جدید یا فاکتور تغییر کرده:
                if not is_new and old_invoice_id:
                    # اول فاکتور قبلی را اصلاح کن
                    try:
                        old_invoice = Invoice.objects.get(pk=old_invoice_id)
                        old_invoice.remaining_debt += old_amount
                        old_invoice.save()
                    except:
                        pass

                # حالا فاکتور فعلی را اصلاح کن
                self.invoice.remaining_debt -= self.amount

            self.invoice.save()

    def delete(self, *args, **kwargs):
        # ✅ بازگرداندن مبلغ به بدهی فاکتور
        if self.invoice:
            self.invoice.remaining_debt += self.amount
            self.invoice.save()
            self.customer.recalculate_financials()

        super().delete(*args, **kwargs)

