from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Họ tên', }), required=False)
    phone = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Điện thoại', }), required=False)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder': 'Email', }), required=False)
    # subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Nội dung', 'rows': 4}), required=False)


