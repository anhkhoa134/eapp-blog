from django.urls import path
from django.views.generic import RedirectView

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

    # Legacy redirect: URL cũ (không dấu gạch) -> URL canonical mới
    path('dangky/', RedirectView.as_view(pattern_name='account:register', permanent=True, query_string=True)),
    path('dangnhap/', RedirectView.as_view(pattern_name='account:login', permanent=True, query_string=True)),
    path('dangxuat/', RedirectView.as_view(pattern_name='account:logout', permanent=True, query_string=True)),
    path('doimatkhau/', RedirectView.as_view(pattern_name='account:change_password', permanent=True, query_string=True)),
    path('thongtintaikhoan/', RedirectView.as_view(pattern_name='account:edit_profile', permanent=True, query_string=True)),
    path('diachigiaohang/', RedirectView.as_view(pattern_name='account:edit_info', permanent=True, query_string=True)),
    path('donhangdamua/', RedirectView.as_view(pattern_name='account:order_cus', permanent=True, query_string=True)),
    path('password_reset/request/', RedirectView.as_view(pattern_name='account:password_reset_request', permanent=True, query_string=True)),
    path('password_reset/done/', RedirectView.as_view(pattern_name='account:password_reset_done', permanent=True, query_string=True)),
    path('password_reset/<uidb64>/<token>/confirm/', RedirectView.as_view(pattern_name='account:password_reset_confirm', permanent=True, query_string=True)),
    path('password_reset/complete/', RedirectView.as_view(pattern_name='account:password_reset_complete', permanent=True, query_string=True)),
]
