from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from App_Post.models import Post, Subject, SubSubject
from App_Product.models import Category, Product


class StaticViewSitemap(Sitemap):
    # priority/changefreq theo từng trang: trang chủ quan trọng nhất, các trang tĩnh còn lại ít thay đổi
    PAGES = {
        'core:home': {'priority': 1.0, 'changefreq': 'daily'},
        'core:about': {'priority': 0.5, 'changefreq': 'monthly'},
        'core:contact': {'priority': 0.5, 'changefreq': 'monthly'},
        'core:CTV': {'priority': 0.5, 'changefreq': 'monthly'},
    }

    def items(self):
        return list(self.PAGES.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.PAGES[item]['priority']

    def changefreq(self, item):
        return self.PAGES[item]['changefreq']

class PostSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        # get_absolute_url cần subject.slug nên loại bài chưa gán subject (tránh lỗi 500 khi render sitemap)
        return Post.objects.filter(subject__isnull=False).select_related('subject').order_by('-display_at')

    def lastmod(self, obj):
        return obj.updated_at

    def images(self, obj):
        if obj.thumbnail:
            return [{
                'location': obj.thumbnail.url,
                'title': obj.title,
                'caption': obj.description[:100] if obj.description else ''
            }]
        return []

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def images(self, obj):
        if obj.thumbnail:
            return [{
                'location': obj.thumbnail.url,
                'title': obj.name,
                'caption': obj.description[:100] if obj.description else ''
            }]
        return []

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.all()

class SubjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Subject.objects.all()

class SubSubjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return SubSubject.objects.select_related('subject')
