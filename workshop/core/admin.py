from django.contrib import admin
from .models import Customer, Design, Stone, InventoryTransaction, Invoice, Expense, FinancialReport , CustomerPayment
from .models import CustomerPayment

# Register your models here.
# ----------------------------
# مشتری
# ----------------------------
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone']
    search_fields = ['name', 'phone']
    ordering = ['name']


# ----------------------------
# طرح
# ----------------------------
@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']
    ordering = ['title']


# ----------------------------
# سنگ
# ----------------------------
@admin.register(Stone)
class StoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_per_box_usd', 'stock_box']
    search_fields = ['name']
    ordering = ['name']


# ----------------------------
# تراکنش انبار
# ----------------------------
@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['stone', 'date', 'quantity_box', 'type']
    list_filter = ['type', 'stone']
    search_fields = ['stone__name']
    ordering = ['-date']


# ----------------------------
# فاکتور فروش
# ----------------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'date', 'total_price', 'amount_paid', 'remaining_debt']
    list_filter = ['payment_type', 'date']
    search_fields = ['invoice_number', 'customer__name']
    ordering = ['-date']


# ----------------------------
# هزینه
# ----------------------------
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'amount', 'note' ]
    list_filter = [ 'date']
    search_fields = [ 'user__username']
    ordering = ['-date']



# ----------------------------
# گزارش مالی
# ----------------------------
@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['start_date', 'end_date', 'total_sales_amount', 'total_expenses', 'net_profit', 'created_by']
    list_filter = ['created_at']
    search_fields = ['created_by__username']
    ordering = ['-created_at']



@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'date', 'received_by', 'user', 'invoice')
    list_filter = ('date', 'received_by')
    search_fields = ('customer__name', 'user__username', 'received_by__username')