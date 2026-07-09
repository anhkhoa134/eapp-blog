from django.contrib import admin

from .models import Comment, Post, SubSubject, Subject


class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']


class SubjectAdmin(admin.ModelAdmin):
    list_display = ['title']


class SubSubjectAdmin(admin.ModelAdmin):
    list_display = ['title']


admin.site.register(Post, PostAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(SubSubject, SubSubjectAdmin)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'content', 'created_at')
