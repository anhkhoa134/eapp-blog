from django.urls import path
from django.views.generic import TemplateView

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
]
