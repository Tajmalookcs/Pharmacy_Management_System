from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pos/<int:counter_id>/', views.pos, name='pos'),
    path('pos/drug-search/', views.drug_search_api, name='drug_search'),
    path('pos/submit/', views.sale_submit, name='sale_submit'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/receipt/', views.sale_receipt, name='sale_receipt'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('returns/', views.return_list, name='return_list'),
    path('returns/new/<int:sale_id>/', views.return_new, name='return_new'),
    path('returns/<int:pk>/', views.return_detail, name='return_detail'),
    path('day-closing/', views.day_closing_list, name='day_closing_list'),
    path('day-closing/new/', views.day_closing_new, name='day_closing_new'),
    path('day-closing/<int:pk>/', views.day_closing_detail, name='day_closing_detail'),
]
