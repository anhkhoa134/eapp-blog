from django.contrib import admin
from django.urls import path, re_path, include
from . import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
from django.contrib.sitemaps.views import sitemap
from App_Core.sitemap import StaticViewSitemap, PostSitemap, SubjectSitemap, SubSubjectSitemap

# Sitemap Product/Category tạm bỏ — site hiện chỉ dùng Post, sẽ tính sau
sitemaps = {
    'static': StaticViewSitemap,
    'posts': PostSitemap,
    'subjects': SubjectSitemap,
    'subsubjects': SubSubjectSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),),
    
    path('', include('App_Core.urls', namespace='core')),
    path('', include('App_Account.urls', namespace='account')),
    path('', include('App_Product.urls', namespace='product')),
    path('', include('App_Post.urls', namespace='post')),
    path('', include('App_Quanly.urls', namespace='quanly')),
   
    re_path(r'^', include('templated_email.urls', namespace='templated_email')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps, 'template_name': 'sitemap.xml'}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


from django.conf.urls import handler404, handler500
handler404 = 'App_Core.views.handler404'
handler500 = 'App_Core.views.handler500'
