from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from templated_email import send_templated_mail

from .models import Profile


@shared_task
def send_birthday_emails():
    today = now().date()
    profiles = Profile.objects.filter(
        birthday__day=today.day,
        birthday__month=today.month,
    )

    sent_emails = []

    for profile in profiles:
        if profile.email:
            send_templated_mail(
                template_name='birthday_email',
                from_email=None,
                recipient_list=[profile.email],
                context={
                    'site_name': 'eApp Blog',
                    'subject': 'Chúc mừng sinh nhật!',
                    'email': profile.email,
                    'name': profile.fullname or '',
                    'birthday': today.strftime('%d/%m'),
                    'date_today': now().strftime('%d-%m-%Y'),
                },
            )
            sent_emails.append(f"{profile.fullname} <{profile.email}>")

    if sent_emails:
        # Gửi báo cáo tiến trình cho tài khoản quản lý
        quanly_email = (
            get_user_model().objects.filter(username='quanly')
            .values_list('email', flat=True).first()
        )
        if quanly_email:
            send_templated_mail(
                template_name='admin_report_email',
                from_email=None,
                recipient_list=[quanly_email],
                context={
                    'sent_count': len(sent_emails),
                    'sent_emails': sent_emails,
                    'date': now().strftime('%d-%m-%Y'),
                },
            )

    return f"Đã gửi {len(sent_emails)} email sinh nhật."
