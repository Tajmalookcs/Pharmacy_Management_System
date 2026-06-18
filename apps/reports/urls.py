from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales'),
    path('stock/', views.stock_report, name='stock'),
    path('expiry/', views.expiry_report, name='expiry'),
    path('profit/', views.profit_report, name='profit'),
    path('partners/', views.partner_report, name='partners'),
    path('counters/', views.counter_report, name='counters'),
    path('export/excel/<str:report_type>/', views.export_excel, name='export_excel'),
    path('export/pdf/<str:report_type>/', views.export_pdf, name='export_pdf'),
]
