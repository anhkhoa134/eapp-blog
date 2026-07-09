from django import forms
import django_filters
from django.db.models import Q

from .models import Post, Subject, SubSubject


class PostFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(
        method='filter_by_keyword', label=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 
                                      'placeholder': 'Tìm kiếm...'})
    )
    subject = django_filters.ModelChoiceFilter(
        field_name='subject',
        queryset=Subject.objects.all(),
        required=False,
        label='Chủ đề',
        widget=forms.Select(attrs={'class': 'form-select me-2'}),
    )
    subsubject = django_filters.ModelChoiceFilter(
        field_name='subsubject',
        queryset=SubSubject.objects.all(),
        required=False,
        label='Chủ đề con',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    
    class Meta:
        model = Post
        fields = ['keyword', 'subject', 'subsubject']
        
    def filter_by_keyword(self, queryset, title, value):
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )