from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('employees/', views.employees, name='employees'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('employee/<int:pk>/update/', views.employee_update, name='employee_update'),
    path('employee/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('payroll/', views.payroll, name='payroll'),
    path('leave/', views.leave, name='leave'),
    path('attendance/', views.attendance, name='attendance'),
]
