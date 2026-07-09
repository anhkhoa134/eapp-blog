# Seed dữ liệu để test giao diện và tính năng của trang quản lý (quanly).
# Cách chạy: python manage.py seed_quanly
#
# Script sẽ tạo:
#   - Khách hàng (User + Profile + Checkout_info)
#   - Đơn hàng + OrderItem trải đều 12 tháng (cho biểu đồ dashboard & fulltime)
#   - Liên hệ (Contact) - có cả đã đọc / chưa đọc
#   - Đánh giá sản phẩm (Review)
#   - Chủ đề + Bài viết (Subject, SubSubject, Post) + Bình luận (Comment, Reply)
#   - Lượt truy cập trang (PageView)
#
# Chạy lại nhiều lần được: dữ liệu seed cũ (nhận diện qua email @seed.test)
# sẽ bị xóa và tạo mới, dữ liệu thật không bị ảnh hưởng.

import random
import calendar
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from App_Core.models import Contact, PageView
from App_Post.management.commands.seed_posts import seed_posts
from App_Post.models import Comment, Reply
from App_Product.models import Order, OrderItem, Product, Review

# Đuôi email để nhận diện dữ liệu seed
SEED_EMAIL_DOMAIN = '@seed.test'
SEED_PASSWORD = '123456'

# (username, fullname, phone, address)
SEED_CUSTOMERS = [
    ('minhanh',   'Nguyễn Minh Anh',  '0901234561', '12 Nguyễn Huệ, Quận 1, TP.HCM'),
    ('tuankiet',  'Trần Tuấn Kiệt',   '0901234562', '45 Lê Lợi, Quận 3, TP.HCM'),
    ('thuha',     'Phạm Thu Hà',      '0901234563', '78 Trần Hưng Đạo, Quận 5, TP.HCM'),
    ('quochuy',   'Lê Quốc Huy',      '0901234564', '23 Hai Bà Trưng, Hoàn Kiếm, Hà Nội'),
    ('ngoclan',   'Vũ Ngọc Lan',      '0901234565', '56 Kim Mã, Ba Đình, Hà Nội'),
    ('ducthang',  'Hoàng Đức Thắng',  '0901234566', '89 Nguyễn Trãi, Thanh Xuân, Hà Nội'),
    ('phuongvy',  'Đặng Phương Vy',   '0901234567', '34 Bạch Đằng, Hải Châu, Đà Nẵng'),
    ('hoangnam',  'Bùi Hoàng Nam',    '0901234568', '67 Lê Duẩn, Thanh Khê, Đà Nẵng'),
    ('kimchi',    'Ngô Kim Chi',      '0901234569', '90 Trần Phú, Nha Trang, Khánh Hòa'),
    ('vanphuc',   'Đỗ Văn Phúc',      '0901234570', '11 Hùng Vương, TP. Huế'),
    ('thanhtam',  'Lý Thanh Tâm',     '0901234571', '25 Nguyễn Văn Cừ, Ninh Kiều, Cần Thơ'),
    ('baochau',   'Trịnh Bảo Châu',   '0901234572', '38 Phạm Ngũ Lão, TP. Vũng Tàu'),
    ('giabao',    'Phan Gia Bảo',     '0901234573', '52 Quang Trung, TP. Đà Lạt'),
    ('mytien',    'Võ Mỹ Tiên',       '0901234574', '73 Lý Thường Kiệt, TP. Buôn Ma Thuột'),
    ('anhtuan',   'Dương Anh Tuấn',   '0901234575', '96 Điện Biên Phủ, Bình Thạnh, TP.HCM'),
]

SEED_COMMENTS = [
    'Bài viết rất hữu ích, cảm ơn shop!',
    'Mình đã áp dụng thử và thấy hiệu quả thật.',
    'Cho mình hỏi sản phẩm này còn hàng không ạ?',
    'Thông tin chi tiết quá, đúng cái mình đang tìm.',
    'Shop tư vấn thêm giúp mình với.',
    'Viết thêm nhiều bài như này nữa nhé!',
    'Mình thấy phần so sánh chưa được khách quan lắm.',
    'Đọc xong quyết định chốt đơn luôn.',
]

SEED_REVIEWS = [
    (5, 'Sản phẩm chất lượng, giao hàng nhanh, đóng gói cẩn thận.'),
    (5, 'Rất hài lòng, sẽ ủng hộ shop lần sau.'),
    (4, 'Hàng tốt so với tầm giá, giao hơi chậm một chút.'),
    (4, 'Dùng ổn, đúng mô tả của shop.'),
    (3, 'Sản phẩm tạm được, đóng gói cần cải thiện.'),
    (2, 'Hàng không giống hình lắm, hơi thất vọng.'),
    (5, 'Chuẩn hàng chính hãng, tư vấn nhiệt tình.'),
    (4, 'Giá hợp lý, chất lượng ổn định.'),
]

