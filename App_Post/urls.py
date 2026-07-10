from django.urls import path
from django.views.generic import RedirectView

from . import views


app_name = 'post'

urlpatterns = [
    path('htmx/comment-add/<int:post_id>/', views.add_comment, name='add_comment'),
    path('htmx/reply-add/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('htmx/reply-add/<int:comment_id>/<int:reply_id>/', views.add_reply, name='add_reply'),
    path('bai-viet/', views.post_all, name='post_all'),
    path('chu-de/<slug:slug_subject>/', views.post_all, name='subject'),
    path('chu-de/<slug:slug_subject>/<slug:slug_subsubject>/', views.post_all, name='post_all'),
    path('bai-viet/<slug:slug_subject>/<slug:slug_post>/', views.post_detail, name='post_detail'),
    path('chu-de-phu/<slug:slug_subsubject>/', views.subsubject, name='subsubject'),

    # Legacy redirect: URL cũ (không dấu gạch) -> URL canonical mới
    path('baiviet/', RedirectView.as_view(pattern_name='post:post_all', permanent=True, query_string=True)),
    path('chude/<slug:slug_subject>/', RedirectView.as_view(pattern_name='post:subject', permanent=True, query_string=True)),
    path('chude/<slug:slug_subject>/<slug:slug_subsubject>/', RedirectView.as_view(pattern_name='post:post_all', permanent=True, query_string=True)),
    path('baiviet/<slug:slug_subject>/<slug:slug_post>/', RedirectView.as_view(pattern_name='post:post_detail', permanent=True, query_string=True)),
]
