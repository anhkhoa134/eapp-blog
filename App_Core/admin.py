from django.contrib import admin

from .models import Contact, PageView

admin.site.register(Contact)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('path', 'view_count')
    search_fields = ('path',)
    ordering = ('-view_count',)
