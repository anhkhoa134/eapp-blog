from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from App_Core.constants import INPUT_ATTRS, LIMIT_PRODUCT_OR_POST
from .models import Post, PostContent, PostPhoto, SubSubject, Subject


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['title', 'image']
        widgets = {
            'title':forms.TextInput(attrs={'class':'form-control'}), 
            'image':forms.FileInput(INPUT_ATTRS),
        }
        labels = {
            'title': 'Tên chủ đề',
            'image': 'Ảnh',
        }

class SubSubjectForm(forms.ModelForm):
    class Meta:
        model = SubSubject
        fields = ['subject', 'title', 'image']
        widgets = {
            'subject':forms.Select(attrs={'class':'form-select'}), 
            'title':forms.TextInput(INPUT_ATTRS), 
            'image':forms.FileInput(INPUT_ATTRS),
        }
        labels = {
            'subject': 'Thuộc chủ đề',
            'title': 'Tên chủ đề phụ',
            'image': 'Ảnh',
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['subject', 'subsubject', 'title', 'description', 'image',
            'featured',
            # 'price', 'address',
            'display_at',
        ]
        widgets = {
            # 'subject':forms.Select(INPUT_ATTRS),
            'subject': forms.Select(attrs={'class': 'form-control', 'id': 'subject', 'data-searchable': 'true'}),
            'subsubject': forms.Select(attrs={'class': 'form-control', 'id': 'subsubject', 'data-searchable': 'true'}),

            'title':forms.TextInput(INPUT_ATTRS),
            # 'price':forms.TextInput(INPUT_ATTRS),
            'address':forms.TextInput(INPUT_ATTRS),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'featured': forms.Select(choices=[(True, 'Có'), (False, 'Không')], 
                                    attrs={'class': 'form-select'}),
            # 'display_at':forms.DateTimeInput(attrs={'class':'form-control',
            #                                             'type':'datetime-local',}), 
            'display_at':forms.DateInput(attrs={'class':'form-control',
                                                        'type':'date',},), 
            'image':forms.FileInput(INPUT_ATTRS), # bỏ đi widgets của image này, thì form edit hiển thị đường link của image đang dùng
        }
        labels = {
            'subject': 'Tên chủ đề',
            'subsubject': 'Tên chủ đề phụ',
            'title': 'Tên tiêu đề',
            # 'price': 'Giá',
            # 'address': 'Địa chỉ',
            'description': 'Mô tả ngắn',
            'featured': 'Nổi bật',
            'display_at': 'Ngày hiển thị',
            'content': 'Chi tiết nội dung',
            'image': 'Ảnh chính',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        # Get the current instance if it exists (for editing)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # If editing, exclude the current post from the check
            if Post.objects.filter(title=title).exclude(pk=instance.pk).exists():
                raise ValidationError('Tiêu đề này đã tồn tại.')
        else:
            # If creating new post
            if Post.objects.filter(title=title).exists():
                raise ValidationError('Tiêu đề này đã tồn tại.')
        return title

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk and Post.objects.count() >= LIMIT_PRODUCT_OR_POST:
            raise ValidationError(f'Số lượng Bài Viết không được vượt quá {LIMIT_PRODUCT_OR_POST}.')
        return cleaned_data


class PostPhotoForm(forms.ModelForm):
	photo = MultipleFileField(required=False, label='Những ảnh phụ')
	class Meta:
		model = PostPhoto
		fields = ['photo']
		widgets = {'photo':forms.FileInput(INPUT_ATTRS)}

# form cho QuillEditor
# class ContentForm(forms.ModelForm):
# 	class Meta:
# 		model = PostContent
# 		fields = ['content']
# 		widgets = {'content':forms.TextInput(attrs={'class':'form-control'}), }
# 		labels = {'content': False,}

class ContentForm(forms.ModelForm):
	class Meta:
		model = PostContent
		fields = ['content']
		widgets = {'content':CKEditor5Widget(attrs={'class':'django_ckeditor_5'}), }
		labels = {'content': False,}


