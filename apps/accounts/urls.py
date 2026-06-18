from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('counters/', views.counter_list, name='counter_list'),
    path('counters/add/', views.counter_add, name='counter_add'),
    path('counters/<int:pk>/edit/', views.counter_edit, name='counter_edit'),
    path('partners/', views.partner_list, name='partner_list'),
    path('partners/add/', views.partner_add, name='partner_add'),
    path('partners/<int:pk>/edit/', views.partner_edit, name='partner_edit'),
]