SEED_CONTACTS = [
    ('Nguyễn Thị Hồng', '0912345678', 'Cho mình hỏi bên shop có giao hàng về tỉnh không ạ?'),
    ('Trần Văn Long', '0912345679', 'Mình muốn đặt số lượng lớn thì có chiết khấu không?'),
    ('Lê Thị Mai', '0912345680', 'Đơn hàng của mình đặt 3 ngày rồi chưa thấy giao.'),
    ('Phạm Đức Anh', '0912345681', 'Sản phẩm bị lỗi thì đổi trả như thế nào ạ?'),
    ('Hoàng Thu Trang', '0912345682', 'Shop có hỗ trợ trả góp không?'),
    ('Vũ Minh Quân', '0912345683', 'Mình cần xuất hóa đơn công ty cho đơn hàng vừa đặt.'),
    ('Đặng Thùy Linh', '0912345684', 'Tư vấn giúp mình laptop cho dân văn phòng với ạ.'),
    ('Bùi Xuân Trường', '0912345685', 'Bên mình muốn hợp tác làm đại lý phân phối.'),
    ('Ngô Thanh Hằng', '0912345686', 'Sản phẩm còn bảo hành không, mình mua 6 tháng rồi.'),
    ('Đỗ Hải Yến', '0912345687', 'Cho hỏi giờ mở cửa của cửa hàng ạ?'),
]

PAYMENT_METHODS = ['COD', 'Chuyển khoản', 'Ví MoMo']
ORDER_STATUS_WEIGHTS = [
    ('Giao thành công', 55),
    ('Chờ xử lý', 20),
    ('Đang vận chuyển', 15),
    ('Đã huỷ', 10),
]


def weighted_choice(pairs):
    values = [v for v, _ in pairs]
    weights = [w for _, w in pairs]
    return random.choices(values, weights=weights, k=1)[0]


def random_datetime_in_month(year, month, max_day=None):
    """Trả về datetime ngẫu nhiên trong tháng, giờ cao điểm mua sắm được ưu tiên."""
    last_day = calendar.monthrange(year, month)[1]
    if max_day:
        last_day = min(last_day, max_day)
    day = random.randint(1, last_day)
    # Ưu tiên khung giờ 8h-22h cho giống hành vi mua thật
    hour = weighted_choice([(random.randint(8, 22), 85), (random.randint(0, 7), 10), (23, 5)])
    return datetime(year, month, day, hour, random.randint(0, 59), random.randint(0, 59))


def clear_old_seed_data():
    """Xóa dữ liệu seed cũ (user seed bị xóa sẽ cascade orders, reviews, comments...)."""
    users = User.objects.filter(email__endswith=SEED_EMAIL_DOMAIN)
    if users.exists():
        print(f"Xóa {users.count()} user seed cũ (kèm đơn hàng, đánh giá, bình luận...)")
        users.delete()

    contacts = Contact.objects.filter(email__endswith=SEED_EMAIL_DOMAIN)
    if contacts.exists():
        print(f"Xóa {contacts.count()} liên hệ seed cũ")
        contacts.delete()


def create_customers():
    print("Tạo khách hàng...")
    customers = []
    for username, fullname, phone, address in SEED_CUSTOMERS:
        email = f'{username}{SEED_EMAIL_DOMAIN}'
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(username=username, email=email, password=SEED_PASSWORD)
        elif not user.email.endswith(SEED_EMAIL_DOMAIN):
            # Trùng username với tài khoản thật -> bỏ qua, không đụng vào
            continue

        # Signal đã tự tạo Profile + Checkout_info, chỉ cần điền thông tin
        profile = user.profile
        profile.fullname = fullname
        profile.phone = phone
        profile.address = address
        profile.email = email
        profile.gender = random.choice(['Nam', 'Nữ'])
        profile.save()
        customers.append(user)
    print(f"  -> {len(customers)} khách hàng")
    return customers


def create_posts_and_comments(customers):
    print("Tạo chủ đề, bài viết và bình luận...")
    posts = seed_posts()

    # Bình luận + trả lời
    quanly_user = User.objects.filter(username='quanly').first()
    comment_count = 0
    for post in posts:
        for content in random.sample(SEED_COMMENTS, random.randint(2, 4)):
            comment = Comment.objects.create(
                post=post,
                user=random.choice(customers),
                content=content,
                is_read=random.random() < 0.6,  # ~40% chưa đọc để test badge thông báo
            )
            created_at = datetime.now() - timedelta(days=random.randint(0, 60),
                                                    hours=random.randint(0, 23))
            Comment.objects.filter(pk=comment.pk).update(created_at=created_at)
            comment_count += 1

            if quanly_user and random.random() < 0.4:
                Reply.objects.create(
                    comment=comment,
                    user=quanly_user,
                    content='Cảm ơn bạn đã quan tâm, shop đã ghi nhận ý kiến nhé!',
                )
    print(f"  -> {len(posts)} bài viết, {comment_count} bình luận")
    return posts


