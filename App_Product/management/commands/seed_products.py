import os
import random
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.contrib.auth.models import User
from App_Product.models import (
    Category, SubCategory, Product, ProductVariant, Attribute, VariantAttribute
)

class MockRequest:
    def __init__(self, user):
        self.user = user


CATEGORY_CATALOG = {
    "Điện thoại & Máy tính": [
        "Điện thoại di động",
        "Laptop & Tablet",
        "Âm thanh & Tai nghe",
        "Phụ kiện công nghệ",
    ],
    "Thời trang nam nữ": [
        "Áo khoác & Hoodie",
        "Áo thun",
        "Quần jean & Kaki",
        "Giày dép",
        "Túi ví & Phụ kiện",
    ],
    "Tiện ích & Văn phòng": [
        "Văn phòng phẩm",
        "Đồ dùng cá nhân",
        "Đồ gia dụng tiện ích",
    ],
}

PRODUCT_CATALOG = [
    ("iPhone 15 Pro Max 256GB", "Điện thoại & Máy tính", "Điện thoại di động", "iphone-15-pro-max.jpg"),
    ("Samsung Galaxy S24 Ultra", "Điện thoại & Máy tính", "Điện thoại di động", "samsung-galaxy-s24-ultra.jpg"),
    ("Xiaomi Redmi Note 13", "Điện thoại & Máy tính", "Điện thoại di động", "xiaomi-redmi-note-13.jpg"),
    ("MacBook Pro M3 Max", "Điện thoại & Máy tính", "Laptop & Tablet", "macbook-pro-m3-max.jpg"),
    ("iPad Pro 11 inch M2", "Điện thoại & Máy tính", "Laptop & Tablet", "ipad-pro-11-inch-m2.jpg"),
    ("Sony WH-1000XM5 Headphone", "Điện thoại & Máy tính", "Âm thanh & Tai nghe", "sony-wh-1000xm5-headphone.jpg"),
    ("Tai nghe AirPods Pro 2", "Điện thoại & Máy tính", "Âm thanh & Tai nghe", "airpods-pro-2.jpg"),
    ("Loa bluetooth di động", "Điện thoại & Máy tính", "Âm thanh & Tai nghe", "loa-bluetooth-di-dong.jpg"),
    ("Bàn phím cơ Keychron K2", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "ban-phim-co-keychron-k2.jpg"),
    ("Chuột Logitech MX Master 3S", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "chuot-logitech-mx-master-3s.jpg"),
    ("Đế sạc không dây 3 in 1", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "de-sac-khong-day-3-in-1.jpg"),
    ("Đèn treo màn hình PC", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "den-treo-man-hinh-pc.jpg"),
    ("Giá đỡ laptop nhôm gấp gọn", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "gia-do-laptop-nhom-gap-gon.jpg"),
    ("Bộ vệ sinh màn hình 4 in 1", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "bo-ve-sinh-man-hinh-4-in-1.jpg"),
    ("Túi chống sốc laptop 14 inch", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "tui-chong-soc-laptop-14-inch.jpg"),
    ("Đồng hồ thông minh eWatch", "Điện thoại & Máy tính", "Phụ kiện công nghệ", "dong-ho-thong-minh-ewatch.jpg"),
    ("Áo khoác gió bomber nam", "Thời trang nam nữ", "Áo khoác & Hoodie", "ao-khoac-gio-bomber-nam.jpg"),
    ("Áo hoodie nỉ bông", "Thời trang nam nữ", "Áo khoác & Hoodie", "ao-hoodie-ni-bong.jpg"),
    ("Áo thun cotton form rộng", "Thời trang nam nữ", "Áo thun", "ao-thun-cotton-form-rong.jpg"),
    ("Quần jean ống rộng Hàn Quốc", "Thời trang nam nữ", "Quần jean & Kaki", "quan-jean-ong-rong-han-quoc.jpg"),
    ("Quần kaki túi hộp", "Thời trang nam nữ", "Quần jean & Kaki", "quan-kaki-tui-hop.jpg"),
    ("Giày sneaker cổ thấp", "Thời trang nam nữ", "Giày dép", "giay-sneaker-co-thap.jpg"),
    ("Dép lê quai ngang unisex", "Thời trang nam nữ", "Giày dép", "dep-le-quai-ngang-unisex.jpg"),
    ("Ví da bò sáp handmade", "Thời trang nam nữ", "Túi ví & Phụ kiện", "vi-da-bo-sap-handmade.jpg"),
    ("Thắt lưng da cao cấp", "Thời trang nam nữ", "Túi ví & Phụ kiện", "that-lung-da-cao-cap.jpg"),
    ("Balo chống nước du lịch", "Thời trang nam nữ", "Túi ví & Phụ kiện", "balo-chong-nuoc-du-lich.jpg"),
    ("Sổ tay ghi chép bìa da", "Tiện ích & Văn phòng", "Văn phòng phẩm", "so-tay-ghi-chep-bia-da.jpg"),
    ("Bút ký kim loại cao cấp", "Tiện ích & Văn phòng", "Văn phòng phẩm", "but-ky-kim-loai-cao-cap.jpg"),
    ("Bình giữ nhiệt inox 304", "Tiện ích & Văn phòng", "Đồ dùng cá nhân", "binh-giu-nhiet-inox-304.jpg"),
    ("Quạt để bàn mini tích điện", "Tiện ích & Văn phòng", "Đồ gia dụng tiện ích", "quat-de-ban-mini-tich-dien.jpg"),
]


