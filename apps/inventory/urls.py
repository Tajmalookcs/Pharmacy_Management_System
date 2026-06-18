from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.drug_list, name='drug_list'),
    path('add/', views.drug_add, name='drug_add'),
    path('<int:pk>/', views.drug_detail, name='drug_detail'),
    path('<int:pk>/edit/', views.drug_edit, name='drug_edit'),
    path('<int:pk>/delete/', views.drug_delete, name='drug_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_add, name='purchase_add'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('adjustments/', views.adjustment_list, name='adjustment_list'),
    path('adjustments/add/', views.adjustment_add, name='adjustment_add'),
]
