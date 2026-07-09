import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from App_Post.models import Post, PostContent, Subject, SubSubject


class MockRequest:
    def __init__(self, user):
        self.user = user


SUBJECT_CATALOG = {
    "Tin tức công nghệ": {
        "description": "Cập nhật xu hướng điện thoại, laptop và thiết bị thông minh đáng chú ý.",
        "subsubjects": {
            "Điện thoại": "Tin tức, đánh giá và kinh nghiệm chọn mua điện thoại.",
            "Laptop": "Gợi ý chọn laptop theo nhu cầu học tập, làm việc và sáng tạo.",
        },
    },
    "Mẹo mua sắm": {
        "description": "Kinh nghiệm mua hàng online, săn ưu đãi và so sánh sản phẩm trước khi chốt đơn.",
        "subsubjects": {
            "Săn khuyến mãi": "Cách đọc ưu đãi, voucher và lịch sale để mua đúng giá trị.",
            "So sánh sản phẩm": "Khung so sánh cấu hình, giá, bảo hành và chi phí sử dụng.",
        },
    },
    "Hướng dẫn sử dụng": {
        "description": "Hướng dẫn bảo quản thiết bị công nghệ và phụ kiện để dùng bền hơn.",
        "subsubjects": {
            "Bảo quản thiết bị": "Các thói quen sử dụng giúp điện thoại và laptop ổn định lâu dài.",
        },
    },
}


LEGACY_POST_TITLES = [
    "Trên tay iPhone 15 Pro Max: có đáng để nâng cấp?",
    "So sánh Galaxy S24 Ultra và iPhone 15 Pro Max",
    "5 mẫu laptop đáng mua nhất cho sinh viên",
    "MacBook Pro M3: hiệu năng thực tế sau 1 tháng",
    "Bí quyết săn sale ngày đôi không bị hớ",
    "Cách so sánh giá sản phẩm trước khi mua",
    "7 cách kéo dài tuổi thọ pin điện thoại",
    "Vệ sinh laptop đúng cách tại nhà",
]


def article_html(keyword, intro, sections, checklist, faq):
    section_html = "\n".join(
        f"""
        <h2>{heading}</h2>
        <p>{body}</p>
        """
        for heading, body in sections
    )
    checklist_html = "\n".join(f"<li>{item}</li>" for item in checklist)
    faq_html = "\n".join(
        f"""
        <h3>{question}</h3>
        <p>{answer}</p>
        """
        for question, answer in faq
    )
    return f"""
    <p><strong>{keyword}</strong> là chủ đề được nhiều khách hàng quan tâm khi chọn mua thiết bị công nghệ và phụ kiện.
    {intro}</p>
    {section_html}
    <h2>Checklist nhanh trước khi quyết định</h2>
    <ul>
        {checklist_html}
    </ul>
    <h2>Câu hỏi thường gặp</h2>
    {faq_html}
    <h2>Kết luận</h2>
    <p>Hãy ưu tiên sản phẩm phù hợp nhu cầu thật, có bảo hành rõ ràng và tổng chi phí sử dụng hợp lý.
    Khi cần tư vấn, bạn có thể đối chiếu các tiêu chí trong bài để chọn nhanh hơn và giảm rủi ro mua nhầm.</p>
    """


