from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from App_Post.models import Post, Subject
from App_Product.models import Category, Product


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return ['core:home', 'core:contact', 'core:about']

    def location(self, item):
        return reverse(item)

class PostSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Post.objects.all()

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
