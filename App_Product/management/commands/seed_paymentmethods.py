from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from PIL import Image, ImageDraw
from io import BytesIO

from App_Product.models import PaymentMethod


PAYMENT_METHODS = [
    {
        'name': 'Chuyển khoản ngân hàng',
        'account_name': 'CONG TY TNHH PTCOM',
        'account_number': '0123456789 - Vietcombank',
    },
    {
        'name': 'Ví điện tử MoMo',
        'account_name': 'PTcom',
        'account_number': '0938717380',
    },
    {
        'name': 'Ví điện tử ZaloPay',
        'account_name': 'PTcom',
        'account_number': '0938717380',
    },
]


def get_owner_user():
    user = User.objects.filter(username='quanly').first()
    if user:
        return user

    user = User.objects.filter(is_superuser=True).order_by('id').first()
    if user:
        return user

    user = User.objects.order_by('id').first()
    if user:
        return user

    raise CommandError('Cần có ít nhất một User trước khi seed phương thức thanh toán.')


def build_seed_qr_png(label):
    size = 420
    cell = 20
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)

    def marker(x, y):
        draw.rectangle((x, y, x + 120, y + 120), fill='black')
        draw.rectangle((x + 20, y + 20, x + 100, y + 100), fill='white')
        draw.rectangle((x + 42, y + 42, x + 78, y + 78), fill='black')

    marker(20, 20)
    marker(280, 20)
    marker(20, 280)

    seed = sum(ord(char) for char in label)
    for row in range(8, 19):
        for col in range(8, 19):
            if (row * 31 + col * 17 + seed) % 5 in (0, 2):
                x = col * cell
                y = row * cell
                draw.rectangle((x, y, x + cell - 4, y + cell - 4), fill='black')

    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


class Command(BaseCommand):
    help = 'Seed dữ liệu phương thức thanh toán cho checkout và trang quản lý thanh toán.'

    def handle(self, *args, **options):
        owner = get_owner_user()
        created_count = 0
        updated_count = 0

        for item in PAYMENT_METHODS:
            paymentmethod, created = PaymentMethod.objects.update_or_create(
                name=item['name'],
                defaults={
                    'user': owner,
                    'account_name': item['account_name'],
                    'account_number': item['account_number'],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

            if not paymentmethod.image:
                filename = f"seed-payment-{slugify(paymentmethod.name)}.png"
                paymentmethod.image.save(
                    filename,
                    ContentFile(build_seed_qr_png(paymentmethod.name)),
                    save=True,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Đã seed phương thức thanh toán: tạo {created_count}, cập nhật {updated_count}.'
        ))