SEO_POSTS = [
    {
        "title": "iPhone 15 Pro Max có đáng mua trong năm 2026?",
        "subject": "Tin tức công nghệ",
        "subsubject": "Điện thoại",
        "image": "iphone-15-pro-max-2026.jpg",
        "featured": True,
        "description": "Đánh giá iPhone 15 Pro Max trong năm 2026: hiệu năng, camera, pin, giá bán và nhóm người dùng nên nâng cấp để mua đúng nhu cầu.",
        "content": article_html(
            "iPhone 15 Pro Max có đáng mua",
            "Bài viết tập trung vào trải nghiệm thực tế thay vì chỉ nhìn cấu hình, giúp bạn biết khi nào nên nâng cấp và khi nào nên chọn mẫu khác.",
            [
                ("Hiệu năng còn đủ mạnh cho nhiều năm", "Chip A17 Pro vẫn xử lý tốt tác vụ hằng ngày, quay video, chỉnh ảnh và chơi game phổ biến. Nếu bạn đang dùng iPhone đời cũ hơn từ 3 năm trở lên, khác biệt về tốc độ mở ứng dụng và camera sẽ rất rõ."),
                ("Camera phù hợp người hay quay chụp", "Cụm camera mạnh ở ảnh thiếu sáng, chân dung và quay video. Người bán hàng online, creator hoặc người thường xuyên du lịch sẽ khai thác được nhiều giá trị hơn so với người chỉ chụp cơ bản."),
                ("Khi nào chưa nên mua", "Nếu máy hiện tại vẫn pin tốt, camera đủ dùng và ngân sách bị kéo căng, bạn có thể chờ thêm đợt giảm giá. Chênh lệch trải nghiệm không phải lúc nào cũng đáng với chi phí nâng cấp."),
            ],
            [
                "Kiểm tra tình trạng pin và bảo hành khi mua máy đã qua sử dụng.",
                "Ưu tiên dung lượng 256GB trở lên nếu quay video nhiều.",
                "So sánh giá máy mới, máy trưng bày và máy cũ cùng chính sách đổi trả.",
            ],
            [
                ("iPhone 15 Pro Max còn dùng tốt mấy năm?", "Với nhu cầu phổ thông, máy vẫn đủ mạnh trong nhiều năm nếu pin và bộ nhớ còn phù hợp."),
                ("Nên mua 15 Pro Max hay đời mới hơn?", "Nếu cần giá tốt, 15 Pro Max hợp lý. Nếu muốn camera và pin mới nhất, hãy so sánh thêm đời mới hơn trước khi chốt."),
            ],
        ),
    },
    {
        "title": "Galaxy S24 Ultra và iPhone 15 Pro Max: chọn máy nào?",
        "subject": "Tin tức công nghệ",
        "subsubject": "Điện thoại",
        "image": "galaxy-s24-ultra-vs-iphone-15-pro-max.jpg",
        "featured": True,
        "description": "So sánh Galaxy S24 Ultra và iPhone 15 Pro Max theo màn hình, camera, hiệu năng, hệ sinh thái và nhu cầu sử dụng thực tế.",
        "content": article_html(
            "Galaxy S24 Ultra và iPhone 15 Pro Max",
            "Hai mẫu flagship hướng đến người dùng cao cấp nhưng triết lý sử dụng rất khác nhau. Chọn đúng hệ sinh thái sẽ quan trọng hơn vài thông số riêng lẻ.",
            [
                ("Màn hình và bút S Pen", "Galaxy S24 Ultra nổi bật với màn hình lớn, khả năng ghi chú và thao tác chính xác bằng S Pen. Đây là lợi thế cho người thường xuyên xử lý tài liệu, ghi chú hoặc chỉnh ảnh nhanh."),
                ("Video và hệ sinh thái", "iPhone 15 Pro Max mạnh ở quay video ổn định, AirDrop, iMessage, Apple Watch và MacBook. Nếu bạn đã dùng nhiều thiết bị Apple, trải nghiệm liền mạch là điểm cộng lớn."),
                ("Camera zoom và xử lý ảnh", "S24 Ultra linh hoạt ở zoom xa và ảnh sắc nét, còn iPhone có màu sắc ổn định, dễ dùng cho video và mạng xã hội. Nên chọn theo kiểu ảnh bạn chụp nhiều nhất."),
            ],
            [
                "Chọn iPhone nếu bạn ưu tiên video và hệ sinh thái Apple.",
                "Chọn Galaxy nếu bạn cần màn hình lớn, S Pen và zoom linh hoạt.",
                "So sánh giá sau khuyến mãi, quà tặng và chính sách bảo hành.",
            ],
            [
                ("Máy nào pin tốt hơn?", "Thời lượng pin phụ thuộc cách dùng, nhưng cả hai đều đủ cho một ngày làm việc với nhu cầu hỗn hợp."),
                ("Máy nào phù hợp bán hàng online?", "iPhone thuận tiện cho video và đăng mạng xã hội, Galaxy tiện khi cần màn hình lớn và ghi chú đơn hàng nhanh."),
            ],
        ),
    },
    {
        "title": "Top laptop cho sinh viên: tiêu chí chọn máy bền, nhẹ, đủ mạnh",
        "subject": "Tin tức công nghệ",
        "subsubject": "Laptop",
        "image": "top-laptop-cho-sinh-vien.jpg",
        "featured": True,
        "description": "Hướng dẫn chọn laptop cho sinh viên theo ngành học, cấu hình, cân nặng, pin, độ bền và ngân sách để dùng ổn định nhiều năm.",
        "content": article_html(
            "laptop cho sinh viên",
            "Một chiếc laptop tốt cho sinh viên cần cân bằng giữa giá, độ bền, pin và khả năng nâng cấp. Đừng chỉ chọn theo tên CPU hoặc thiết kế bên ngoài.",
            [
                ("Chọn cấu hình theo ngành học", "Sinh viên văn phòng, kinh tế và ngoại ngữ có thể ưu tiên máy mỏng nhẹ, RAM 16GB và SSD 512GB. Ngành thiết kế, kỹ thuật hoặc dữ liệu nên cân nhắc màn hình tốt và GPU phù hợp."),
                ("Cân nặng và pin quyết định trải nghiệm hằng ngày", "Máy dưới 1,5kg sẽ dễ mang đi học hơn. Pin thực tế từ 6 giờ trở lên giúp giảm phụ thuộc ổ cắm trong lớp học, thư viện hoặc quán cà phê."),
                ("Đừng bỏ qua bảo hành", "Bảo hành chính hãng, linh kiện dễ thay và trung tâm hỗ trợ gần nơi học giúp tiết kiệm nhiều thời gian khi máy gặp lỗi giữa kỳ thi hoặc đồ án."),
            ],
            [
                "RAM tối thiểu 16GB nếu muốn dùng lâu dài.",
                "SSD 512GB là mức dễ chịu cho tài liệu, ảnh và phần mềm học tập.",
                "Kiểm tra bàn phím, webcam, cổng kết nối và độ sáng màn hình.",
            ],
            [
                ("Sinh viên có nên mua laptop cũ?", "Có thể mua nếu kiểm tra kỹ pin, màn hình, bàn phím, SSD và có bảo hành rõ ràng."),
                ("Laptop gaming có phù hợp đi học?", "Phù hợp với ngành cần GPU, nhưng thường nặng và pin yếu hơn laptop mỏng nhẹ."),
            ],
        ),
    },
    {
        "title": "MacBook Pro M3 sau 1 tháng: hiệu năng, pin và ai nên mua",
        "subject": "Tin tức công nghệ",
        "subsubject": "Laptop",
        "image": "macbook-pro-m3-sau-1-thang.jpg",
        "featured": False,
        "description": "Đánh giá MacBook Pro M3 sau 1 tháng sử dụng: hiệu năng thực tế, màn hình, thời lượng pin, điểm mạnh và nhóm người dùng nên mua.",
        "content": article_html(
            "MacBook Pro M3",
            "MacBook Pro M3 không chỉ là nâng cấp cấu hình. Giá trị lớn nhất nằm ở hiệu năng ổn định, màn hình tốt và thời lượng pin phù hợp làm việc di động.",
            [
                ("Hiệu năng ổn định khi làm việc dài", "Máy xử lý tốt lập trình, chỉnh ảnh, dựng video vừa phải và làm việc đa nhiệm. Điểm đáng chú ý là hiệu năng ít tụt khi dùng pin, phù hợp người hay di chuyển."),
                ("Màn hình và loa là lợi thế thực tế", "Màn hình sáng, màu tốt và loa rõ giúp trải nghiệm họp online, xem nội dung và chỉnh ảnh đáng tin cậy hơn nhiều laptop phổ thông."),
                ("Ai nên cân nhắc kỹ", "Nếu bạn chỉ dùng trình duyệt, văn bản và bảng tính nhẹ, MacBook Air hoặc laptop Windows tốt có thể hợp lý hơn. Pro M3 phù hợp khi bạn thật sự cần màn hình, cổng kết nối và hiệu năng bền."),
            ],
            [
                "Chọn RAM đủ lớn ngay từ đầu vì khó nâng cấp.",
                "Ưu tiên SSD phù hợp dung lượng dự án hiện tại và 2-3 năm tới.",
                "Kiểm tra phần mềm chuyên ngành có hỗ trợ macOS hay không.",
            ],
            [
                ("MacBook Pro M3 có nóng không?", "Máy kiểm soát nhiệt tốt trong đa số tác vụ, nhưng vẫn nóng hơn khi render hoặc xử lý video nặng."),
                ("Có nên mua bản thấp nhất?", "Nên mua nếu nhu cầu vừa phải. Với công việc sáng tạo nặng, hãy cân nhắc RAM và SSD cao hơn."),
            ],
        ),
    },
    {
        "title": "Kinh nghiệm săn sale ngày đôi không bị mua hớ",
        "subject": "Mẹo mua sắm",
        "subsubject": "Săn khuyến mãi",
        "image": "kinh-nghiem-san-sale-ngay-doi.jpg",
        "featured": False,
        "description": "Kinh nghiệm săn sale ngày đôi: cách kiểm tra giá thật, voucher, phí vận chuyển, bảo hành và dấu hiệu khuyến mãi không đáng mua.",
        "content": article_html(
            "săn sale ngày đôi",
            "Ngày đôi có nhiều ưu đãi hấp dẫn nhưng cũng dễ khiến người mua chốt đơn vì cảm giác gấp. Mục tiêu là mua đúng món cần, đúng giá và đúng chính sách.",
            [
                ("Theo dõi giá trước ngày sale", "Hãy lưu sản phẩm vào danh sách yêu thích trước 1-2 tuần để biết giá nền. Nếu giá sale không thấp hơn đáng kể, voucher lớn cũng chưa chắc là món hời."),
                ("Tính tổng chi phí sau cùng", "Giá hiển thị chưa phải giá thật. Cần cộng phí vận chuyển, phụ phí thanh toán, điều kiện bảo hành và chi phí phụ kiện bắt buộc nếu có."),
                ("Đọc kỹ điều kiện đổi trả", "Một số deal giá sâu có điều kiện đổi trả hạn chế. Với điện thoại, laptop hoặc đồ điện tử, chính sách bảo hành quan trọng không kém mức giảm giá."),
            ],
            [
                "Đặt ngân sách tối đa trước khi vào app mua sắm.",
                "Ưu tiên shop có đánh giá thật, phản hồi rõ và bảo hành minh bạch.",
                "Chụp lại giá, voucher và cam kết bảo hành trước khi thanh toán.",
            ],
            [
                ("Có nên chờ flash sale?", "Nên chờ nếu không cần gấp, nhưng hãy kiểm tra số lượng và điều kiện để tránh bỏ lỡ deal tốt hơn."),
                ("Voucher lớn có luôn rẻ hơn không?", "Không. Voucher cần được so với giá nền và tổng chi phí sau cùng."),
            ],
        ),
    },
    {
        "title": "Cách so sánh giá sản phẩm trước khi mua online",
        "subject": "Mẹo mua sắm",
        "subsubject": "So sánh sản phẩm",
        "image": "cach-so-sanh-gia-san-pham-online.jpg",
        "featured": False,
        "description": "Cách so sánh giá sản phẩm online chính xác hơn bằng giá nền, cấu hình, bảo hành, phí giao hàng, đánh giá người mua và uy tín gian hàng.",
        "content": article_html(
            "so sánh giá sản phẩm online",
            "So sánh giá đúng không chỉ là chọn con số thấp nhất. Cần đặt giá trong cùng cấu hình, tình trạng hàng, thời gian bảo hành và độ tin cậy của người bán.",
            [
                ("So sánh cùng phiên bản", "Điện thoại và laptop có nhiều biến thể RAM, bộ nhớ, màu sắc hoặc thị trường phân phối. Hãy chắc chắn các lựa chọn đang so sánh là cùng phiên bản."),
                ("Bảo hành là một phần của giá", "Một sản phẩm rẻ hơn nhưng bảo hành ngắn, khó đổi trả hoặc không có hóa đơn có thể tốn kém hơn khi phát sinh lỗi."),
                ("Đọc đánh giá có chọn lọc", "Ưu tiên đánh giá có ảnh thật, thời gian sử dụng đủ lâu và phản hồi từ người bán. Tránh dựa hoàn toàn vào điểm sao trung bình."),
            ],
            [
                "Lập bảng so sánh giá, cấu hình, bảo hành và phí vận chuyển.",
                "Kiểm tra lịch sử giá nếu sàn hoặc công cụ hỗ trợ.",
                "Không chuyển khoản ngoài hệ thống nếu chưa xác minh người bán.",
            ],
            [
                ("Giá thấp nhất có nên mua ngay?", "Chỉ nên mua khi chính sách bảo hành, đổi trả và uy tín người bán đủ rõ."),
                ("Nên so sánh bao nhiêu nơi?", "Ít nhất 3 nơi bán để có mặt bằng giá hợp lý trước khi quyết định."),
            ],
        ),
    },
    {
        "title": "7 cách kéo dài tuổi thọ pin điện thoại",
        "subject": "Hướng dẫn sử dụng",
        "subsubject": "Bảo quản thiết bị",
        "image": "keo-dai-tuoi-tho-pin-dien-thoai.jpg",
        "featured": False,
        "description": "Hướng dẫn kéo dài tuổi thọ pin điện thoại bằng thói quen sạc đúng, kiểm soát nhiệt độ, ứng dụng nền, độ sáng màn hình và phụ kiện sạc.",
        "content": article_html(
            "kéo dài tuổi thọ pin điện thoại",
            "Pin xuống cấp là điều tự nhiên, nhưng thói quen sử dụng đúng có thể làm chậm quá trình chai pin và giữ trải nghiệm ổn định hơn.",
            [
                ("Tránh nhiệt độ cao", "Nhiệt là yếu tố làm pin xuống cấp nhanh. Không nên vừa sạc vừa chơi game nặng, đặt điện thoại dưới nắng hoặc để máy trong xe nóng."),
                ("Dùng sạc chất lượng", "Củ sạc và cáp đạt chuẩn giúp dòng điện ổn định hơn. Phụ kiện quá rẻ, không rõ nguồn gốc có thể gây nóng máy và giảm tuổi thọ pin."),
                ("Quản lý ứng dụng nền", "Ứng dụng chạy nền, định vị liên tục và thông báo dày đặc làm pin hao nhanh. Hãy tắt quyền không cần thiết và cập nhật ứng dụng thường xuyên."),
            ],
            [
                "Giữ pin trong khoảng 20-80% khi có thể.",
                "Bật sạc tối ưu nếu hệ điều hành hỗ trợ.",
                "Giảm độ sáng và tần số quét khi không cần hiệu năng cao.",
            ],
            [
                ("Có cần xả pin về 0% không?", "Không cần. Pin lithium hiện nay không cần xả cạn thường xuyên."),
                ("Sạc qua đêm có hại không?", "Máy hiện đại có cơ chế bảo vệ, nhưng vẫn nên bật sạc tối ưu và tránh để máy quá nóng."),
            ],
        ),
    },
    {
        "title": "Vệ sinh laptop đúng cách tại nhà không làm hỏng máy",
        "subject": "Hướng dẫn sử dụng",
        "subsubject": "Bảo quản thiết bị",
        "image": "ve-sinh-laptop-dung-cach-tai-nha.jpg",
        "featured": False,
        "description": "Hướng dẫn vệ sinh laptop tại nhà an toàn: làm sạch màn hình, bàn phím, khe tản nhiệt, cổng kết nối và những lỗi cần tránh.",
        "content": article_html(
            "vệ sinh laptop đúng cách",
            "Vệ sinh laptop định kỳ giúp máy mát hơn, bàn phím sạch hơn và giảm rủi ro bụi bẩn ảnh hưởng tới cổng kết nối. Quan trọng nhất là thao tác nhẹ và đúng dụng cụ.",
            [
                ("Chuẩn bị dụng cụ phù hợp", "Bạn cần khăn microfiber, cọ mềm, bóng thổi bụi và dung dịch vệ sinh màn hình phù hợp. Không xịt trực tiếp dung dịch lên màn hình hoặc bàn phím."),
                ("Làm sạch màn hình và bàn phím", "Tắt máy, rút sạc, lau màn hình theo một chiều bằng khăn ẩm nhẹ. Với bàn phím, nghiêng máy và dùng cọ mềm để lấy bụi giữa các phím."),
                ("Khi nào nên mang ra kỹ thuật", "Nếu máy nóng bất thường, quạt kêu lớn hoặc lâu chưa thay keo tản nhiệt, bạn nên nhờ kỹ thuật vệ sinh bên trong thay vì tự tháo nếu chưa có kinh nghiệm."),
            ],
            [
                "Luôn tắt máy và rút sạc trước khi vệ sinh.",
                "Không dùng cồn mạnh, khăn giấy thô hoặc nước lau kính thông thường.",
                "Không thổi khí quá mạnh vào khe tản nhiệt theo hướng làm kẹt quạt.",
            ],
            [
                ("Bao lâu nên vệ sinh laptop?", "Nên lau ngoài mỗi 1-2 tuần và kiểm tra vệ sinh bên trong sau 6-12 tháng tùy môi trường sử dụng."),
                ("Có nên tự tháo máy không?", "Chỉ nên tự tháo nếu bạn có dụng cụ và hiểu cấu trúc máy. Nếu không, hãy đem đến kỹ thuật viên."),
            ],
        ),
    },
]


