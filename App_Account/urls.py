from django.urls import path

from . import views


app_name = 'account'

urlpatterns = [
    path('dang-ky/', views.register_user, name='register'),
    path('dang-nhap/', views.login_user, name='login'),
    path('dang-xuat/', views.logout_user, name='logout'),
    path('doi-mat-khau/', views.change_password, name='change_password'),
    path('thong-tin-tai-khoan/', views.edit_profile, name='edit_profile'),
    path('dia-chi-giao-hang/', views.edit_info, name='edit_info'),
    path('don-hang-da-mua/', views.order_cus, name='order_cus'),
    path('dat-lai-mat-khau/yeu-cau/', views.password_reset_request, name='password_reset_request'),
    path('dat-lai-mat-khau/da-gui/', views.password_reset_done, name='password_reset_done'),
    path('dat-lai-mat-khau/<uidb64>/<token>/xac-nhan/', views.password_reset_confirm, name='password_reset_confirm'),
    path('dat-lai-mat-khau/hoan-tat/', views.password_reset_complete, name='password_reset_complete'),
    path('htmx/check-username-register/', views.check_username_register, name='check_username_register'),
    path('htmx/check-username-login/', views.check_username_login, name='check_username_login'),
    path('htmx/check-old-password/', views.check_old_password, name='check_old_password'),
    path('htmx/check-password1/', views.check_password1, name='check_password1'),
    path('htmx/check-password2/', views.check_password2, name='check_password2'),
]
