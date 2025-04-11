from django.db import models
from django.contrib.auth.models import User
import django_jalali.db.models as jmodels  # ✅ اضافه کن اگر هنوز نذاشتی




# Create your models here.


# ----------------------------
# 1. مدل مشتری (Customers)
# ----------------------------
class Customer(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام مشتری")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتری‌ها"
        ordering = ['name']

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
    quantity = models.PositiveIntegerField(verbose_name="تعداد قواره")
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


