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


# Danh sách Subject/SubSubject và bài viết khớp với kế hoạch nội dung tại docs/content-plan/.
SUBJECT_CATALOG = {
    "Tin tức công nghệ": {
        "description": "Cập nhật xu hướng điện thoại, laptop và thiết bị thông minh đáng chú ý.",
        "subsubjects": {
            "Điện thoại": "Tin tức, đánh giá và kinh nghiệm chọn mua điện thoại.",
            "Laptop": "Gợi ý chọn laptop theo nhu cầu học tập, làm việc và sáng tạo.",
            "AI & Thiết bị thông minh": "Giải thích và đánh giá tính năng AI trên điện thoại, laptop và thiết bị thông minh.",
        },
    },
    "Mẹo mua sắm": {
        "description": "Kinh nghiệm mua hàng online, săn ưu đãi và so sánh sản phẩm trước khi chốt đơn.",
        "subsubjects": {
            "Săn khuyến mãi": "Cách đọc ưu đãi, voucher và lịch sale để mua đúng giá trị.",
            "So sánh sản phẩm": "Khung so sánh cấu hình, giá, bảo hành và chi phí sử dụng.",
            "Mua sắm livestream": "Kinh nghiệm mua hàng qua livestream và social commerce an toàn, đúng giá.",
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


def article_html(keyword, intro, sections, conclusion):
    section_html = "\n".join(
        f"<h2>{heading}</h2>\n<p>{body}</p>" for heading, body in sections
    )
    return f"""
    <p><strong>{keyword}</strong> là chủ đề được nhiều người quan tâm. {intro}</p>
    {section_html}
    <h2>Kết luận</h2>
    <p>{conclusion}</p>
    """


SEO_POSTS = [
    # ==== Tin tức công nghệ / Điện thoại ====
    {
        "title": "iPhone 15 Pro Max có đáng mua trong năm 2026?",
        "subject": "Tin tức công nghệ",
        "subsubject": "Điện thoại",
        "image": "iphone-15-pro-max-2026.jpg",
        "featured": True,
        "description": "Đánh giá iPhone 15 Pro Max trong năm 2026: hiệu năng, camera, pin, giá bán và nhóm người dùng nên nâng cấp để mua đúng nhu cầu.",
        "content": article_html(
            "iPhone 15 Pro Max có đáng mua",
            "Bài viết tập trung vào trải nghiệm thực tế để bạn biết khi nào nên nâng cấp.",
            [
                ("Hiệu năng vẫn đủ mạnh", "Chip A17 Pro xử lý tốt tác vụ hằng ngày, quay video và game phổ biến; nâng cấp từ máy 3 năm tuổi trở lên sẽ thấy khác biệt rõ."),
                ("Camera cho người hay quay chụp", "Máy mạnh ở ảnh thiếu sáng và quay video, phù hợp người bán hàng online và creator."),
                ("Khi nào chưa nên mua", "Nếu máy hiện tại còn tốt và ngân sách bị kéo căng, hãy chờ đợt giảm giá thay vì mua ngay."),
            ],
            "Ưu tiên bản 256GB trở lên, kiểm tra pin và bảo hành kỹ nếu mua máy đã qua sử dụng.",
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
            "Hai flagship có triết lý khác nhau; chọn đúng hệ sinh thái quan trọng hơn vài thông số lẻ.",
            [
                ("Màn hình và S Pen", "Galaxy nổi bật với màn hình lớn và S Pen, hợp người hay ghi chú và xử lý tài liệu."),
                ("Video và hệ sinh thái", "iPhone mạnh ở quay video ổn định và liên kết liền mạch với Apple Watch, MacBook."),
                ("Camera zoom", "S24 Ultra linh hoạt khi zoom xa, iPhone cho màu ổn định và dễ dùng cho mạng xã hội."),
            ],
            "Chọn iPhone nếu ưu tiên video và hệ sinh thái Apple; chọn Galaxy nếu cần màn hình lớn, S Pen và zoom linh hoạt.",
        ),
    },
    {
        "title": "Top 5 điện thoại tầm trung đáng mua nhất 2026",
        "subject": "Tin tức công nghệ",
        "subsubject": "Điện thoại",
        "image": "iphone-15-pro-max-2026.jpg",
        "featured": False,
        "description": "Gợi ý 5 điện thoại tầm trung đáng mua nhất 2026 theo tiêu chí hiệu năng, camera, pin và giá bán, giúp bạn chọn nhanh đúng nhu cầu.",
        "content": article_html(
            "điện thoại tầm trung đáng mua",
            "Phân khúc tầm trung hiện có hiệu năng và camera tiệm cận flagship với mức giá dễ chịu hơn nhiều.",
            [
                ("Tiêu chí chọn máy tầm trung", "Ưu tiên chip ổn định, RAM từ 8GB, pin từ 5000mAh và cam kết cập nhật phần mềm dài."),
                ("Nhóm thiên về camera", "Chọn máy có chống rung quang học và chế độ chụp đêm tốt nếu bạn hay chụp ảnh."),
                ("Nhóm thiên về pin và hiệu năng", "Người chơi game hoặc dùng cả ngày nên ưu tiên pin lớn và sạc nhanh trên 45W."),
            ],
            "Xác định nhu cầu chính trước rồi mới so giá; máy tầm trung tốt là máy cân bằng chứ không phải máy nhiều thông số nhất.",
        ),
    },
    {
        "title": "Điện thoại pin trâu: tiêu chí chọn và gợi ý theo ngân sách",
        "subject": "Tin tức công nghệ",
        "subsubject": "Điện thoại",
        "image": "galaxy-s24-ultra-vs-iphone-15-pro-max.jpg",
        "featured": False,
        "description": "Cách chọn điện thoại pin trâu theo dung lượng pin, chip tiết kiệm điện, màn hình và sạc nhanh, kèm gợi ý theo từng mức ngân sách.",
        "content": article_html(
            "điện thoại pin trâu",
            "Pin trâu không chỉ nằm ở số mAh mà còn ở chip, màn hình và phần mềm tối ưu.",
            [
                ("Dung lượng pin chỉ là một nửa", "Chip tiết kiệm điện và màn hình tối ưu quyết định thời gian dùng thực tế nhiều hơn con số mAh."),
                ("Sạc nhanh là tiêu chí đi kèm", "Máy pin lớn nên có sạc từ 33W trở lên để không mất quá lâu cho một lần sạc đầy."),
                ("Gợi ý theo ngân sách", "Tầm phổ thông ưu tiên pin 6000mAh; tầm trung trở lên cân bằng thêm camera và màn hình đẹp."),
            ],
            "Chọn máy có pin từ 5000mAh, chip tiết kiệm điện và sạc nhanh phù hợp; đọc thêm đánh giá thời gian onscreen thực tế trước khi chốt.",
        ),
    },
    {
        "title": "Điện thoại gập 2026: nên mua ngay hay chờ iPhone Fold?",
        "subject": "Tin tức công nghệ",
        "subsubject": "Điện thoại",
        "image": "galaxy-s24-ultra-vs-iphone-15-pro-max.jpg",
        "featured": True,
        "description": "Thị trường điện thoại gập 2026 tăng tốc với màn hình không nếp gấp và iPhone Fold sắp ra mắt: nên mua ngay hay chờ, ai hợp với máy gập.",
        "content": article_html(
            "điện thoại gập 2026",
            "Máy gập đang chuyển từ sản phẩm thử nghiệm thành xu hướng chính với màn hình gần như không còn nếp gấp.",
            [
                ("Vì sao 2026 là năm của máy gập", "Lượng máy gập bán ra dự kiến tăng hơn 40% khi các hãng lớn đều tham gia và Apple chuẩn bị ra mắt iPhone Fold."),
                ("Ai hợp với điện thoại gập", "Người cần màn hình lớn để đọc tài liệu, đa nhiệm và giải trí sẽ khai thác được nhiều giá trị nhất."),
                ("Nên mua ngay hay chờ", "Nếu không vội, chờ thế hệ có màn hình không nếp gấp và giá ổn định hơn sau khi iPhone Fold ra mắt là lựa chọn an toàn."),
            ],
            "Máy gập đáng cân nhắc nếu bạn thật sự dùng màn hình lớn hằng ngày; kiểm tra kỹ độ bền bản lề và chính sách bảo hành trước khi chốt.",
        ),
    },
    # ==== Tin tức công nghệ / Laptop ====
    {
        "title": "Top laptop cho sinh viên: tiêu chí chọn máy bền, nhẹ, đủ mạnh",
        "subject": "Tin tức công nghệ",
        "subsubject": "Laptop",
        "image": "top-laptop-cho-sinh-vien.jpg",
        "featured": True,
        "description": "Hướng dẫn chọn laptop cho sinh viên theo ngành học, cấu hình, cân nặng, pin, độ bền và ngân sách để dùng ổn định nhiều năm.",
        "content": article_html(
            "laptop cho sinh viên",
            "Laptop tốt cho sinh viên cần cân bằng giá, độ bền, pin và khả năng nâng cấp.",
            [
                ("Chọn cấu hình theo ngành học", "Ngành văn phòng ưu tiên máy mỏng nhẹ RAM 16GB; ngành thiết kế, kỹ thuật cần màn hình tốt và GPU phù hợp."),
                ("Cân nặng và pin", "Máy dưới 1,5kg và pin thực tế từ 6 giờ giúp việc mang đi học thoải mái hơn."),
                ("Đừng bỏ qua bảo hành", "Bảo hành chính hãng và trung tâm hỗ trợ gần nơi học tiết kiệm nhiều thời gian khi máy gặp lỗi."),
            ],
            "RAM tối thiểu 16GB, SSD 512GB và kiểm tra kỹ bàn phím, màn hình, cổng kết nối trước khi mua.",
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
            "Giá trị lớn nhất của máy nằm ở hiệu năng ổn định, màn hình tốt và pin phù hợp làm việc di động.",
            [
                ("Hiệu năng ổn định", "Máy xử lý tốt lập trình, chỉnh ảnh và đa nhiệm; hiệu năng ít tụt khi dùng pin."),
                ("Màn hình và loa là lợi thế", "Màn hình sáng, màu chuẩn và loa rõ giúp họp online lẫn chỉnh ảnh đáng tin cậy hơn."),
                ("Ai nên cân nhắc kỹ", "Nếu chỉ dùng trình duyệt và văn bản nhẹ, MacBook Air hoặc laptop Windows tốt sẽ hợp lý hơn."),
            ],
            "Chọn RAM và SSD đủ lớn ngay từ đầu vì máy khó nâng cấp, và kiểm tra phần mềm chuyên ngành có hỗ trợ macOS.",
        ),
    },
    {
        "title": "Laptop văn phòng dưới 20 triệu: gợi ý cấu hình đáng tiền",
        "subject": "Tin tức công nghệ",
        "subsubject": "Laptop",
        "image": "top-laptop-cho-sinh-vien.jpg",
        "featured": False,
        "description": "Gợi ý laptop văn phòng dưới 20 triệu với cấu hình đáng tiền: CPU, RAM, SSD, màn hình và bảo hành phù hợp nhu cầu làm việc hằng ngày.",
        "content": article_html(
            "laptop văn phòng dưới 20 triệu",
            "Tầm giá này đủ để có một chiếc máy mỏng nhẹ, bền và dùng mượt nhiều năm nếu chọn đúng cấu hình.",
            [
                ("Cấu hình nên có", "CPU tiết kiệm điện thế hệ mới, RAM 16GB và SSD 512GB là mức chuẩn cho công việc văn phòng."),
                ("Màn hình và bàn phím", "Ưu tiên màn hình từ Full HD độ sáng tốt và bàn phím gõ êm vì bạn dùng chúng cả ngày."),
                ("Những thứ có thể đánh đổi", "Card đồ họa rời và màn hình cảm ứng thường không cần thiết cho nhu cầu văn phòng."),
            ],
            "Chốt máy có cấu hình chuẩn văn phòng, bảo hành chính hãng rõ ràng và cân nặng phù hợp việc di chuyển của bạn.",
        ),
    },
    {
        "title": "Nên mua laptop gaming hay laptop mỏng nhẹ? Cách chọn đúng nhu cầu",
        "subject": "Tin tức công nghệ",
        "subsubject": "Laptop",
        "image": "macbook-pro-m3-sau-1-thang.jpg",
        "featured": False,
        "description": "So sánh laptop gaming và laptop mỏng nhẹ về hiệu năng, cân nặng, pin và chi phí để bạn chọn đúng dòng máy theo nhu cầu thật.",
        "content": article_html(
            "laptop gaming hay laptop mỏng nhẹ",
            "Hai dòng máy phục vụ hai kiểu sử dụng khác nhau; chọn sai dòng sẽ tốn tiền cho thứ không dùng đến.",
            [
                ("Laptop gaming hợp với ai", "Người cần GPU cho game, đồ họa hoặc dựng video; đổi lại máy nặng và pin ngắn hơn."),
                ("Laptop mỏng nhẹ hợp với ai", "Người di chuyển nhiều, làm việc văn phòng và cần pin cả ngày sẽ thấy giá trị rõ nhất."),
                ("Tính tổng chi phí", "Máy gaming thường cần thêm balo, sạc to và chuột rời; máy mỏng nhẹ có thể cần hub mở rộng cổng."),
            ],
            "Liệt kê phần mềm bạn dùng hằng ngày trước; nếu không có ứng dụng cần GPU rời thì laptop mỏng nhẹ là lựa chọn hợp lý hơn.",
        ),
    },
    # ==== Tin tức công nghệ / AI & Thiết bị thông minh ====
    {
        "title": "Laptop AI là gì? Có đáng mua trong năm 2026?",
        "subject": "Tin tức công nghệ",
        "subsubject": "AI & Thiết bị thông minh",
        "image": "macbook-pro-m3-sau-1-thang.jpg",
        "featured": True,
        "description": "Giải thích laptop AI và NPU dễ hiểu: khác gì laptop thường, những tính năng thực sự hữu ích và ai nên mua laptop AI trong năm 2026.",
        "content": article_html(
            "laptop AI",
            "Laptop AI là dòng máy có chip NPU chuyên xử lý tác vụ trí tuệ nhân tạo ngay trên máy, không cần gửi dữ liệu lên mạng.",
            [
                ("Khác gì laptop thường", "NPU xử lý các tác vụ AI như làm mờ phông họp online, tách giọng nói và tóm tắt văn bản mà không làm nặng CPU, giúp máy mát và tiết kiệm pin hơn."),
                ("Tính năng thực sự hữu ích", "Đáng giá nhất là khử ồn cuộc họp, dịch phụ đề trực tiếp và tìm kiếm nội dung trong máy; các tính năng còn lại phần lớn vẫn đang hoàn thiện."),
                ("Ai nên mua trong 2026", "Người mua máy mới dùng 4-5 năm nên chọn máy có NPU để không lỗi thời; người có laptop còn tốt chưa cần nâng cấp chỉ vì mác AI."),
            ],
            "Chọn laptop AI khi bạn đằng nào cũng cần mua máy mới; đừng trả thêm quá nhiều chỉ cho nhãn AI mà hãy so hiệu năng, pin và màn hình như thường lệ.",
        ),
    },
    {
        "title": "NPU trên điện thoại dùng để làm gì? Giải thích dễ hiểu",
        "subject": "Tin tức công nghệ",
        "subsubject": "AI & Thiết bị thông minh",
        "image": "iphone-15-pro-max-2026.jpg",
        "featured": False,
        "description": "NPU trên điện thoại là gì và dùng để làm gì: xử lý ảnh, dịch offline, trợ lý ảo và cách đánh giá sức mạnh AI khi chọn mua máy mới.",
        "content": article_html(
            "NPU trên điện thoại",
            "NPU là bộ xử lý chuyên cho tác vụ AI, hoạt động song song với CPU và GPU trong chip điện thoại.",
            [
                ("NPU làm gì hằng ngày", "Xử lý ảnh chụp đêm, nhận diện khuôn mặt, dịch offline và trợ lý ảo đều chạy qua NPU nhanh và tiết kiệm pin hơn CPU."),
                ("Vì sao AI chạy trên máy tốt hơn", "Xử lý tại chỗ giúp phản hồi nhanh, dùng được khi không có mạng và dữ liệu cá nhân không phải gửi lên máy chủ."),
                ("Cách đánh giá khi mua máy", "Đừng chỉ nhìn số TOPS quảng cáo; hãy xem tính năng AI cụ thể máy hỗ trợ và thời gian hãng cam kết cập nhật phần mềm."),
            ],
            "NPU ngày càng quan trọng nhưng chỉ hữu ích qua tính năng cụ thể; khi chọn máy, hãy thử trực tiếp các tính năng AI bạn định dùng thay vì tin thông số.",
        ),
    },
    {
        "title": "Tính năng AI trên điện thoại 2026: cái nào thực sự hữu ích?",
        "subject": "Tin tức công nghệ",
        "subsubject": "AI & Thiết bị thông minh",
        "image": "galaxy-s24-ultra-vs-iphone-15-pro-max.jpg",
        "featured": False,
        "description": "Điểm qua tính năng AI trên điện thoại 2026: xóa vật thể, dịch cuộc gọi, tóm tắt văn bản và cách phân biệt tính năng hữu ích với quảng cáo.",
        "content": article_html(
            "tính năng AI trên điện thoại",
            "Các hãng đưa AI vào mọi tính năng, nhưng giá trị thực tế giữa chúng chênh lệch rất lớn.",
            [
                ("Nhóm đáng dùng hằng ngày", "Xóa vật thể trong ảnh, dịch cuộc gọi trực tiếp, tóm tắt ghi âm và gõ phím thông minh là những tính năng tiết kiệm thời gian rõ rệt."),
                ("Nhóm nghe hay nhưng ít dùng", "Tạo ảnh nghệ thuật, viết lại tin nhắn theo phong cách hay hình nền AI thường chỉ vui lúc đầu rồi bị bỏ quên."),
                ("Lưu ý về quyền riêng tư", "Kiểm tra tính năng nào xử lý trên máy và tính năng nào gửi dữ liệu lên máy chủ trước khi cấp quyền truy cập ảnh, tin nhắn."),
            ],
            "Khi chọn máy vì AI, hãy liệt kê 3 tính năng bạn chắc chắn dùng hằng tuần rồi thử trực tiếp tại cửa hàng; đừng mua vì danh sách tính năng dài.",
        ),
    },
    # ==== Mẹo mua sắm / Săn khuyến mãi ====
    {
        "title": "Kinh nghiệm săn sale ngày đôi không bị mua hớ",
        "subject": "Mẹo mua sắm",
        "subsubject": "Săn khuyến mãi",
        "image": "kinh-nghiem-san-sale-ngay-doi.jpg",
        "featured": False,
        "description": "Kinh nghiệm săn sale ngày đôi: cách kiểm tra giá thật, voucher, phí vận chuyển, bảo hành và dấu hiệu khuyến mãi không đáng mua.",
        "content": article_html(
            "săn sale ngày đôi",
            "Mục tiêu là mua đúng món cần, đúng giá và đúng chính sách thay vì chốt đơn theo cảm giác gấp.",
            [
                ("Theo dõi giá trước ngày sale", "Lưu sản phẩm trước 1-2 tuần để biết giá nền; giá sale không thấp hơn đáng kể thì chưa phải món hời."),
                ("Tính tổng chi phí sau cùng", "Cộng phí vận chuyển, phụ phí thanh toán và điều kiện bảo hành vào giá hiển thị."),
                ("Đọc kỹ điều kiện đổi trả", "Deal giá sâu đôi khi kèm điều kiện đổi trả hạn chế, đặc biệt với đồ điện tử."),
            ],
            "Đặt ngân sách tối đa trước khi mở app, ưu tiên shop uy tín và chụp lại giá cùng cam kết bảo hành trước khi thanh toán.",
        ),
    },
    {
        "title": "Cách dùng voucher và mã giảm giá để mua đồ công nghệ rẻ hơn",
        "subject": "Mẹo mua sắm",
        "subsubject": "Săn khuyến mãi",
        "image": "kinh-nghiem-san-sale-ngay-doi.jpg",
        "featured": False,
        "description": "Hướng dẫn dùng voucher và mã giảm giá đúng cách: thứ tự áp mã, điều kiện đơn tối thiểu và cách cộng dồn ưu đãi khi mua đồ công nghệ.",
        "content": article_html(
            "cách dùng voucher mã giảm giá",
            "Dùng voucher đúng cách có thể giảm đáng kể tổng chi phí, nhưng cần hiểu điều kiện của từng loại mã.",
            [
                ("Phân loại mã giảm giá", "Mã của sàn, mã của shop và mã vận chuyển thường cộng dồn được với nhau nếu áp đúng thứ tự."),
                ("Chú ý điều kiện đơn tối thiểu", "Đừng mua thêm đồ không cần chỉ để đạt mức tối thiểu; phần mua thêm có thể ăn hết phần giảm."),
                ("Canh khung giờ nhả mã", "Nhiều mã giá trị cao chỉ mở vào khung giờ cố định; lưu mã trước và đặt nhắc để không bỏ lỡ."),
            ],
            "So sánh giá sau khi áp toàn bộ mã giữa vài gian hàng rồi mới chốt; mã lớn trên giá đã bị đẩy cao không phải là ưu đãi thật.",
        ),
    },
    {
        "title": "Flash sale là gì? Mẹo canh flash sale thành công",
        "subject": "Mẹo mua sắm",
        "subsubject": "Săn khuyến mãi",
        "image": "kinh-nghiem-san-sale-ngay-doi.jpg",
        "featured": False,
        "description": "Flash sale là gì và cách canh flash sale thành công: chuẩn bị trước giờ mở bán, kiểm tra giá nền và tránh bẫy giảm giá ảo.",
        "content": article_html(
            "flash sale",
            "Flash sale là đợt giảm giá sâu trong thời gian ngắn với số lượng giới hạn, đòi hỏi chuẩn bị trước để mua kịp.",
            [
                ("Chuẩn bị trước giờ mở bán", "Thêm sản phẩm vào giỏ, lưu địa chỉ và phương thức thanh toán sẵn để thao tác nhanh nhất."),
                ("Kiểm tra giá nền", "So mức giá flash sale với giá bán những tuần trước để chắc chắn mức giảm là thật."),
                ("Tránh tâm lý sợ bỏ lỡ", "Số lượng giới hạn dễ khiến bạn mua món không cần; chỉ canh những món đã nằm trong kế hoạch."),
            ],
            "Flash sale đáng săn khi bạn đã biết giá nền và thực sự cần món hàng; nếu lỡ đợt này, gần như luôn có đợt sau.",
        ),
    },
    {
        "title": "Có nên mua laptop, điện thoại ngay trước đợt tăng giá 2026?",
        "subject": "Mẹo mua sắm",
        "subsubject": "Săn khuyến mãi",
        "image": "kinh-nghiem-san-sale-ngay-doi.jpg",
        "featured": False,
        "description": "Giá laptop và điện thoại 2026 được dự báo tăng 13–17% do khan hiếm chip nhớ: khi nào nên mua ngay, khi nào nên chờ và cách mua đúng giá.",
        "content": article_html(
            "giá laptop điện thoại tăng 2026",
            "Chip nhớ đang bị các trung tâm dữ liệu AI gom mạnh, kéo giá linh kiện và giá thiết bị tiêu dùng tăng theo.",
            [
                ("Vì sao giá tăng", "RAM và bộ nhớ flash khan hiếm do nhu cầu AI khiến giá máy tính dự báo tăng khoảng 17% và điện thoại khoảng 13% trong năm 2026."),
                ("Khi nào nên mua ngay", "Nếu máy hiện tại đã yếu hoặc bạn có kế hoạch mua trong vài tháng tới, chốt sớm ở đợt khuyến mãi gần nhất thường lợi hơn chờ."),
                ("Khi nào nên chờ", "Máy hiện tại còn dùng tốt thì không cần mua vì sợ tăng giá; giá có thể hạ nhiệt khi nguồn cung chip nhớ cân bằng lại."),
            ],
            "Đừng mua theo tâm lý hoảng loạn: so giá nền vài tuần gần nhất, tận dụng đợt sale lớn và chỉ mua khi nhu cầu là có thật.",
        ),
    },
    # ==== Mẹo mua sắm / So sánh sản phẩm ====
    {
        "title": "Cách so sánh giá sản phẩm trước khi mua online",
        "subject": "Mẹo mua sắm",
        "subsubject": "So sánh sản phẩm",
        "image": "cach-so-sanh-gia-san-pham-online.jpg",
        "featured": False,
        "description": "Cách so sánh giá sản phẩm online chính xác hơn bằng giá nền, cấu hình, bảo hành, phí giao hàng, đánh giá người mua và uy tín gian hàng.",
        "content": article_html(
            "so sánh giá sản phẩm online",
            "So sánh giá đúng không chỉ là chọn con số thấp nhất mà phải cùng cấu hình, bảo hành và độ tin cậy người bán.",
            [
                ("So sánh cùng phiên bản", "Điện thoại, laptop có nhiều biến thể RAM, bộ nhớ và thị trường; hãy chắc các lựa chọn là cùng phiên bản."),
                ("Bảo hành là một phần của giá", "Sản phẩm rẻ hơn nhưng bảo hành ngắn hoặc khó đổi trả có thể tốn kém hơn khi phát sinh lỗi."),
                ("Đọc đánh giá có chọn lọc", "Ưu tiên đánh giá có ảnh thật và thời gian dùng đủ lâu thay vì chỉ nhìn điểm sao trung bình."),
            ],
            "Lập bảng so sánh giá, cấu hình, bảo hành ở ít nhất 3 nơi bán và không chuyển khoản ngoài hệ thống khi chưa xác minh người bán.",
        ),
    },
    {
        "title": "Hàng chính hãng, hàng xách tay và hàng cũ: nên chọn loại nào?",
        "subject": "Mẹo mua sắm",
        "subsubject": "So sánh sản phẩm",
        "image": "cach-so-sanh-gia-san-pham-online.jpg",
        "featured": False,
        "description": "So sánh hàng chính hãng, hàng xách tay và hàng cũ về giá, bảo hành, rủi ro và trường hợp nên chọn từng loại khi mua đồ công nghệ.",
        "content": article_html(
            "hàng chính hãng và hàng xách tay",
            "Mỗi nguồn hàng có mức giá và rủi ro khác nhau; hiểu rõ khác biệt giúp bạn không trả giá đắt cho sự yên tâm không cần thiết hoặc rẻ mà rủi ro cao.",
            [
                ("Hàng chính hãng", "Giá cao nhất nhưng bảo hành đầy đủ tại Việt Nam; phù hợp thiết bị đắt tiền dùng lâu dài."),
                ("Hàng xách tay", "Giá tốt hơn nhưng bảo hành hạn chế; chỉ nên mua ở nơi uy tín và chấp nhận rủi ro sửa chữa."),
                ("Hàng cũ", "Tiết kiệm nhất nếu kiểm tra kỹ pin, màn hình, nguồn gốc và còn chính sách bao test đổi trả."),
            ],
            "Thiết bị giá trị cao nên ưu tiên chính hãng; hàng xách tay và hàng cũ chỉ đáng mua khi chênh lệch giá đủ lớn và nơi bán minh bạch.",
        ),
    },
    {
        "title": "Cách đọc đánh giá sản phẩm để tránh mua nhầm hàng kém chất lượng",
        "subject": "Mẹo mua sắm",
        "subsubject": "So sánh sản phẩm",
        "image": "cach-so-sanh-gia-san-pham-online.jpg",
        "featured": False,
        "description": "Cách đọc đánh giá sản phẩm hiệu quả: nhận diện review ảo, ưu tiên đánh giá có ảnh thật và đối chiếu phản hồi của người bán.",
        "content": article_html(
            "cách đọc đánh giá sản phẩm",
            "Điểm sao trung bình dễ bị làm đẹp; giá trị thật nằm ở nội dung từng đánh giá và cách người bán phản hồi.",
            [
                ("Nhận diện review ảo", "Cảnh giác với loạt đánh giá 5 sao ngắn, đăng dồn trong vài ngày và không có ảnh thật."),
                ("Ưu tiên đánh giá chi tiết", "Đánh giá có ảnh chụp thật, nêu cả ưu lẫn nhược điểm sau thời gian dùng đủ lâu đáng tin hơn."),
                ("Xem cách người bán phản hồi", "Shop trả lời khiếu nại rõ ràng, có hướng xử lý cụ thể thường đáng tin hơn shop im lặng."),
            ],
            "Đọc kỹ các đánh giá 1-3 sao trước tiên vì chúng cho biết rủi ro thật; kết hợp với uy tín gian hàng trước khi quyết định.",
        ),
    },
    # ==== Mẹo mua sắm / Mua sắm livestream ====
    {
        "title": "Mua hàng qua livestream: mẹo tránh bị chốt đơn theo cảm xúc",
        "subject": "Mẹo mua sắm",
        "subsubject": "Mua sắm livestream",
        "image": "kinh-nghiem-san-sale-ngay-doi.jpg",
        "featured": False,
        "description": "Mẹo mua hàng qua livestream tỉnh táo: đặt ngân sách trước, kiểm tra giá nền, đọc chính sách đổi trả và tránh hiệu ứng khan hiếm ảo.",
        "content": article_html(
            "mua hàng qua livestream",
            "Livestream tạo cảm giác gấp gáp bằng đếm ngược và số lượng giới hạn, khiến người xem dễ chốt đơn ngoài kế hoạch.",
            [
                ("Đặt ngân sách trước khi vào live", "Quyết định số tiền tối đa và món cần mua trước khi xem; mọi thứ ngoài danh sách chỉ nên lưu lại để cân nhắc sau."),
                ("Nhận diện hiệu ứng khan hiếm ảo", "Câu 'chỉ còn vài suất' lặp lại nhiều phiên là dấu hiệu tạo áp lực; hàng thật sự hết sẽ được gỡ khỏi giỏ live."),
                ("Kiểm tra trước khi chốt", "Mở trang sản phẩm xem giá gốc, đánh giá và chính sách đổi trả thay vì chỉ nghe người bán nói trên sóng."),
            ],
            "Xem live để tham khảo và lấy voucher, nhưng quyết định mua nên dựa trên giá nền và nhu cầu thật; đơn hàng tốt không cần chốt trong 30 giây.",
        ),
    },
    {
        "title": "So sánh giá trên livestream và giá trên sàn: cách kiểm tra nhanh",
        "subject": "Mẹo mua sắm",
        "subsubject": "Mua sắm livestream",
        "image": "cach-so-sanh-gia-san-pham-online.jpg",
        "featured": False,
        "description": "Cách kiểm tra nhanh giá trên livestream so với giá trên sàn và tại shop: giá nền, voucher độc quyền live và những chiêu đẩy giá cần biết.",
        "content": article_html(
            "so sánh giá livestream",
            "Giá trên live không phải lúc nào cũng rẻ nhất; đôi khi giá gốc bị đẩy lên trước để mức giảm trông sâu hơn.",
            [
                ("Kiểm tra giá nền trong 2 phút", "Tìm đúng mã sản phẩm trên sàn và vài shop khác khi live đang chạy; giá live tốt thật phải thấp hơn giá nền sau voucher."),
                ("Voucher độc quyền live", "Nhiều deal live chỉ rẻ hơn nhờ voucher giới hạn; kiểm tra voucher đó áp cho phiên bản nào và có điều kiện gì kèm theo."),
                ("Chiêu đẩy giá cần biết", "So giá hôm nay với lịch sử giá vài tuần trước nếu công cụ hỗ trợ; mức giảm so với giá vừa bị đẩy lên không phải ưu đãi thật."),
            ],
            "Luôn so giá live với giá nền cùng phiên bản trước khi chốt; nếu chênh lệch không đáng kể, mua trên sàn thường dễ đổi trả và đối chiếu hơn.",
        ),
    },
    {
        "title": "Mua hàng trên TikTok Shop an toàn: những điều cần kiểm tra",
        "subject": "Mẹo mua sắm",
        "subsubject": "Mua sắm livestream",
        "image": "cach-so-sanh-gia-san-pham-online.jpg",
        "featured": False,
        "description": "Hướng dẫn mua hàng trên TikTok Shop an toàn: chọn shop uy tín, kiểm tra đánh giá, chính sách đổi trả và xử lý khi hàng không đúng mô tả.",
        "content": article_html(
            "mua hàng TikTok Shop an toàn",
            "TikTok Shop tăng trưởng rất nhanh nhưng chất lượng gian hàng không đồng đều, nên khâu kiểm tra trước khi mua càng quan trọng.",
            [
                ("Chọn shop uy tín", "Ưu tiên gian hàng chính hãng hoặc shop có điểm đánh giá cao, lượng bán ổn định và phản hồi khiếu nại rõ ràng."),
                ("Kiểm tra trước khi đặt", "Đọc đánh giá có ảnh thật, xem kỹ mô tả phiên bản và chụp lại cam kết của người bán trên live để làm bằng chứng."),
                ("Xử lý khi hàng không đúng mô tả", "Quay video mở hộp, khiếu nại qua kênh chính thức của sàn trong thời hạn đổi trả thay vì chỉ nhắn riêng cho shop."),
            ],
            "Mua qua kênh chính thức của sàn để được bảo vệ đơn hàng; video mở hộp và ảnh chụp cam kết trên live là bằng chứng tốt nhất khi cần khiếu nại.",
        ),
    },
    # ==== Hướng dẫn sử dụng / Bảo quản thiết bị ====
    {
        "title": "7 cách kéo dài tuổi thọ pin điện thoại",
        "subject": "Hướng dẫn sử dụng",
        "subsubject": "Bảo quản thiết bị",
        "image": "keo-dai-tuoi-tho-pin-dien-thoai.jpg",
        "featured": False,
        "description": "Hướng dẫn kéo dài tuổi thọ pin điện thoại bằng thói quen sạc đúng, kiểm soát nhiệt độ, ứng dụng nền, độ sáng màn hình và phụ kiện sạc.",
        "content": article_html(
            "kéo dài tuổi thọ pin điện thoại",
            "Pin xuống cấp là tự nhiên, nhưng thói quen đúng sẽ làm chậm quá trình chai pin rõ rệt.",
            [
                ("Tránh nhiệt độ cao", "Không vừa sạc vừa chơi game nặng, không để máy dưới nắng hoặc trong xe nóng."),
                ("Dùng sạc chất lượng", "Củ sạc và cáp đạt chuẩn cho dòng điện ổn định; phụ kiện trôi nổi dễ gây nóng máy."),
                ("Quản lý ứng dụng nền", "Tắt quyền định vị và thông báo không cần thiết để giảm hao pin ngầm."),
            ],
            "Giữ pin trong khoảng 20-80% khi có thể, bật sạc tối ưu và giảm độ sáng khi không cần hiệu năng cao.",
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
            "Vệ sinh định kỳ giúp máy mát hơn và bền hơn; quan trọng nhất là thao tác nhẹ và đúng dụng cụ.",
            [
                ("Chuẩn bị dụng cụ phù hợp", "Dùng khăn microfiber, cọ mềm và bóng thổi bụi; không xịt dung dịch trực tiếp lên màn hình."),
                ("Làm sạch màn hình và bàn phím", "Tắt máy, rút sạc, lau màn hình theo một chiều và dùng cọ mềm lấy bụi giữa các phím."),
                ("Khi nào nên mang ra kỹ thuật", "Máy nóng bất thường hoặc lâu chưa thay keo tản nhiệt thì nên nhờ kỹ thuật vệ sinh bên trong."),
            ],
            "Lau ngoài mỗi 1-2 tuần, vệ sinh sâu sau 6-12 tháng và không tự tháo máy nếu chưa có kinh nghiệm.",
        ),
    },
    {
        "title": "Cách bảo quản điện thoại khi đi mưa và môi trường ẩm",
        "subject": "Hướng dẫn sử dụng",
        "subsubject": "Bảo quản thiết bị",
        "image": "keo-dai-tuoi-tho-pin-dien-thoai.jpg",
        "featured": False,
        "description": "Cách bảo quản điện thoại khi đi mưa và trong môi trường ẩm: chống nước đúng cách, xử lý khi máy dính nước và phụ kiện nên dùng.",
        "content": article_html(
            "bảo quản điện thoại khi đi mưa",
            "Chuẩn chống nước không đồng nghĩa với miễn nhiễm; hơi ẩm tích tụ lâu ngày vẫn gây hại cho máy.",
            [
                ("Phòng ngừa khi đi mưa", "Dùng túi chống nước hoặc ngăn kín trong balo; hạn chế nghe gọi trực tiếp dưới mưa."),
                ("Xử lý khi máy dính nước", "Tắt máy ngay, lau khô, không sạc và không dùng máy sấy nóng; để máy khô tự nhiên nơi thoáng."),
                ("Môi trường ẩm lâu dài", "Tránh để máy trong phòng tắm hoặc nơi ẩm thấp; gói hút ẩm trong hộp đựng giúp bảo quản tốt hơn."),
            ],
            "Đừng chủ quan với chuẩn kháng nước; nếu máy vào nước và có dấu hiệu bất thường, hãy mang đến kỹ thuật sớm.",
        ),
    },
    {
        "title": "Sạc laptop đúng cách: những thói quen giúp pin bền hơn",
        "subject": "Hướng dẫn sử dụng",
        "subsubject": "Bảo quản thiết bị",
        "image": "ve-sinh-laptop-dung-cach-tai-nha.jpg",
        "featured": False,
        "description": "Hướng dẫn sạc laptop đúng cách: mức pin nên duy trì, dùng sạc chính hãng, cắm sạc liên tục có hại không và cách hạn chế chai pin.",
        "content": article_html(
            "sạc laptop đúng cách",
            "Pin laptop khó thay hơn điện thoại nên thói quen sạc đúng càng quan trọng để giữ máy bền.",
            [
                ("Mức pin nên duy trì", "Giữ pin trong khoảng 20-80% và bật giới hạn sạc nếu máy hỗ trợ khi cắm điện thường xuyên."),
                ("Cắm sạc liên tục có hại không", "Máy đời mới có cơ chế bảo vệ, nhưng nhiệt độ cao khi vừa sạc vừa chạy nặng vẫn làm pin nhanh chai."),
                ("Dùng đúng củ sạc", "Sạc chính hãng hoặc đạt chuẩn công suất giúp dòng điện ổn định và an toàn cho cả pin lẫn mainboard."),
            ],
            "Duy trì mức pin hợp lý, giữ máy thoáng mát khi sạc và kiểm tra tình trạng pin định kỳ bằng công cụ của hệ điều hành.",
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
        post.author = "eApp Blog"
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
    help = "Seed bài viết SEO mẫu theo kế hoạch nội dung docs/content-plan/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Không bắt buộc gắn ảnh seed vào bài viết.",
        )

    def handle(self, *args, **options):
        posts = seed_posts(force_images=not options["skip_images"])
        self.stdout.write(self.style.SUCCESS(f"Đã seed {len(posts)} bài viết SEO."))
