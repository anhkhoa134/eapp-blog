import json
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from templated_email import send_templated_mail

from App_Core.forms import ContactForm
from App_Core.middleware import generate_response
from App_Core.models import Contact
from App_Post.models import Post, Subject
from App_Product.models import Category
from App_Core.storage import CustomStorage

logger = logging.getLogger(__name__)


def handler404(request, exception, template_name='404.html'):
    logger.error(f"404 Error: {request.path} - {exception}")
    return render(request, 'partials/error_404_500.html', status=404)

def handler500(request, *args, **argv):
    logger.error(f"500 Error: {request.path} - {args} - {argv}")
    return render(request, 'partials/error_404_500.html', status=500)

def csrf_failure(request, reason=""):
    # CSRF lệch ở trang đăng nhập (token cũ do cache/back-forward/phiên đổi):
    # đưa về form login với thông báo thay vì trang Forbidden 403 thô
    logger.warning(f"CSRF failure: {request.path} - {reason}")
    if request.path == reverse('account:login'):
        messages.error(request, "Tài khoản đã đăng nhập ở một nơi khác hoặc phiên đăng nhập đã thay đổi. Vui lòng đăng nhập lại.")
        return redirect('account:login')
    return render(request, 'partials/error_404_500.html', status=403)

@login_required
@csrf_exempt
def custom_upload_function(request):
    if request.method == 'POST' and request.FILES.get('upload'):
        upload = request.FILES['upload']

        # Chặn các định dạng ngoài whitelist (tránh lưu .svg/.html gây stored XSS)
        ext = os.path.splitext(upload.name)[1].lstrip('.').lower()
        allowed_types = [t.lower() for t in getattr(settings, 'CKEDITOR_5_UPLOAD_FILE_TYPES', [])]
        if allowed_types and ext not in allowed_types:
            return JsonResponse({'error': {'message': f'Định dạng .{ext} không được hỗ trợ'}}, status=400)

        user_id = request.user.id
        username = request.user.username
        custom_storage = CustomStorage(user_id, username)
        file_name = custom_storage.save(upload.name, upload)
        file_url = custom_storage.url(file_name)
        return JsonResponse({'url': file_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def home(request):
    try:
        # prefetch subcategories vì nav trong base.html duyệt category.subcategories
        categories = Category.objects.prefetch_related('subcategories')
        subjects = Subject.objects.prefetch_related('posts').order_by('id')

        posts = Post.objects.select_related('subject', 'subsubject').order_by('-display_at')
        posts_featured = Post.objects.filter(featured=True).select_related('subject').order_by('-display_at')

        # Hero trang chủ blog: ưu tiên bài featured, thiếu thì bù bài mới nhất
        hero_posts = list(posts_featured[:3])
        if len(hero_posts) < 3:
            hero_ids = [post.id for post in hero_posts]
            hero_posts += list(posts.exclude(id__in=hero_ids)[:3 - len(hero_posts)])
        hero_ids = [post.id for post in hero_posts]
        latest_posts = posts.exclude(id__in=hero_ids)[:6]

        return render(request, 'home.html', {'categories':categories,
                                                    'subjects':subjects,
                                                    'posts':posts,
                                                    'posts_featured':posts_featured,
                                                    'hero_posts':hero_posts,
                                                    'latest_posts':latest_posts,
                                                    })
    except Exception:
        logger.exception("Home view error")
        # Trong trường hợp lỗi, render trang home với dữ liệu rỗng
        return render(request, 'home.html', {
            'categories': [],
            'subjects': [],
            'posts': [],
            'posts_featured': [],
            'hero_posts': [],
            'latest_posts': [],
        })

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Process the form data
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Lưu thông tin vào cơ sở dữ liệu
            Contact.objects.create(
                name=name,
                phone=phone,
                email=email,
                message=message
            )
            
            # Gửi email
            # send_mail(
            #     subject = "Thông báo mới từ eApp Blog",
            #     message = f"Đây là tin nhắn tự động. \nName: {name} \nPhone: {phone} \nEmail: {email} \nNội dung: {message}",
            #     from_email = None,
            #     recipient_list = ["wenlamsao@gmail.com"],
            #     fail_silently = False,
            # )
            
            quanly_email = get_user_model().objects.get(username='quanly').email
            send_templated_mail(
                template_name='contact_email',  # Không cần .html ở đây
                from_email=None,
                recipient_list=[quanly_email],
                context={
                    'site_name': 'eApp Blog',
                    'name': name,
                    'phone':phone,
                    'email': email,
                    'message': message,
                    'date_today': timezone.now().strftime('%d-%m-%Y'),
                },
            )
            
            messages.success(request, "Chúng tôi đã tiếp nhận thông tin và sẽ phản hồi sớm!")
            return redirect('core:success')
        
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form':form,})

def contact_modal(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            Contact.objects.create(
                name=name,
                phone=phone,
                email=email,
                message=message
            )
            
            quanly_email = get_user_model().objects.get(username='quanly').email
            send_templated_mail(
                template_name='contact_email',  # Không cần .html ở đây
                from_email=None,
                recipient_list=[quanly_email],
                context={
                    'site_name': 'eApp Blog',
                    'name': name,
                    'phone':phone,
                    'email': email,
                    'message': message,
                    'date_today': timezone.now().strftime('%d-%m-%Y'),
                },
            )
            
            return generate_response("Gửi liên hệ thành công.", 'bg-success')
        else:
            return generate_response("Gửi liên hệ thất bại.", 'bg-danger')
    else:
        form = ContactForm()
    return render(request, 'partials/contact_modal.html', {'form': form})
