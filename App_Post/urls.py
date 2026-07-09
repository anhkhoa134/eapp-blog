from django.urls import path

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
]
