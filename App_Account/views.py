import logging

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from templated_email import send_templated_mail

from App_Account.forms import CustomPasswordChangeForm, RegisterForm
from App_Account.models import Checkout_info, Profile
from App_Product.models import Order
from App_Product.cart_access import merge_guest_commerce_to_user
from App_Account.password_validation import get_password_strength_errors

logger = logging.getLogger(__name__)


def register_user(request):
    # Lưu 'next_url' vào session nếu có trong GET
    if 'next' in request.GET:
        request.session['next_url'] = request.GET.get('next')
    next_url = request.session.get('next_url', '/')  # Lấy 'next_url' từ session, mặc định là trang chủ
    logger.debug("register_user next_url=%s", next_url)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Đăng ký thành công!")
            
            # Xóa 'next_url' khỏi session sau khi đăng nhập thành công
            request.session.pop('next_url', None)
            logger.debug("register_user POST next_url=%s session_next_url=%s", next_url, request.session.get('next_url', None))
            if next_url: # Kiểm tra nếu có tham số 'next' thì chuyển hướng về trang trước đó
                return redirect(next_url)

            return redirect('core:home')
        else:
            messages.success(request, "Tài khoản không đúng, vui lòng tạo lại.")
            return redirect('account:register')
        
    else:
        form = RegisterForm()
        return render(request, 'register.html', {'form':form,})

def check_username_register(request):
    username = request.POST.get('username')

    if not username:
        return HttpResponse("")
    elif get_user_model().objects.filter(username=username).exists():
        return HttpResponse("<div style='color: red;'>Tên tài khoản đã tồn tại, vui lòng chọn tên khác.</div>")
    elif ' ' in username:
        return HttpResponse("<div style='color: red;'>Tên tài khoản không được có khoảng trắng.</div>")
    else:
        return HttpResponse("<div style='color: green;'>Tên tài khoản phù hợp.</div>")

def check_username_login(request):
    username = request.POST.get('username')

    if not username:
        return HttpResponse("")
    elif not get_user_model().objects.filter(username=username).exists():
        return HttpResponse("<div style='color: red;'>Tên tài khoản không tồn tại.</div>")
    else:
        return HttpResponse("<div style='color: green;'>Tên tài khoản phù hợp.</div>")

def toanbo_so(password1):
    for char in str(password1):
        if not char.isdigit(): # nếu không phải số thì False => có ký tự khác
            return False
    return True                # ngược lại, nếu ko có False, từ trở về True => toàn bộ là số

def check_old_password(request):
    old_password = request.POST.get('old_password')
    if not request.user.check_password(old_password):
        return HttpResponse("<div style='color: red;'>Mật khẩu cũ không chính xác.</div>")
    return HttpResponse("<div style='color: green;'>Mật khẩu cũ chính xác.</div>")

def check_password1(request):
    password1 = request.POST.get('password1')
    if not password1:
        return HttpResponse("")

    user = request.user if request.user.is_authenticated else None
    errors = get_password_strength_errors(
        password1,
        user=user,
        username=request.POST.get('username'),
    )
    if errors:
        return HttpResponse("".join(f"<div style='color: red;'>{error}</div>" for error in errors))
    return HttpResponse("<div style='color: green;'>Mật khẩu phù hợp.</div>")

def check_password2(request):
    password1 = request.POST.get('password1')
    password2 = request.POST.get('password2')

    if not password2:
        return HttpResponse("")
    if not password1:
        return HttpResponse("<div style='color: red;'>Vui lòng nhập mật khẩu mới trước.</div>")
    if password1 == password2:
        return HttpResponse("<div style='color: green;'>Xác nhận mật khẩu trùng khớp.</div>")
    return HttpResponse("<div style='color: red;'>Xác nhận mật khẩu không trùng với mật khẩu mới.</div>")

def login_user(request):
    guest_session_key = request.session.session_key
    # Lưu 'next_url' vào session nếu có trong GET
    if 'next' in request.GET:
        request.session['next_url'] = request.GET.get('next')
    if request.method == "GET" and request.GET.get('auth_message') == 'cart':
        messages.info(request, "Vui lòng đăng nhập tài khoản để thêm sản phẩm vào giỏ hàng.")
    if request.method == "GET" and request.GET.get('auth_message') == 'wishlist':
        messages.info(request, "Vui lòng đăng nhập tài khoản để thêm sản phẩm vào yêu thích.")
    next_url = request.session.get('next_url')  # Lấy 'next_url' từ session
    # print('login_user: next_url: ', next_url)
    
    quanly_url = request.session.get('quanly_url')
    # print('login_user: quanly_url: ', quanly_url)
    
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password1']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            merge_guest_commerce_to_user(request, user, guest_session_key)
            
            # Xóa 'next_url' khỏi session sau khi đăng nhập thành công
            request.session.pop('next_url', None)
            # print('POST: next_url: ', next_url)
            # print('POST: session: ', request.session.get('next_url', None))
            if next_url: # Kiểm tra nếu có tham số 'next' thì chuyển hướng về trang trước đó
                messages.success(request, "Đăng nhập thành công!")
                return redirect(next_url)
            
            request.session.pop('quanly_url', None)
            # print('POST: quanly_url: ', quanly_url)
            if quanly_url:
                if request.user.username == 'quanly':
                    messages.success(request, "Đăng nhập thành công!")
                    return redirect(quanly_url)
            
            messages.success(request, "Đăng nhập thành công!")
            return redirect('core:home')
        
        else:
            messages.error(request, "Tài khoản không đúng, vui lòng đăng nhập lại.")
            return redirect('account:login')
        
    else:
        form = RegisterForm()
        return render(request, 'login.html', {'form':form,})

