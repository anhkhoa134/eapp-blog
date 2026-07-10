from django.urls import path
from django.views.generic import RedirectView, TemplateView

from . import views


app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('lien-he/', views.contact, name='contact'),
    path('htmx/lien-he-modal/', views.contact_modal, name='contact_modal'),
    path('ctv/', TemplateView.as_view(template_name='CTV.html'), name='CTV'),
    path('gioi-thieu/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('thanh-cong/', TemplateView.as_view(template_name='success.html'), name='success'),
    path('tai-len/', views.custom_upload_function, name='custom_upload_file'),

    # Legacy redirect: URL cũ (không dấu gạch) -> URL canonical mới
    path('lienhe/', RedirectView.as_view(pattern_name='core:contact', permanent=True, query_string=True)),
    path('gioithieu/', RedirectView.as_view(pattern_name='core:about', permanent=True, query_string=True)),
    path('CTV/', RedirectView.as_view(pattern_name='core:CTV', permanent=True, query_string=True)),
    path('success/', RedirectView.as_view(pattern_name='core:success', permanent=True, query_string=True)),
]