def seed_posts(force_images=True):
    project_root = settings.BASE_DIR
    seed_images_folder = os.path.join(project_root, "static", "website", "img", "seed_posts")
    if force_images and not os.path.isdir(seed_images_folder):
        raise CommandError(f"Thư mục hình ảnh '{seed_images_folder}' không tồn tại.")

    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    request = MockRequest(user)

    subjects_by_title = {}
    subsubjects_by_key = {}
    for subject_title, subject_data in SUBJECT_CATALOG.items():
        subject, _ = Subject.objects.update_or_create(
            title=subject_title,
            defaults={"description": subject_data["description"]},
        )
        subjects_by_title[subject_title] = subject

        for subsubject_title, description in subject_data["subsubjects"].items():
            subsubject, _ = SubSubject.objects.update_or_create(
                subject=subject,
                title=subsubject_title,
                defaults={"description": description},
            )
            subsubjects_by_key[(subject_title, subsubject_title)] = subsubject

    current_titles = [post_data["title"] for post_data in SEO_POSTS]
    stale_titles = [title for title in LEGACY_POST_TITLES if title not in current_titles]
    if stale_titles:
        Post.objects.filter(title__in=stale_titles).delete()

    posts = []
    for index, post_data in enumerate(SEO_POSTS):
        subject = subjects_by_title[post_data["subject"]]
        subsubject = subsubjects_by_key[(post_data["subject"], post_data["subsubject"])]
        post, _ = Post.objects.get_or_create(title=post_data["title"])
        post.request = request
        post.subject = subject
        post.subsubject = subsubject
        post.description = post_data["description"]
        post.author = "PTcom"
        post.featured = post_data["featured"]
        post.is_sale = False
        post.price = None
        post.address = ""
        post.display_at = timezone.now() - timedelta(days=index * 3)

        image_path = os.path.join(seed_images_folder, post_data["image"])
        if force_images and not os.path.exists(image_path):
            raise CommandError(f"Thiếu ảnh seed cho bài viết: {image_path}")

        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                post.image.save(f"seed-post-{index + 1}-{post_data['image']}", File(image_file), save=False)

        post.save()
        Post.objects.filter(pk=post.pk).update(created_at=post.display_at, updated_at=timezone.now())
        PostContent.objects.update_or_create(
            post=post,
            defaults={"content": post_data["content"]},
        )
        posts.append(post)

    return posts


def run():
    seed_posts()


class Command(BaseCommand):
    help = "Seed bài viết SEO mẫu"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Không bắt buộc gắn ảnh seed vào bài viết.",
        )

    def handle(self, *args, **options):
        posts = seed_posts(force_images=not options["skip_images"])
        self.stdout.write(self.style.SUCCESS(f"Đã seed {len(posts)} bài viết SEO."))
