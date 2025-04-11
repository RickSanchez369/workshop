from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('customers/', views.customer_list, name='customers'),
    path('invoices/', views.invoice_list, name='invoices'),
    path('inventory/', views.inventory_list, name='inventory'),
    path('expenses/', views.expense_list, name='expenses'),
    path('financial/', views.financial_report, name='financial'),
    path('financial/export/', views.export_financial_report_docx, name='financial_export'),
    path('user-stats/', views.user_report, name='user_report'),
    path('download-backup/', views.download_backup, name='download_backup'),
]
