from django.contrib import admin

from .models import (
    Attribute,
    CartItem,
    Category,
    Compare,
    Order,
    OrderItem,
    Product,
    ProductPhoto,
    ProductVariant,
    Review,
    SubCategory,
    VariantAttribute,
    Wishlist,
)


class ProductPhotoAdmin(admin.TabularInline):
    model = ProductPhoto


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductPhotoAdmin]
    list_display = ['name', 'slug', 'price', 'price_sale', 'created_at']


class AttributeAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']


class VariantAttributeAdmin(admin.TabularInline):
    model = VariantAttribute


class ProductVariantAdmin(admin.ModelAdmin):
    inlines = [VariantAttributeAdmin]
    list_display = ['product', 'name', 'slug', 'price', 'price_sale']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_paid', 'status_order', 'note', 'created_at']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product']


class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'created_at']


admin.site.register(Product, ProductAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(CartItem, CartItemAdmin)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')


@admin.register(Compare)
class CompareAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_products')

    def display_products(self, obj):
        return ", ".join([product.name for product in obj.products.all()])
    display_products.short_description = 'Products'