def create_orders(customers, products):
    """Tạo đơn hàng trải đều các tháng trong năm để dashboard & fulltime có dữ liệu chart."""
    print("Tạo đơn hàng...")
    now = datetime.now()
    order_count = 0

    # Mỗi tháng từ đầu năm đến nay: 8-15 đơn, riêng tháng hiện tại 20-30 đơn (cho dashboard)
    for month in range(1, now.month + 1):
        if month == now.month:
            so_don = random.randint(20, 30)
            max_day = now.day
        else:
            so_don = random.randint(8, 15)
            max_day = None

        for _ in range(so_don):
            user = random.choice(customers)
            profile = user.profile
            status = weighted_choice(ORDER_STATUS_WEIGHTS)
            if status == 'Giao thành công':
                is_paid = 'Đã thanh toán'
            elif status == 'Đã huỷ':
                is_paid = 'Chưa thanh toán'
            else:
                is_paid = random.choice(['Đã thanh toán', 'Chưa thanh toán'])

            order = Order.objects.create(
                user=user,
                fullname=profile.fullname,
                phone=profile.phone,
                shipping_address=profile.address,
                payment_method=random.choice(PAYMENT_METHODS),
                status_order=status,
                is_paid=is_paid,
                note=random.choice(['', '', 'Giao giờ hành chính', 'Gọi trước khi giao']),
            )

            # 1-3 sản phẩm mỗi đơn
            for product in random.sample(products, random.randint(1, min(3, len(products)))):
                variant = product.variants.first()
                price = variant.get_price() if variant else product.get_price()
                quantity = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                    price=price,
                    subtotal=price * quantity,
                )
            order.calculate_total()

            # created_at là auto_now_add nên phải update qua queryset
            created_at = random_datetime_in_month(now.year, month, max_day)
            Order.objects.filter(pk=order.pk).update(created_at=created_at)
            order_count += 1

    print(f"  -> {order_count} đơn hàng")


def create_reviews(customers, products):
    print("Tạo đánh giá sản phẩm...")
    review_count = 0
    for product in random.sample(products, min(len(products), 15)):
        for user in random.sample(customers, random.randint(1, 4)):
            rating, content = random.choice(SEED_REVIEWS)
            _, created = Review.objects.get_or_create(
                user=user,
                product=product,
                defaults={'rating': rating, 'content': content},
            )
            if created:
                review_count += 1
    print(f"  -> {review_count} đánh giá")


def create_contacts():
    print("Tạo liên hệ...")
    for i, (name, phone, message) in enumerate(SEED_CONTACTS):
        email = f'lienhe{i + 1}{SEED_EMAIL_DOMAIN}'
        contact = Contact.objects.create(
            name=name,
            phone=phone,
            email=email,
            message=message,
            is_read=random.random() < 0.5,  # một nửa chưa đọc để test badge chuông
        )
        created_at = datetime.now() - timedelta(days=random.randint(0, 30),
                                                hours=random.randint(0, 23))
        Contact.objects.filter(pk=contact.pk).update(created_at=created_at)
    print(f"  -> {len(SEED_CONTACTS)} liên hệ")


def create_pageviews(products, posts):
    print("Tạo lượt truy cập trang...")
    paths = ['/', '/lien-he/', '/gio-hang/', '/bai-viet/']
    paths += [p.get_absolute_url() for p in products[:8] if p.category]
    paths += [p.get_absolute_url() for p in posts[:5] if p.subject]

    for path in paths:
        PageView.objects.update_or_create(
            path=path,
            defaults={'view_count': random.randint(50, 3000)},
        )
    print(f"  -> {len(paths)} trang")


def seed_quanly():
    # Cần có sản phẩm trước (chạy seed_products nếu database trống)
    if not Product.objects.exists():
        print("Chưa có sản phẩm, chạy seed_products trước...")
        call_command("seed_products")

    products = list(Product.objects.all())
    if not products:
        raise CommandError("Không có sản phẩm nào để tạo đơn hàng. Hãy chạy seed_products trước.")

    clear_old_seed_data()

    customers = create_customers()
    if not customers:
        raise CommandError("Không tạo được khách hàng seed nào.")

    posts = create_posts_and_comments(customers)
    create_orders(customers, products)
    create_reviews(customers, products)
    create_contacts()
    create_pageviews(products, posts)

    print("\nSeed dữ liệu trang quản lý hoàn tất!")
    print(f"Tài khoản khách hàng test: username như '{SEED_CUSTOMERS[0][0]}', mật khẩu '{SEED_PASSWORD}'")
    print("Chạy lại command bất cứ lúc nào, dữ liệu seed cũ sẽ được thay mới.")


def run():
    seed_quanly()


class Command(BaseCommand):
    help = "Seed dữ liệu test cho trang quản lý"

    def handle(self, *args, **options):
        seed_quanly()