PRODUCT_VARIANT_CATALOG = {
    "iPhone 15 Pro Max 256GB": [
        {
            "price": 29990000,
            "price_sale": 27990000,
            "stock": 12,
            "attributes": [("Màu sắc", "Titan Tự Nhiên"), ("Dung lượng", "256GB")],
        },
        {
            "price": 29990000,
            "price_sale": 27490000,
            "stock": 8,
            "attributes": [("Màu sắc", "Titan Xanh"), ("Dung lượng", "256GB")],
        },
        {
            "price": 34990000,
            "price_sale": 32990000,
            "stock": 5,
            "attributes": [("Màu sắc", "Titan Đen"), ("Dung lượng", "512GB")],
        },
        {
            "price": 41990000,
            "price_sale": 39990000,
            "stock": 3,
            "attributes": [("Màu sắc", "Titan Trắng"), ("Dung lượng", "1TB")],
        },
    ],
}


def get_or_create_variant_attributes(attribute_pairs):
    attributes = []
    for key, value in attribute_pairs:
        attr, _ = Attribute.objects.get_or_create(key=key, value=value)
        attributes.append(attr)
    return attributes


def sync_variant_attributes(variant, attributes):
    VariantAttribute.objects.filter(variant=variant).delete()
    for attr in attributes:
        VariantAttribute.objects.get_or_create(variant=variant, attribute=attr)


def seed_product_variants(product, variants_data, default_variant):
    for index, variant_data in enumerate(variants_data):
        attributes = get_or_create_variant_attributes(variant_data["attributes"])

        if index == 0 and default_variant:
            variant = default_variant
            variant.price = variant_data["price"]
            variant.price_sale = variant_data["price_sale"]
            variant.stock = variant_data["stock"]
            variant.save()
        else:
            variant = ProductVariant.objects.create(
                product=product,
                price=variant_data["price"],
                price_sale=variant_data["price_sale"],
                stock=variant_data["stock"],
            )

        sync_variant_attributes(variant, attributes)

    Product.objects.filter(pk=product.pk).update(
        is_stock=any(variant_data["stock"] > 0 for variant_data in variants_data),
        stock=sum(variant_data["stock"] for variant_data in variants_data),
    )