def logout_user(request):
    logout(request)
    messages.success(request, "Đăng xuất tài khoản.")
    return redirect('core:home')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()  # Lưu mật khẩu mới
            login(request, user)  # Đăng nhập lại người dùng
            messages.success(request, "Mật khẩu thay đổi thành công.")
            return redirect('core:home')
        else:
            messages.error(request, "Đã xảy ra lỗi. Vui lòng kiểm tra lại.")
            return redirect('account:change_password')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'registration/change_password.html', {'form': form})

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Nhập email của bạn'}),
        label=False,
    )

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = CustomPasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            users = User.objects.filter(email=data)
            if users.exists():
                for user in users:
                    # Tạo uidb64 và token
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)

                    # Sử dụng templated_email để gửi email reset password
                    send_templated_mail(
                        template_name='reset_email',  # Không cần .html ở đây
                        from_email=None,
                        recipient_list=[user.email],
                        context={
                            'email': user.email,
                            'domain': request.META['HTTP_HOST'],
                            'site_name': 'PTcom',
                            'uid': uidb64,
                            'user': user,
                            'token': token,
                            'protocol': 'https' if request.is_secure() else 'http',
                            'date_today': timezone.now().strftime('%d-%m-%Y'),
                        },
                        # Optional:
                        # cc=['cc@example.com'],
                        # bcc=['bcc@example.com'],
                        # headers={'My-Custom-Header':'Custom Value'},
                        # template_prefix="my_emails/",
                        # template_suffix="email",
                    )

                return redirect("account:password_reset_done")
            
            else:
                messages.error(request, "Email không tồn tại.")
                return redirect("account:password_reset_request")
            
    password_reset_form = CustomPasswordResetForm()
    return render(request, 'registration/reset_form.html', {'form': password_reset_form})

def password_reset_done(request):
    return render(request, 'registration/reset_done.html')

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mật khẩu mới'})
        self.fields['new_password1'].help_text = '<ul class="form-text text-muted small"><li>Mật khẩu phải có ít nhất 8 ký tự</li><li>Không được toàn bộ là số</li><li>Không được giống "Tên tài khoản"</li><li>Không nên sử dụng mật khẩu phổ biến như "1234", "abcdef", "password"</li></ul>'
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Xác nhận lại mật khẩu'})
        self.fields['new_password1'].label = False
        self.fields['new_password2'].label = False

def password_reset_confirm(request, uidb64=None, token=None):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('account:password_reset_complete')
        else:
            form = CustomSetPasswordForm(user)
    else:
        form = None
    return render(request, 'registration/reset_confirm.html', {'form': form})

def password_reset_complete(request):
    return render(request, 'registration/reset_complete.html')

@login_required
def edit_profile(request):
    profile = Profile.objects.get(user=request.user)
    uploaded_size = profile.get_uploaded_size()
    
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email')
        user.save()
                
        profile.fullname = request.POST.get('fullname')
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        if request.POST.get('birthday'):
            profile.birthday = request.POST.get('birthday')
        else:
            profile.birthday = None
        profile.gender = request.POST.get('gender')
        profile.email = request.POST.get('email')
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        profile.request = request
        profile.save()
        messages.success(request, "Cập nhật Thông tin tài khoản.")
        return redirect('account:edit_profile')
    
    return render(request, 'edit_profile.html', {'profile':profile,
                                                          'uploaded_size': uploaded_size,})

@login_required
def edit_info(request):
    info = Checkout_info.objects.get(user=request.user)
   
    if request.method == 'POST':
        info.fullname = request.POST.get('fullname')
        info.phone = request.POST.get('phone')
        info.address = request.POST.get('address')
        info.save()
        messages.success(request, "Cập nhật Địa chỉ giao hàng.")
        return redirect('account:edit_info')
   
    return render(request, 'edit_info.html', {'info':info})

@login_required
def order_cus(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product', 'items__variant__attributes__attribute')
        .order_by('-id')
    )
    return render(request, 'order_cus.html', {'orders':orders,})
