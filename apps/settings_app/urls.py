from django.urls import path
from . import views

app_name = 'settings_app'

urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('create-superuser/', views.create_superuser, name='create_superuser'),
    path('user/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('user/<int:pk>/reset-password/', views.reset_password, name='reset_password'),
    path('shutdown/', views.shutdown_server, name='shutdown'),
]