def seed_products():
    # Setup folders
    project_root = settings.BASE_DIR
    images_folder = os.path.join(project_root, 'static', 'website', 'img')
    seed_images_folder = os.path.join(images_folder, 'seed_products')

    if not os.path.exists(images_folder):
        raise CommandError(f"Thư mục hình ảnh '{images_folder}' không tồn tại.")

    # Get sample images
    supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    image_files = [
        os.path.join(images_folder, f) for f in os.listdir(images_folder)
        if os.path.isfile(os.path.join(images_folder, f)) and os.path.splitext(f)[1].lower() in supported_extensions
    ]

    if not image_files:
        raise CommandError("Không tìm thấy hình ảnh trong thư mục.")

    # Clean existing data to avoid unique name conflict
    print("Clearing old products, variants, and attributes...")
    Product.objects.all().delete()
    Attribute.objects.all().delete()

    # Get default user for request mock
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()

    # Ensure Category & SubCategory exist with the intended parent mapping.
    categories_by_name = {}
    subcategories_by_key = {}
    for category_name, subcategory_names in CATEGORY_CATALOG.items():
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={"description": f"Nhóm sản phẩm {category_name}."},
        )
        categories_by_name[category_name] = category

        for subcategory_name in subcategory_names:
            SubCategory.objects.filter(name=subcategory_name).exclude(category=category).delete()
            subcategory, _ = SubCategory.objects.get_or_create(
                category=category,
                name=subcategory_name,
                defaults={"description": f"{subcategory_name} thuộc {category_name}."},
            )
            subcategories_by_key[(category_name, subcategory_name)] = subcategory

    # Pre-create some Attributes
    sample_attrs = [
        ("Màu sắc", "Đen"),
        ("Màu sắc", "Trắng"),
        ("Màu sắc", "Xanh đen"),
        ("Màu sắc", "Xám"),
        ("Kích thước", "S"),
        ("Kích thước", "M"),
        ("Kích thước", "L"),
        ("Kích thước", "XL"),
        ("Chất liệu", "Cotton"),
        ("Chất liệu", "Polyester"),
    ]
    created_attributes = []
    for key, value in sample_attrs:
        attr, _ = Attribute.objects.get_or_create(key=key, value=value)
        created_attributes.append(attr)

    number_of_products = len(PRODUCT_CATALOG)
    print(f"Starting seed of {number_of_products} products...")

    for i, (name, category_name, subcategory_name, image_filename) in enumerate(PRODUCT_CATALOG):
        try:
            # 1. Select the intended category and subcategory for this product.
            category = categories_by_name[category_name]
            subcategory = subcategories_by_key[(category_name, subcategory_name)]
            product_variants = PRODUCT_VARIANT_CATALOG.get(name)

            # 2. Setup values
            price = random.randint(15, 120) * 10000 # values from 150,000 to 1,200,000
            price_sale = random.choice([None, random.randint(10, int(price/10000 - 5)) * 10000])
            is_stock = random.choice([True, True, True, False]) # 75% chance of being in stock
            stock = random.randint(5, 100) if is_stock else 0
            if product_variants:
                first_variant = product_variants[0]
                price = first_variant["price"]
                price_sale = first_variant["price_sale"]
                stock = sum(variant_data["stock"] for variant_data in product_variants)
                is_stock = stock > 0

            # 3. Instantiate Product
            product = Product(
                category=category,
                subcategory=subcategory,
                name=name,
                description=f"Đây là mô tả chi tiết của sản phẩm {name}. Sản phẩm chất lượng cao, bền bỉ và thời trang.",
                price=price,
                price_sale=price_sale,
                is_stock=is_stock,
                stock=stock,
                is_sale=(price_sale is not None),
                featured=random.choice([True, False, False, False])
            )
            
            # Attach mock request
            product.request = MockRequest(user)

            # 4. Save Main Image
            seed_image_path = os.path.join(seed_images_folder, image_filename)
            selected_image_path = seed_image_path if os.path.exists(seed_image_path) else random.choice(image_files)
            with open(selected_image_path, 'rb') as img_file:
                django_file = File(img_file)
                image_name = f"product_{i}_{image_filename}"
                product.image.save(image_name, django_file, save=True)

            # 5. Link attributes to the variant created by signal
            variant = product.variants.first()
            if product_variants and variant:
                seed_product_variants(product, product_variants, variant)
            elif variant:
                # Add 1 to 2 random attributes to this variant
                attrs_to_add = random.sample(created_attributes, random.randint(1, 2))
                for attr in attrs_to_add:
                    VariantAttribute.objects.get_or_create(variant=variant, attribute=attr)
                
                # Update variant details
                variant.price = price
                variant.price_sale = price_sale
                variant.stock = stock
                variant.save()

            print(f"[{i+1}/{number_of_products}] Created product '{product.name}' successfully.")

        except Exception as e:
            print(f"Error seeding product '{name}': {e}")

    print("Database seeding completed successfully!")


def run():
    seed_products()


class Command(BaseCommand):
    help = "Seed dữ liệu sản phẩm mẫu"

    def handle(self, *args, **options):
        seed_products()
