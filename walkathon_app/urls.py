from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register', views.register, name='register'),
    path('registered_list/', views.registered_list, name='registered_list'),
    path('checkin_list/', views.checkin_list, name='checkin_list'),
    path('scan_now/', views.scan_now, name='scan_now'),
    path('process_scan/', views.process_scan, name='process_scan'),
    path('certificate_entries/', views.certificate_entries, name='certificate_entries'),
    path('reports/', views.reports, name='reports'),
    path('logs_triggered/', views.logs_triggered, name='logs_triggered'),
    path('export_csv/', views.export_participants_csv, name='export_csv'),
    path('captcha_image/', views.captcha_image, name='captcha_image'),
    path('upload_excel/', views.upload_excel, name='upload_excel'),
    path('bulk_ticket/', views.bulk_ticket, name='bulk_ticket'),
]