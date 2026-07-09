from django import forms
import django_filters
from django.db.models import Q
from .models import Category, Order, Product, SubCategory
from App_Core.constants import IS_PAID, IS_STOCK_BOOL, STATUS_ORDER


class ProductFilter(django_filters.FilterSet):    
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains', label=False, 
                                    widget=forms.TextInput(attrs={'class': 'form-control me-2',
                                                                  'placeholder': 'Tìm kiếm...'}))

    category = django_filters.ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select me-2'}),
    )

    subcategory = django_filters.ModelChoiceFilter(
        field_name='subcategory',
        queryset=SubCategory.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    is_stock = django_filters.ChoiceFilter(field_name='is_stock', choices=IS_STOCK_BOOL, label=False,
                                        widget=forms.Select(attrs={'class': 'form-select',}))

    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gt', label=False, 
                                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                                          'placeholder': 'Giá tối thiểu...'}))
    
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lt', label=False, 
                                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                                          'placeholder': 'Giá tối đa...'}))
    
    class Meta:
        model = Product
        fields = ['name', 'is_stock', 'category', 'subcategory', 'price']
        
        
        
class OrderFilter(django_filters.FilterSet):
    is_paid = django_filters.ChoiceFilter(field_name='is_paid', choices=IS_PAID, label=False, 
                                         widget=forms.Select(attrs={'class': 'form-select me-2',}))
    
    status_order = django_filters.ChoiceFilter(field_name='status_order', choices=STATUS_ORDER, label=False, 
                                         widget=forms.Select(attrs={'class': 'form-select',}))

    min_price = django_filters.NumberFilter(field_name="total_price", lookup_expr='gt', label=False, 
                                            widget=forms.TextInput(attrs={'class': 'form-control me-2',
                                                                          'placeholder': 'Giá tối thiểu...'}))
    
    max_price = django_filters.NumberFilter(field_name="total_price", lookup_expr='lt', label=False, 
                                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                                          'placeholder': 'Giá tối đa...'}))
    
    class Meta:
        model = Order
        fields = [
            # 'total_price', 
                  'is_paid', 'status_order']
