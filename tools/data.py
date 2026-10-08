# -*- coding: utf-8 -*-
"""Dữ liệu dùng chung của website: thông tin pháp nhân, menu, lĩnh vực dịch vụ, bài viết.

Nội dung lĩnh vực dịch vụ được chuyển từ website cũ (willmichco/Website).
Sửa nội dung tại đây rồi chạy:  python3 tools/build.py

Giọng văn thống nhất trên toàn website: xưng "luật sư", gọi người đọc là "anh chị";
câu ngắn, từ ngữ đời thường; dẫn điều luật khi đưa ra một khẳng định pháp lý.
Không hứa hẹn kết quả (Quy tắc 9.1.6 Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư).
"""

# ---------------------------------------------------------------------------
# Cấu hình tên miền.
# SITE_URL là tên miền chính (canonical): mọi canonical, og:url, sitemap, robots.txt, schema
# đều sinh từ đây. Website hiện chạy song song ở hai nơi:
#   - https://luat-su-nam-phap-ly.willmich-co.chatgpt.site  (bản chính, canonical)
#   - https://willmichco.github.io/luatsunam/               (bản sao; canonical trỏ về bản chính)
# BASE_PATH là thư mục gốc của website trên máy chủ, chỉ dùng cho trang 404.html
# (GitHub Pages phục vụ trang này ở mọi độ sâu đường dẫn nên không dùng được đường dẫn tương đối).
#
# Khi đã mua và trỏ DNS tên miền lsn.vn (CHƯA đổi trước khi lsn.vn truy cập được, vì canonical
# trỏ tới tên miền không hoạt động sẽ khiến Google bỏ qua hoặc gỡ trang khỏi kết quả):
#   1. SITE_URL = "https://lsn.vn", BASE_PATH = "/"
#   2. python3 tools/build.py && python3 tools/check_seo.py
#   3. Xem README, mục "Chuyển sang tên miền lsn.vn".
# ---------------------------------------------------------------------------
SITE_URL = "https://luat-su-nam-phap-ly.willmich-co.chatgpt.site"
BASE_PATH = "/luatsunam/"

FIRM = {
    "legal_name": "Công Ty Luật TNHH Luật Sư Nam",
    "short_name": "Luật Sư Nam",
    "brand": "LSN Law Firm",
    "slogan": "Kiến tạo công lý bền vững",
    "lawyer": "Luật sư Nguyễn Trọng Nam",
    "phone": "0983 498 499",
    "phone_tel": "0983498499",
    "phone_intl": "+84983498499",
    "email": "luatsunam.hcm@gmail.com",
    "zalo": "https://zalo.me/0983498499",
    "street": "22c Vũ Ngọc Phan",
    "ward": "Phường Bình Lợi Trung",
    "city": "Thành phố Hồ Chí Minh",
    "hours": "Thứ 2 – Thứ 6: 08:00 – 17:30",
    "hours_note": "Ngoài giờ và cuối tuần: vui lòng liên hệ trước qua hotline hoặc Zalo",
    "maps_query": "22c%20V%C5%A9%20Ng%E1%BB%8Dc%20Phan%2C%20Ph%C6%B0%E1%BB%9Dng%20B%C3%ACnh%20L%E1%BB%A3i%20Trung%2C%20Th%C3%A0nh%20ph%E1%BB%91%20H%E1%BB%93%20Ch%C3%AD%20Minh",
}
FIRM["address"] = f'{FIRM["street"]}, {FIRM["ward"]}, {FIRM["city"]}'

# ---------------------------------------------------------------------------
# Lĩnh vực dịch vụ
#
# Mỗi lĩnh vực có một trang riêng /dich-vu/<slug>/ gồm các phần theo thứ tự:
#   hero_title, lead          Tiêu đề và đoạn mở đầu (hero_title được dùng <em> để tô đỏ)
#   problem_title, problem_text  Thẻ "Anh chị đang gặp chuyện gì?" ở trang chủ và trang Dịch vụ
#   situations                Những tình huống người dân thường gặp
#   scope_intro, scope        Luật sư giúp được những việc gì
#   tips, note_*, principle_* Việc nên làm ngay, lưu ý và nguyên tắc làm việc
#   steps                     Các bước làm việc
#   docs, deliverables        Giấy tờ nên mang theo, anh chị nhận được gì
#   faq                       Câu hỏi hay gặp (câu trả lời có dẫn điều luật)
#   laws                      Căn cứ pháp luật chủ yếu
#   cta_title, cta_text       Lời mời liên hệ cuối trang
# ---------------------------------------------------------------------------
SERVICES = [
    {
        "slug": "thua-ke",
        "name": "Thừa kế",
        "icon": "i-inherit",
        "short": "Tư vấn lập di chúc, phân chia di sản, khai nhận thừa kế và giải quyết tranh chấp giữa các bên liên quan.",
        "title": "Luật sư tư vấn Thừa kế tại TP.HCM",
        "description": "Luật sư tư vấn lập di chúc, khai nhận và phân chia di sản thừa kế, giải quyết tranh chấp thừa kế theo Bộ luật Dân sự. Liên hệ 0983 498 499.",
        "image_alt": "Luật sư trao đổi hồ sơ thừa kế với khách hàng tại văn phòng",
        "problem_title": "Chia đất, chia nhà sau khi cha mẹ mất",
        "problem_text": "Anh em tranh chấp di sản, không có di chúc hoặc di chúc chưa rõ ràng, cần làm thủ tục khai nhận thừa kế.",
        "hero_title": "Chia di sản thừa kế đúng luật, <em>giữ được tình thân</em>",
        "lead": "Cha mẹ mất để lại nhà đất, tiền bạc mà anh chị em chưa thống nhất, di chúc chưa rõ ràng hay giấy tờ còn thiếu? Luật sư giúp anh chị biết ai được hưởng, hưởng bao nhiêu, cần làm thủ tục gì, và ưu tiên cách thỏa thuận êm thấm trước khi phải tính đến Tòa án.",
        "situations": [
            "Cha mẹ mất không để lại di chúc, anh chị em chưa biết chia thế nào cho đúng.",
            "Có di chúc nhưng một người trong nhà cho rằng di chúc không hợp lệ.",
            "Nhà đất đứng tên cha mẹ, một người đang ở và không chịu chia.",
            "Muốn khai nhận, sang tên nhưng có người ở xa, ở nước ngoài hoặc không chịu ký.",
            "Cha mẹ còn khỏe, muốn lập di chúc rõ ràng để con cháu sau này không tranh chấp.",
            "Người mất còn nợ, không biết người thừa kế có phải trả thay hay không.",
        ],
        "scope_intro": "Một hồ sơ thừa kế thường dính tới nhiều chuyện cùng lúc: quan hệ gia đình, nhà đất, tài sản chung của cha mẹ, khoản nợ và ý nguyện của người đã mất. Luật sư xem tổng thể trước rồi mới tư vấn, để anh chị hiểu rõ phần của mình và chọn cách làm phù hợp.",
        "scope": [
            ("Lập và kiểm tra di chúc", "Hướng dẫn cách lập di chúc có hiệu lực: hình thức, nội dung, người làm chứng; chỉ ra những chỗ dễ bị cho là vô hiệu."),
            ("Xác định di sản và người thừa kế", "Tách phần tài sản riêng của người mất khỏi tài sản chung; xác định ai thuộc hàng thừa kế, ai được hưởng dù không có tên trong di chúc."),
            ("Khai nhận, phân chia di sản", "Hướng dẫn thủ tục khai nhận, thỏa thuận phân chia, từ chối nhận di sản và đăng ký sang tên tài sản."),
            ("Thừa kế nhà đất, tiền gửi, cổ phần", "Kiểm tra giấy tờ sở hữu, nghĩa vụ thuế phí và thủ tục chuyển quyền với từng loại tài sản."),
            ("Người thừa kế ở nước ngoài", "Hướng dẫn giấy tờ do nước ngoài cấp, ủy quyền, hợp pháp hóa lãnh sự để người ở xa vẫn làm được thủ tục."),
            ("Tranh chấp thừa kế", "Đánh giá chứng cứ, thời hiệu; thử hòa giải trong gia đình hoặc bảo vệ quyền lợi của anh chị tại Tòa án."),
        ],
        "tips": [
            "Giữ bản chính giấy chứng tử, di chúc (nếu có) và giấy tờ nhà đất ở nơi an toàn; chỉ đưa bản sao cho người khác.",
            "Ghi lại danh sách người thân của người mất: vợ hoặc chồng, cha mẹ, các con (kể cả con riêng, con nuôi).",
            "Chưa ký văn bản từ chối nhận di sản hay thỏa thuận phân chia khi chưa hiểu rõ phần mình được hưởng.",
            "Để ý thời hiệu: yêu cầu chia di sản là nhà đất 30 năm, tài sản khác 10 năm, tính từ ngày người để lại di sản mất.",
        ],
        "docs": [
            "Giấy chứng tử và giấy tờ nhân thân của các bên",
            "Di chúc, văn bản tặng cho hoặc thỏa thuận đã có",
            "Giấy chứng nhận nhà đất, giấy tờ tài sản, sao kê",
            "Tài liệu về khoản nợ và nghĩa vụ của người để lại di sản",
        ],
        "deliverables": [
            "Giải thích rõ quyền thừa kế và rủi ro của hồ sơ",
            "Danh mục giấy tờ, thủ tục và lộ trình thực hiện",
            "Dự thảo di chúc, thỏa thuận hoặc văn bản cần thiết",
            "Luật sư đại diện làm việc theo phạm vi ủy quyền đã thống nhất",
        ],
        "principle_title": "Ưu tiên giữ hòa khí gia đình",
        "principle_text": "Khi còn khả năng thỏa thuận, luật sư hướng tới phương án êm thấm giữa những người trong nhà; đồng thời chuẩn bị sẵn căn cứ, chứng cứ để bảo vệ quyền lợi của anh chị nếu tranh chấp xảy ra.",
        "steps": [
            ("Nghe anh chị kể", "Người mất là ai, để lại tài sản gì, gia đình có những ai."),
            ("Xem giấy tờ", "Kiểm tra di chúc, giấy tờ sở hữu, hàng thừa kế và thời hiệu."),
            ("Bàn cách làm", "So sánh thỏa thuận, công chứng hay khởi kiện, kèm chi phí dự kiến."),
            ("Chuẩn bị hồ sơ", "Soạn văn bản, hướng dẫn thủ tục theo cách đã chọn."),
            ("Đi cùng đến cùng", "Làm việc với cơ quan, tổ chức hoặc Tòa án khi được ủy quyền."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Thời gian và thủ tục cụ thể phụ thuộc loại tài sản, tình trạng giấy tờ và mức độ thống nhất giữa những người thừa kế.",
        "faq": [
            ("Cha mẹ mất không để lại di chúc thì chia thế nào?",
             "Di sản được chia theo pháp luật. Hàng thừa kế thứ nhất gồm vợ, chồng, cha đẻ, mẹ đẻ, cha nuôi, mẹ nuôi, con đẻ, con nuôi của người mất; những người cùng hàng được hưởng phần bằng nhau (<strong>Điều 650, 651 Bộ luật Dân sự 2015</strong>). Trước khi chia, cần tách phần tài sản của người vợ hoặc chồng còn sống ra khỏi khối tài sản chung."),
            ("Một người trong nhà không chịu ký thì có làm thủ tục được không?",
             "Thỏa thuận phân chia di sản tại tổ chức hành nghề công chứng cần sự đồng ý của tất cả những người thừa kế. Nếu có người không đồng ý hoặc không hợp tác, anh chị có thể yêu cầu Tòa án chia di sản. Luật sư sẽ cùng anh chị cân nhắc nên thương lượng thêm hay khởi kiện, tùy giấy tờ và quan hệ trong gia đình."),
            ("Đã nhiều năm rồi, còn yêu cầu chia di sản được không?",
             "Thời hiệu yêu cầu chia di sản là 30 năm với bất động sản và 10 năm với động sản, tính từ thời điểm mở thừa kế (<strong>Điều 623 Bộ luật Dân sự 2015</strong>). Hồ sơ mở thừa kế trước năm 2017, hoặc tài sản đã được anh chị em thỏa thuận để chung, cần luật sư xem riêng. Đọc thêm: <a href=\"{{root}}kien-thuc-phap-ly/thoi-hieu-chia-di-san-thua-ke/\">thời hiệu chia di sản thừa kế</a>."),
        ],
        "laws": ["Bộ luật Dân sự 2015 (Phần thứ tư – Thừa kế)", "Luật Công chứng 2024", "Luật Đất đai 2024", "Luật Hôn nhân và Gia đình 2014"],
        "cta_title": "Chuẩn bị đúng từ đầu giúp gia đình tránh tranh chấp về sau",
        "cta_text": "Anh chị gọi điện hoặc nhắn Zalo kể sơ qua về tài sản và những người thừa kế. Luật sư sẽ cho biết cần chuẩn bị giấy tờ gì và nên bắt đầu từ đâu.",
        "related": ["cong-chung", "dat-dai-bat-dong-san", "tranh-tung-giai-quyet-tranh-chap"],
    },
    {
        "slug": "tranh-tung-giai-quyet-tranh-chap",
        "name": "Tranh tụng & Giải quyết tranh chấp",
        "icon": "i-gavel",
        "short": "Đại diện, thương lượng và bảo vệ quyền lợi tại Tòa án, Trọng tài trong tranh chấp thương mại, hợp đồng và lao động.",
        "title": "Luật sư Tranh tụng & Giải quyết tranh chấp",
        "seo_title": "Luật sư tranh tụng, giải quyết tranh chấp tại TP.HCM",
        "description": "Đại diện, thương lượng, hòa giải và bảo vệ quyền lợi tại Tòa án, Trọng tài trong tranh chấp hợp đồng, thương mại, dân sự và lao động.",
        "image_alt": "Búa phán quyết trên bàn xét xử",
        "problem_title": "Bị kiện hoặc cần khởi kiện ra Tòa",
        "problem_text": "Soạn đơn, chuẩn bị chứng cứ, đại diện và tranh luận tại Tòa án, Trọng tài qua các cấp xét xử.",
        "hero_title": "Bị kiện hay cần khởi kiện, <em>có luật sư cùng chuẩn bị</em>",
        "lead": "Nhận giấy của Tòa án, đối tác chây ỳ không trả tiền hay chuyện làm ăn đổ vỡ – luật sư giúp anh chị xem hồ sơ, tính trước được mất, thử thương lượng, và khi cần thì đại diện, tranh luận tại Tòa án, Trọng tài.",
        "situations": [
            "Nhận được thông báo thụ lý hoặc giấy triệu tập của Tòa án vì bị kiện.",
            "Đối tác nhận hàng, nhận tiền rồi không thanh toán, không giao hàng như đã thỏa thuận.",
            "Muốn khởi kiện nhưng không biết nộp đơn ở Tòa nào, cần chứng cứ gì.",
            "Đã có bản án sơ thẩm, chưa đồng ý và muốn kháng cáo.",
            "Thắng kiện rồi nhưng bên kia không chịu thi hành bản án.",
        ],
        "scope_intro": "Giải quyết tranh chấp không chỉ là nộp đơn kiện. Luật sư cùng anh chị cân nhắc mục tiêu thực sự, chi phí, thời gian, khả năng đòi được tiền và quan hệ giữa các bên, rồi mới chọn cách làm.",
        "scope": [
            ("Xem hồ sơ, đánh giá chứng cứ", "Rà soát hợp đồng, chứng từ, tin nhắn, thời hiệu, Tòa án có thẩm quyền; chỉ ra tài liệu còn thiếu."),
            ("Tính toán trước khi kiện", "Phân tích yêu cầu, khả năng bị phản bác, biện pháp khẩn cấp tạm thời, chi phí và khả năng thi hành."),
            ("Thương lượng, hòa giải", "Soạn thư yêu cầu, chuẩn bị nội dung đàm phán, tham gia hòa giải và rà soát thỏa thuận để bảo đảm thực hiện được."),
            ("Đại diện tại Tòa án", "Chuẩn bị đơn từ, bản trình bày, chứng cứ; tham gia phiên họp, hòa giải và xét xử theo phạm vi ủy quyền."),
            ("Trọng tài thương mại", "Tư vấn điều khoản trọng tài, thời hạn; chuẩn bị hồ sơ và đại diện trong quá trình tố tụng trọng tài."),
            ("Thi hành bản án", "Hỗ trợ yêu cầu thi hành án, xác minh điều kiện thi hành, thỏa thuận thi hành và theo dõi việc xử lý tài sản."),
        ],
        "tips": [
            "Không bỏ qua giấy tờ của Tòa án: đọc kỹ, ghi lại ngày nhận và thời hạn phải trả lời.",
            "Gom đủ hợp đồng, hóa đơn, chứng từ chuyển khoản, tin nhắn, email; giữ nguyên dữ liệu gốc, không chỉnh sửa.",
            "Thời hạn kháng cáo bản án dân sự sơ thẩm chỉ 15 ngày – nên gặp luật sư ngay sau phiên tòa.",
            "Hạn chế tự nhắn tin cam kết hay thừa nhận điều gì với bên kia khi chưa hỏi ý kiến luật sư.",
        ],
        "docs": [
            "Hợp đồng, phụ lục, biên bản và chứng từ thanh toán",
            "Email, tin nhắn, thư yêu cầu và phản hồi giữa các bên",
            "Tài liệu giao nhận, nghiệm thu, đối chiếu công nợ",
            "Đơn từ, quyết định hoặc hồ sơ Tòa án đã nhận",
        ],
        "deliverables": [
            "Đánh giá thẳng thắn về căn cứ, rủi ro và các lựa chọn",
            "Kế hoạch giải quyết theo từng mốc công việc",
            "Đơn từ, văn bản và chứng cứ được sắp xếp bài bản",
            "Cập nhật tiến độ và lời khuyên ở mỗi giai đoạn",
        ],
        "principle_title": "Chọn cách làm có lợi thật sự",
        "principle_text": "Mục tiêu là kết quả thực tế và đòi được quyền lợi, không phải kiện cho bằng được. Tòa án là lựa chọn khi thương lượng không còn hiệu quả, sau khi anh chị đã biết rõ chi phí và rủi ro.",
        "steps": [
            ("Nghe anh chị kể", "Ai tranh chấp với ai, về việc gì, các mốc thời gian quan trọng."),
            ("Đánh giá chứng cứ", "Căn cứ, thời hiệu, Tòa án có thẩm quyền và khả năng thi hành."),
            ("Chọn cách giải quyết", "Thương lượng, hòa giải, Tòa án hay Trọng tài."),
            ("Triển khai", "Soạn hồ sơ và tham gia làm việc theo phạm vi ủy quyền."),
            ("Theo sát kết quả", "Cập nhật tiến độ, điều chỉnh cách làm và hỗ trợ thi hành án."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Không ai có thể bảo đảm trước kết quả xét xử. Đánh giá chỉ chính xác khi luật sư được xem đầy đủ hồ sơ và chứng cứ.",
        "faq": [
            ("Nhận thông báo bị kiện, tôi phải làm gì?",
             "Trong thời hạn 15 ngày kể từ ngày nhận thông báo thụ lý, anh chị cần nộp cho Tòa án văn bản ghi ý kiến của mình về yêu cầu của người khởi kiện, kèm tài liệu, chứng cứ (nếu có) (<strong>Điều 199 Bộ luật Tố tụng dân sự 2015</strong>). Đây là lúc nên nhờ luật sư xem hồ sơ để chuẩn bị ý kiến và chứng cứ phản bác."),
            ("Không đồng ý bản án sơ thẩm thì kháng cáo trong bao lâu?",
             "Thời hạn kháng cáo bản án dân sự sơ thẩm là 15 ngày kể từ ngày tuyên án; nếu anh chị vắng mặt tại phiên tòa vì lý do chính đáng thì thời hạn tính từ ngày nhận được bản án hoặc bản án được niêm yết (<strong>Điều 273 Bộ luật Tố tụng dân sự 2015</strong>). Kháng cáo quá hạn rất khó được chấp nhận."),
            ("Có nhất thiết phải ra Tòa không?",
             "Không phải lúc nào cũng vậy. Nhiều tranh chấp có thể giải quyết bằng thương lượng, hòa giải với chi phí và thời gian ít hơn. Luật sư phân tích chứng cứ, chi phí, thời gian và khả năng thi hành để anh chị chọn cách phù hợp."),
        ],
        "laws": ["Bộ luật Tố tụng dân sự 2015 (sửa đổi, bổ sung)", "Bộ luật Dân sự 2015", "Luật Thương mại 2005", "Luật Trọng tài thương mại 2010", "Luật Thi hành án dân sự"],
        "cta_title": "Chuẩn bị sớm giúp giữ được chứng cứ và thời hạn",
        "cta_text": "Gọi điện hoặc nhắn Zalo cho luật sư ngay khi nhận giấy tờ của Tòa án hoặc khi thấy tranh chấp có dấu hiệu kéo dài.",
        "related": ["dan-su", "lao-dong-viec-lam", "dat-dai-bat-dong-san"],
    },
    {
        "slug": "hon-nhan-gia-dinh",
        "name": "Hôn nhân & Gia đình",
        "icon": "i-heart",
        "short": "Tư vấn ly hôn, quyền nuôi con, cấp dưỡng, phân chia tài sản chung và các thỏa thuận gia đình một cách kín đáo.",
        "title": "Luật sư Hôn nhân & Gia đình, tư vấn ly hôn",
        "seo_title": "Luật sư ly hôn, hôn nhân gia đình tại TP.HCM",
        "description": "Tư vấn ly hôn thuận tình và đơn phương, quyền nuôi con, cấp dưỡng, phân chia tài sản chung vợ chồng. Thông tin khách hàng được bảo mật theo Luật Luật sư.",
        "image_alt": "Gia đình cha mẹ và con nhỏ lúc hoàng hôn",
        "problem_title": "Ly hôn, giành quyền nuôi con",
        "problem_text": "Muốn ly hôn thuận tình hay đơn phương, chia tài sản chung, cấp dưỡng và quyền nuôi con.",
        "hero_title": "Ly hôn, nuôi con, chia tài sản – <em>kín đáo và tôn trọng</em>",
        "lead": "Chuyện gia đình khó nói với người ngoài. Luật sư nghe anh chị trình bày riêng, giải thích quyền của anh chị và các con, rồi cùng tìm cách giải quyết ít tổn thương nhất. Mọi thông tin được giữ kín theo Luật Luật sư.",
        "situations": [
            "Muốn ly hôn nhưng vợ hoặc chồng không chịu ký đơn, hoặc đã bỏ đi không liên lạc được.",
            "Hai bên đồng ý ly hôn nhưng chưa thống nhất ai nuôi con, chia nhà, chia tiền ra sao.",
            "Lo mất quyền nuôi con vì thu nhập thấp hơn hoặc đang phải ở nhờ nhà người thân.",
            "Người kia không cấp dưỡng nuôi con như đã thỏa thuận hoặc như bản án.",
            "Tài sản đứng tên một người, không biết có phải tài sản chung để chia hay không.",
            "Một bên đang ở nước ngoài, cần làm thủ tục ly hôn hoặc giấy tờ ủy quyền.",
        ],
        "scope_intro": "Luật sư giúp anh chị nhìn rõ quyền, nghĩa vụ và hệ quả của từng lựa chọn trước khi quyết định. Hồ sơ được xử lý kín đáo, tôn trọng hoàn cảnh riêng và ưu tiên phương án có thể thực hiện lâu dài, nhất là với các con.",
        "scope": [
            ("Ly hôn thuận tình", "Tư vấn điều kiện, chuẩn bị hồ sơ và hoàn thiện thỏa thuận về con, tài sản, nợ chung để nộp Tòa án."),
            ("Ly hôn đơn phương", "Đánh giá căn cứ ly hôn, Tòa án có thẩm quyền, chứng cứ; soạn đơn và bảo vệ quyền lợi của anh chị khi bên kia không đồng ý hoặc vắng mặt."),
            ("Quyền nuôi con, cấp dưỡng", "Phân tích điều kiện chăm sóc con, nguyện vọng của con, mức cấp dưỡng và giấy tờ cần có để bảo vệ lợi ích của các cháu."),
            ("Chia tài sản, nợ chung", "Xác định tài sản chung, tài sản riêng, công sức đóng góp, khoản nợ và cách chia nhà đất, tiền, cổ phần."),
            ("Có yếu tố nước ngoài", "Hướng dẫn hồ sơ, giấy tờ nước ngoài và thủ tục khi một bên đang ở hoặc có tài sản ở nước ngoài."),
            ("Thỏa thuận trong gia đình", "Soạn, rà soát thỏa thuận về tài sản vợ chồng, chia tài sản trong thời kỳ hôn nhân, nuôi con và các cam kết khác."),
        ],
        "tips": [
            "Cất giữ bản chính giấy chứng nhận kết hôn, giấy khai sinh của con và giấy tờ tài sản ở nơi an toàn.",
            "Ghi lại thu nhập, chi phí nuôi con và ai đang trực tiếp chăm sóc con hằng ngày.",
            "Nếu bị bạo lực gia đình, hãy ưu tiên an toàn: báo công an hoặc chính quyền nơi cư trú, giữ lại giấy khám thương, hình ảnh.",
            "Không tự ý bán, chuyển nhượng tài sản chung khi đang có mâu thuẫn; việc này có thể bất lợi cho chính anh chị.",
        ],
        "docs": [
            "Giấy chứng nhận kết hôn và giấy tờ nhân thân",
            "Giấy khai sinh của con và tài liệu về việc chăm sóc con",
            "Giấy tờ nhà đất, tài khoản, cổ phần và tài sản khác",
            "Chứng từ về thu nhập, khoản nợ và nghĩa vụ chung",
        ],
        "deliverables": [
            "Giải thích quyền lợi và những điểm cần ưu tiên",
            "Phương án về con, tài sản và nghĩa vụ tài chính",
            "Đơn từ, hồ sơ và thỏa thuận được soạn sẵn",
            "Luật sư đồng hành, bảo vệ quyền lợi tại Tòa án theo phạm vi đã thống nhất",
        ],
        "principle_title": "Kín đáo và nhân văn",
        "principle_text": "Thông tin gia đình được tiếp nhận thận trọng. Luật sư khuyến khích thỏa thuận khi phù hợp, nhưng luôn chuẩn bị phương án pháp lý đầy đủ để bảo vệ anh chị và các con.",
        "steps": [
            ("Trao đổi riêng", "Mong muốn của anh chị, tình trạng hôn nhân, con và tài sản."),
            ("Xem hồ sơ", "Tách rõ việc đã thống nhất và việc còn tranh chấp."),
            ("Bàn phương án", "Thỏa thuận hay yêu cầu Tòa án giải quyết, kèm chi phí dự kiến."),
            ("Làm thủ tục", "Soạn hồ sơ, nộp đơn và theo dõi quá trình giải quyết."),
            ("Sau bản án", "Hướng dẫn thi hành và xử lý việc phát sinh về con, tài sản."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Thời gian giải quyết phụ thuộc mức độ thống nhất của hai bên, nơi cư trú, tình trạng tài sản và lịch làm việc của Tòa án.",
        "faq": [
            ("Vợ hoặc chồng không chịu ký đơn thì có ly hôn được không?",
             "Có thể, nếu có căn cứ. Khi một bên yêu cầu ly hôn mà hòa giải tại Tòa án không thành, Tòa án giải quyết cho ly hôn nếu có căn cứ về bạo lực gia đình hoặc vi phạm nghiêm trọng quyền, nghĩa vụ vợ chồng làm hôn nhân lâm vào tình trạng trầm trọng, đời sống chung không thể kéo dài (<strong>Điều 56 Luật Hôn nhân và Gia đình 2014</strong>). Đọc thêm: <a href=\"{{root}}kien-thuc-phap-ly/ly-hon-don-phuong/\">ly hôn đơn phương</a>."),
            ("Con còn nhỏ thì ai được nuôi?",
             "Hai bên được thỏa thuận; nếu không thỏa thuận được, Tòa án quyết định dựa trên quyền lợi về mọi mặt của con. Con dưới 36 tháng tuổi được giao cho mẹ trực tiếp nuôi, trừ trường hợp người mẹ không đủ điều kiện hoặc cha mẹ có thỏa thuận khác phù hợp với lợi ích của con; con từ đủ 07 tuổi trở lên thì phải xem xét nguyện vọng của con (<strong>Điều 81 Luật Hôn nhân và Gia đình 2014</strong>)."),
            ("Tôi có thể nhờ luật sư ra Tòa thay mình không?",
             "Đối với việc ly hôn, anh chị phải tự mình tham gia tố tụng, không được ủy quyền cho người khác thay mặt (<strong>khoản 4 Điều 85 Bộ luật Tố tụng dân sự 2015</strong>). Luật sư chuẩn bị hồ sơ, hướng dẫn anh chị trình bày và tham gia với tư cách người bảo vệ quyền và lợi ích hợp pháp, nhất là trong các vấn đề về con và tài sản."),
        ],
        "laws": ["Luật Hôn nhân và Gia đình 2014", "Bộ luật Tố tụng dân sự 2015 (sửa đổi, bổ sung)", "Bộ luật Dân sự 2015"],
        "cta_title": "Một phương án rõ ràng giúp gia đình bớt áp lực",
        "cta_text": "Anh chị có thể gọi điện hoặc nhắn Zalo để hẹn trao đổi riêng với luật sư. Nội dung trao đổi được giữ kín ngay từ cuộc gọi đầu tiên.",
        "related": ["thua-ke", "cong-chung", "dan-su"],
    },
    {
        "slug": "dat-dai-bat-dong-san",
        "name": "Đất đai & Bất động sản",
        "icon": "i-house",
        "short": "Rà soát pháp lý dự án, giao dịch, cấp giấy chứng nhận và giải quyết tranh chấp đất đai, nhà ở.",
        "title": "Luật sư Đất đai & Bất động sản",
        "seo_title": "Luật sư đất đai, bất động sản tại TP.HCM",
        "description": "Rà soát pháp lý dự án và giao dịch bất động sản, thủ tục cấp Giấy chứng nhận, giải quyết tranh chấp đất đai, nhà ở theo Luật Đất đai hiện hành.",
        "image_alt": "Ngôi nhà và khuôn viên sân vườn",
        "problem_title": "Mua bán, đặt cọc nhà đất",
        "problem_text": "Lo bị lừa khi đặt cọc, tranh chấp ranh giới, chậm sang tên hoặc chưa được cấp sổ.",
        "hero_title": "Nhà đất là tài sản lớn – <em>kiểm tra kỹ trước khi xuống tiền</em>",
        "lead": "Sắp đặt cọc mua nhà, tranh chấp ranh giới với hàng xóm, đất bị thu hồi hay mãi chưa được cấp sổ – luật sư giúp anh chị đọc hiểu giấy tờ, chỉ ra rủi ro và đi cùng anh chị qua từng thủ tục với cơ quan nhà nước, Tòa án.",
        "situations": [
            "Sắp đặt cọc, mua nhà đất và muốn biết giấy tờ có an toàn không.",
            "Đã đặt cọc nhưng bên bán đổi ý, đòi tăng giá hoặc không chịu ra công chứng.",
            "Mua đất bằng giấy tay nhiều năm, giờ không sang tên được.",
            "Tranh chấp ranh giới, lối đi chung với hàng xóm.",
            "Đất bị thu hồi, không đồng ý với mức bồi thường, hỗ trợ.",
            "Hồ sơ xin cấp sổ bị trả lại hoặc kéo dài không rõ lý do.",
        ],
        "scope_intro": "Giấy tờ nhà đất thường trải qua nhiều đời chủ, nhiều thời kỳ. Luật sư kiểm tra nguồn gốc, tình trạng pháp lý, quy hoạch, thế chấp và điều kiện chuyển nhượng trước, rồi mới đề xuất cách làm an toàn cho anh chị.",
        "scope": [
            ("Kiểm tra trước khi mua, đặt cọc", "Xem giấy chứng nhận, người bán, quy hoạch, thế chấp, hạn chế chuyển nhượng và các điều khoản đặt cọc."),
            ("Thủ tục nhà đất", "Hỗ trợ cấp, cấp đổi giấy chứng nhận; sang tên, tặng cho, thừa kế, tách thửa, hợp thửa và đăng ký biến động."),
            ("Hợp đồng và đặt cọc", "Soạn, rà soát hợp đồng đặt cọc, chuyển nhượng, thuê; thiết kế cách thanh toán và cách xử lý khi một bên vi phạm."),
            ("Tranh chấp đất đai", "Tư vấn tranh chấp ranh giới, lối đi, quyền sử dụng, giao dịch vô hiệu và yêu cầu hủy, chỉnh lý giấy chứng nhận."),
            ("Thu hồi, bồi thường, tái định cư", "Rà soát phương án bồi thường, hỗ trợ, tái định cư; tư vấn khiếu nại và làm việc với cơ quan nhà nước."),
            ("Pháp lý dự án bất động sản", "Rà soát chủ trương, đất đai, xây dựng, điều kiện kinh doanh, mua bán và chuyển nhượng dự án."),
        ],
        "tips": [
            "Chưa đặt cọc, chưa chuyển tiền lớn khi chưa xem bản chính giấy chứng nhận và kiểm tra quy hoạch, thế chấp.",
            "Ưu tiên chuyển khoản; nếu đưa tiền mặt phải có biên nhận ghi rõ nội dung và chữ ký người nhận.",
            "Giữ lại toàn bộ hợp đồng, biên nhận, tin nhắn và thông báo của cơ quan nhà nước.",
            "Nhận quyết định thu hồi đất, bồi thường: chú ý thời hiệu khiếu nại, thông thường là 90 ngày kể từ khi nhận hoặc biết quyết định.",
        ],
        "docs": [
            "Giấy chứng nhận và hồ sơ kỹ thuật thửa đất, căn nhà",
            "Hợp đồng, đặt cọc, giấy giao nhận tiền và biên bản",
            "Thông tin quy hoạch, thế chấp hoặc thông báo của cơ quan nhà nước",
            "Đơn từ, quyết định và tài liệu tranh chấp đã có",
        ],
        "deliverables": [
            "Đánh giá tình trạng pháp lý và những rủi ro chính",
            "Danh sách điều kiện cần hoàn thiện trước khi giao dịch",
            "Hợp đồng, văn bản và hồ sơ thủ tục phù hợp",
            "Phương án thương lượng, khiếu nại hoặc khởi kiện",
        ],
        "principle_title": "Không chỉ nhìn bản sao sổ",
        "principle_text": "Việc đánh giá dựa trên giấy tờ về người bán, hiện trạng, quy hoạch, thế chấp và lịch sử chuyển nhượng mà anh chị cung cấp hoặc có thể xác minh – không chỉ một bản sao giấy chứng nhận.",
        "steps": [
            ("Nghe anh chị kể", "Giao dịch, thủ tục hay tranh chấp cần giải quyết."),
            ("Kiểm tra giấy tờ", "Quyền sở hữu, quy hoạch, thế chấp và hạn chế pháp lý."),
            ("Chỉ ra rủi ro", "Việc cần khắc phục và điều kiện phải có trước khi ký."),
            ("Triển khai", "Soạn hồ sơ, đàm phán hoặc làm việc với cơ quan nhà nước."),
            ("Hoàn tất", "Theo dõi đăng ký, bàn giao và nghĩa vụ sau giao dịch."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Kết luận pháp lý phụ thuộc giấy tờ thực tế và thông tin từ cơ quan có thẩm quyền. Không nên đặt cọc hoặc thanh toán lớn khi tình trạng hồ sơ chưa được làm rõ.",
        "faq": [
            ("Đặt cọc rồi mà bên bán đổi ý thì xử lý thế nào?",
             "Nếu hợp đồng đặt cọc không có thỏa thuận khác, bên nhận cọc từ chối giao kết, thực hiện hợp đồng thì phải trả lại tiền cọc và một khoản tiền tương đương giá trị tiền cọc; ngược lại, bên đặt cọc từ chối thì mất cọc (<strong>Điều 328 Bộ luật Dân sự 2015</strong>). Cách xử lý cụ thể còn tùy nội dung hợp đồng đặt cọc và chứng cứ về việc ai vi phạm. Đọc thêm: <a href=\"{{root}}kien-thuc-phap-ly/dat-coc-mua-ban-nha-dat/\">6 điểm cần kiểm tra trước khi đặt cọc</a>."),
            ("Mua bán đất bằng giấy tay có được không?",
             "Hợp đồng chuyển nhượng quyền sử dụng đất phải được công chứng hoặc chứng thực theo <strong>Luật Đất đai 2024</strong> (trừ một số trường hợp kinh doanh bất động sản). Giấy tay khó dùng để sang tên và dễ phát sinh tranh chấp. Với giao dịch giấy tay đã có từ trước, khả năng hợp thức hóa phụ thuộc thời điểm giao dịch, tình trạng đất và giấy tờ – luật sư cần xem hồ sơ cụ thể."),
            ("Tranh chấp đất với hàng xóm có phải hòa giải ở phường, xã trước không?",
             "Với tranh chấp về việc ai có quyền sử dụng đất, như ranh giới, lối đi, các bên phải hòa giải tại Ủy ban nhân dân cấp xã nơi có đất trước khi yêu cầu giải quyết. Tranh chấp về hợp đồng chuyển nhượng, tặng cho hay thừa kế quyền sử dụng đất thường không bắt buộc bước này. Luật sư sẽ xác định đúng thủ tục cho vụ việc của anh chị."),
        ],
        "laws": ["Luật Đất đai 2024", "Luật Nhà ở 2023", "Luật Kinh doanh bất động sản 2023", "Bộ luật Dân sự 2015"],
        "cta_title": "Kiểm tra trước khi ký để không mất tiền oan",
        "cta_text": "Chuẩn bị sẵn giấy tờ nhà đất đang có rồi gọi điện hoặc nhắn Zalo cho luật sư. Luật sư sẽ cho biết cần xác minh thêm điều gì trước khi anh chị xuống tiền.",
        "related": ["cong-chung", "thua-ke", "tranh-tung-giai-quyet-tranh-chap"],
    },
    {
        "slug": "lao-dong-viec-lam",
        "name": "Lao động & Việc làm",
        "icon": "i-network",
        "problem_icon": "i-team",
        "short": "Xây dựng quy chế, hợp đồng lao động, xử lý kỷ luật, chấm dứt hợp đồng và tranh chấp lao động.",
        "title": "Luật sư Lao động & Việc làm",
        "seo_title": "Luật sư lao động, tranh chấp lao động TP.HCM",
        "description": "Xây dựng hợp đồng lao động, nội quy, quy chế; tư vấn xử lý kỷ luật, chấm dứt hợp đồng và giải quyết tranh chấp lao động theo Bộ luật Lao động.",
        "image_alt": "Hai doanh nhân bắt tay trong văn phòng",
        "problem_title": "Bị cho nghỉ việc, nợ lương, bảo hiểm",
        "problem_text": "Người lao động bị chấm dứt hợp đồng trái luật; doanh nghiệp cần xử lý kỷ luật, nội quy đúng quy định.",
        "hero_title": "Quyền lợi người lao động, <em>quy trình đúng cho doanh nghiệp</em>",
        "lead": "Bị cho nghỉ việc đột ngột, bị nợ lương, công ty không đóng bảo hiểm – hay doanh nghiệp cần kỷ luật, cho nghỉ việc đúng luật để tránh bị kiện. Luật sư giúp anh chị biết mình đúng, sai ở đâu và nên làm gì tiếp theo.",
        "situations": [
            "Bị công ty cho nghỉ việc ngang, không báo trước, không có lý do rõ ràng.",
            "Bị nợ lương, không được trả trợ cấp thôi việc hoặc tiền ngày phép.",
            "Công ty không đóng hoặc đóng thiếu bảo hiểm xã hội.",
            "Bị kỷ luật, sa thải nhưng thấy không đúng quy trình.",
            "Doanh nghiệp cần xây dựng hợp đồng, nội quy, quy trình kỷ luật đúng luật.",
            "Doanh nghiệp muốn cho người lao động nghỉ việc mà không bị kiện ngược.",
        ],
        "scope_intro": "Quan hệ lao động cần cả căn cứ pháp luật lẫn hồ sơ làm đúng từng bước. Luật sư xem quy trình, chứng cứ và tác động thực tế để đề xuất cách xử lý phù hợp cho cả người lao động và doanh nghiệp.",
        "scope": [
            ("Hợp đồng và hồ sơ nhân sự", "Soạn, rà soát hợp đồng lao động, thử việc, bảo mật, đào tạo, điều chuyển và hồ sơ quản lý người lao động."),
            ("Nội quy và chính sách", "Xây dựng nội quy lao động, quy chế lương thưởng, đánh giá công việc và quy trình tiếp nhận khiếu nại."),
            ("Kỷ luật lao động", "Đánh giá hành vi, chứng cứ, thời hiệu; hướng dẫn họp xử lý và ra quyết định đúng trình tự."),
            ("Chấm dứt hợp đồng", "Tư vấn đơn phương chấm dứt, thỏa thuận nghỉ việc, thay đổi cơ cấu và các khoản phải thanh toán."),
            ("Tiền lương, bảo hiểm", "Rà soát tiền lương, làm thêm giờ, phép năm, bảo hiểm, trợ cấp và các khoản bồi thường."),
            ("Tranh chấp lao động", "Đại diện thương lượng, hòa giải và khởi kiện về kỷ luật, cho nghỉ việc, tiền lương, bảo hiểm và quyền lợi khác."),
        ],
        "tips": [
            "Giữ lại hợp đồng lao động, bảng lương, sao kê nhận lương và các quyết định của công ty.",
            "Chụp lại tin nhắn, email thông báo cho nghỉ việc; ghi rõ ngày nhận.",
            "Không ký đơn xin nghỉ việc hay biên bản theo mẫu công ty đưa nếu nội dung không đúng sự thật.",
            "Thời hiệu yêu cầu Tòa án giải quyết tranh chấp lao động cá nhân là 01 năm – đừng để quá lâu.",
        ],
        "docs": [
            "Hợp đồng, phụ lục, mô tả công việc và hồ sơ nhân sự",
            "Nội quy, quy chế, thông báo và biên bản liên quan",
            "Bảng lương, chấm công, bảo hiểm và chứng từ thanh toán",
            "Email, tin nhắn, đánh giá công việc hoặc đơn khiếu nại",
        ],
        "deliverables": [
            "Đánh giá căn cứ và rủi ro của từng hướng xử lý",
            "Các bước cần làm và mẫu văn bản cần dùng",
            "Văn bản nhân sự được soạn hoặc rà soát",
            "Phương án thương lượng và đại diện khi tranh chấp",
        ],
        "principle_title": "Phòng ngừa hơn chữa cháy",
        "principle_text": "Hồ sơ lao động được thiết kế để áp dụng được trong thực tế, đồng thời đủ căn cứ chứng minh khi cơ quan quản lý kiểm tra hoặc khi có tranh chấp.",
        "steps": [
            ("Nghe anh chị kể", "Hợp đồng, vị trí công việc và chuyện đang xảy ra."),
            ("Rà soát quy trình", "Căn cứ, thời hạn, thẩm quyền và chứng cứ."),
            ("Cân nhắc lựa chọn", "Giải quyết nội bộ, thỏa thuận hay tranh chấp."),
            ("Chuẩn bị văn bản", "Soạn giấy tờ và hướng dẫn từng bước thực hiện."),
            ("Theo dõi kết quả", "Kiểm tra thanh toán, bàn giao và nghĩa vụ còn lại."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Kỷ luật hoặc cho nghỉ việc sai căn cứ, sai thời hiệu hay sai thủ tục có thể khiến doanh nghiệp phải nhận lại người lao động, trả lương và bồi thường.",
        "faq": [
            ("Bị cho nghỉ việc trái luật, tôi có quyền đòi gì?",
             "Nếu người sử dụng lao động đơn phương chấm dứt hợp đồng trái pháp luật, họ phải nhận anh chị trở lại làm việc, trả tiền lương, đóng bảo hiểm cho những ngày không được làm việc và trả thêm ít nhất 02 tháng tiền lương theo hợp đồng; nếu anh chị không muốn quay lại thì còn được trả trợ cấp thôi việc (<strong>Điều 41 Bộ luật Lao động 2019</strong>)."),
            ("Thời hạn khởi kiện tranh chấp lao động là bao lâu?",
             "Thời hiệu yêu cầu Tòa án giải quyết tranh chấp lao động cá nhân là 01 năm kể từ ngày phát hiện ra hành vi mà anh chị cho rằng quyền, lợi ích hợp pháp của mình bị vi phạm (<strong>khoản 3 Điều 190 Bộ luật Lao động 2019</strong>). Một số tranh chấp như bị sa thải, bị đơn phương chấm dứt hợp đồng có thể yêu cầu Tòa án giải quyết mà không bắt buộc qua hòa giải viên lao động (<strong>Điều 188</strong>)."),
        ],
        "laws": ["Bộ luật Lao động 2019", "Luật Bảo hiểm xã hội 2024", "Bộ luật Tố tụng dân sự 2015 (sửa đổi, bổ sung)"],
        "cta_title": "Biết rõ quyền lợi trước khi ký bất cứ giấy tờ gì",
        "cta_text": "Gọi điện hoặc nhắn Zalo kể ngắn gọn chuyện đang xảy ra ở nơi làm việc. Luật sư sẽ cho biết anh chị cần giữ lại giấy tờ gì và nên làm gì trước.",
        "related": ["tranh-tung-giai-quyet-tranh-chap", "dan-su", "hinh-su"],
    },
    {
        "slug": "hinh-su",
        "name": "Hình sự",
        "icon": "i-shield-check",
        "problem_icon": "i-shield",
        "short": "Bào chữa, bảo vệ người bị hại và đồng hành cùng khách hàng trong các giai đoạn điều tra, truy tố, xét xử.",
        "title": "Luật sư bào chữa vụ án Hình sự",
        "seo_title": "Luật sư bào chữa vụ án hình sự tại TP.HCM",
        "description": "Luật sư bào chữa cho người bị buộc tội và bảo vệ quyền lợi bị hại qua các giai đoạn điều tra, truy tố, xét xử, kháng cáo. Hỗ trợ khẩn cấp 0983 498 499.",
        "image": "assets/img/luat-su-nam.webp",
        "image_size": (800, 812),
        "image_alt": "Luật sư Nguyễn Trọng Nam tại ghế người bào chữa trong phòng xử án",
        "urgent": True,
        "problem_title": "Người nhà bị công an mời, bị bắt",
        "problem_text": "Cần luật sư bào chữa, gặp người bị tạm giữ, tạm giam, hoặc bảo vệ quyền lợi cho người bị hại.",
        "hero_title": "Người thân gặp chuyện hình sự – <em>cần luật sư càng sớm càng tốt</em>",
        "lead": "Nhận giấy mời của công an, người thân bị tạm giữ, tạm giam, hay anh chị là người bị hại cần được bồi thường. Giai đoạn đầu rất quan trọng: luật sư giúp anh chị hiểu quyền của mình, làm thủ tục tham gia vụ án và bảo vệ quyền lợi theo đúng pháp luật.",
        "situations": [
            "Người thân bị bắt, bị tạm giữ; gia đình chưa biết đang ở đâu, cần làm gì.",
            "Nhận giấy mời, giấy triệu tập của cơ quan công an và lo lắng không biết trình bày thế nào.",
            "Người nhà đã bị khởi tố, cần luật sư bào chữa ở giai đoạn điều tra, truy tố, xét xử.",
            "Bị lừa đảo, chiếm đoạt tài sản, bị đánh gây thương tích – muốn tố giác và đòi bồi thường.",
            "Đã có bản án sơ thẩm, gia đình muốn kháng cáo.",
        ],
        "scope_intro": "Vụ án hình sự cần được xử lý thận trọng ngay từ buổi làm việc đầu tiên. Luật sư nghiên cứu hồ sơ, đối chiếu chứng cứ, theo dõi thủ tục và xây dựng luận điểm bào chữa hoặc bảo vệ trên cơ sở pháp luật và sự thật khách quan.",
        "scope": [
            ("Tư vấn ban đầu", "Giải thích quyền, nghĩa vụ, các bước tố tụng; hướng dẫn chuẩn bị giấy tờ trước khi làm việc với cơ quan tiến hành tố tụng."),
            ("Bào chữa cho người bị buộc tội", "Tham gia từ giai đoạn tạm giữ, điều tra, truy tố, xét xử; nghiên cứu hồ sơ và xây dựng luận cứ bào chữa."),
            ("Bảo vệ người bị hại", "Tư vấn tố giác, yêu cầu khởi tố, bồi thường; bảo vệ quyền lợi của người bị hại trong vụ án."),
            ("Chứng cứ và kiến nghị", "Thu thập, giao nộp, đánh giá tài liệu; đề nghị, khiếu nại quyết định, hành vi tố tụng khi có căn cứ."),
            ("Kháng cáo", "Đánh giá bản án, tư vấn phạm vi kháng cáo, chuẩn bị đơn và luận cứ cho phiên phúc thẩm."),
            ("Bồi thường dân sự trong vụ án", "Tư vấn thiệt hại, hoàn trả, bồi thường, tài sản bị thu giữ và các quyền lợi dân sự liên quan."),
        ],
        "tips": [
            "Ghi lại tên cơ quan, cán bộ thụ lý, số điện thoại, thời gian và nơi người thân được đưa đến.",
            "Giữ nguyên giấy mời, quyết định, biên bản đã nhận; chụp ảnh lại toàn bộ.",
            "Nói thật với luật sư; không xóa, sửa tài liệu, không bàn bạc để thống nhất lời khai sai sự thật.",
            "Thời hạn kháng cáo bản án hình sự sơ thẩm chỉ 15 ngày kể từ ngày tuyên án.",
        ],
        "docs": [
            "Giấy mời, giấy triệu tập, quyết định hoặc biên bản đã nhận",
            "Tài liệu, dữ liệu, chứng từ liên quan đến sự việc",
            "Diễn biến sự việc theo thời gian và thông tin người làm chứng",
            "Giấy tờ về nhân thân, việc khắc phục hậu quả hoặc thiệt hại",
        ],
        "deliverables": [
            "Giải thích rõ quyền, nghĩa vụ và giai đoạn tố tụng",
            "Đánh giá hồ sơ và định hướng làm việc phù hợp",
            "Luận cứ, đơn từ và kiến nghị theo phạm vi dịch vụ",
            "Luật sư tham gia tố tụng khi đủ điều kiện, thủ tục",
        ],
        "principle_title": "Trung thực và đúng pháp luật",
        "principle_text": "Luật sư giữ kín thông tin, tôn trọng sự thật khách quan, không hướng dẫn khai báo gian dối hay cản trở hoạt động tố tụng. Mọi luận điểm đều dựa trên chứng cứ và quy định pháp luật.",
        "steps": [
            ("Tiếp nhận gấp", "Giai đoạn vụ việc, cơ quan thụ lý và lịch làm việc gần nhất."),
            ("Xem giấy tờ", "Quyết định, biên bản, chứng cứ và thông tin ban đầu."),
            ("Đăng ký tham gia", "Làm thủ tục bào chữa hoặc bảo vệ quyền lợi."),
            ("Nghiên cứu hồ sơ", "Xây dựng luận điểm, giao nộp tài liệu, kiến nghị."),
            ("Tham gia tố tụng", "Có mặt tại buổi làm việc, phiên tòa và giai đoạn sau đó."),
        ],
        "note_title": "Lưu ý quan trọng",
        "note_text": "Không xóa, sửa, che giấu tài liệu hoặc trao đổi nhằm thống nhất lời khai sai sự thật. Hãy cung cấp thông tin trung thực để luật sư tư vấn đúng.",
        "faq": [
            ("Người thân bị bắt, khi nào luật sư được tham gia?",
             "Trường hợp bắt, tạm giữ người, người bào chữa được tham gia tố tụng từ khi người bị bắt có mặt tại trụ sở cơ quan điều tra, cơ quan được giao nhiệm vụ tiến hành một số hoạt động điều tra hoặc từ khi có quyết định tạm giữ (<strong>Điều 74 Bộ luật Tố tụng hình sự 2015</strong>). Người thân thích của người bị buộc tội có quyền lựa chọn người bào chữa cho họ (<strong>Điều 75</strong>), nên gia đình có thể liên hệ luật sư ngay."),
            ("Nhận giấy mời của công an, tôi có nên đi một mình?",
             "Không nên phớt lờ. Hãy đọc kỹ giấy mời, giấy triệu tập để biết anh chị được mời với tư cách gì và nội dung làm việc. Nếu lo ngại vụ việc liên quan đến mình, nên trao đổi với luật sư trước buổi làm việc để hiểu quyền, nghĩa vụ và cách trình bày trung thực, đúng trọng tâm. Tùy tư cách tham gia, anh chị có thể nhờ luật sư bảo vệ quyền lợi."),
            ("Thời hạn kháng cáo bản án hình sự là bao lâu?",
             "Thời hạn kháng cáo bản án sơ thẩm là 15 ngày kể từ ngày tuyên án; với người vắng mặt tại phiên tòa thì tính từ ngày họ nhận được bản án hoặc bản án được niêm yết (<strong>Điều 333 Bộ luật Tố tụng hình sự 2015</strong>)."),
        ],
        "laws": ["Bộ luật Hình sự 2015 (sửa đổi, bổ sung 2017, 2025)", "Bộ luật Tố tụng hình sự 2015 (sửa đổi, bổ sung)", "Luật Luật sư 2006 (sửa đổi, bổ sung 2012)"],
        "cta_title": "Việc hình sự cần luật sư từ giai đoạn đầu",
        "cta_text": "Gọi ngay hotline để luật sư biết vụ việc đang ở giai đoạn nào và việc gì cần làm trước. Chuẩn bị sẵn giấy mời, quyết định hoặc biên bản đã nhận.",
        "related": ["tranh-tung-giai-quyet-tranh-chap", "dan-su", "lao-dong-viec-lam"],
    },
    {
        "slug": "dan-su",
        "name": "Dân sự",
        "icon": "i-scale",
        "short": "Tư vấn hợp đồng, nghĩa vụ, bồi thường, tài sản và đại diện giải quyết tranh chấp dân sự theo đúng trình tự.",
        "title": "Luật sư tư vấn Dân sự",
        "seo_title": "Luật sư dân sự, tranh chấp hợp đồng tại TP.HCM",
        "description": "Tư vấn hợp đồng, nghĩa vụ dân sự, bồi thường thiệt hại, quyền tài sản và đại diện giải quyết tranh chấp dân sự đúng trình tự tố tụng.",
        "image_alt": "Khu cao ốc văn phòng tại thành phố",
        "problem_title": "Cho vay không trả, hợp đồng bị bội tín",
        "problem_text": "Đòi nợ, đòi bồi thường thiệt hại, tranh chấp hợp đồng mua bán, thuê nhà, hợp tác làm ăn.",
        "hero_title": "Đòi nợ, đòi bồi thường, tranh chấp hợp đồng – <em>đúng cách, có căn cứ</em>",
        "lead": "Cho người quen vay tiền mà không trả, thuê nhà bị đòi lại trước hạn, bị gây thiệt hại mà không được bồi thường. Luật sư giúp anh chị xem giấy tờ, tin nhắn đang có đã đủ chứng minh chưa và chọn cách đòi lại quyền lợi hiệu quả nhất.",
        "situations": [
            "Cho vay tiền, cho mượn tài sản nhưng người vay khất lần, né tránh.",
            "Cho vay không làm giấy, chỉ có chuyển khoản hoặc tin nhắn.",
            "Hợp đồng mua bán, thuê nhà, dịch vụ bị bên kia vi phạm.",
            "Bị gây thiệt hại về tài sản, sức khỏe, danh dự và muốn đòi bồi thường.",
            "Tài sản chung với người khác, không thống nhất được cách sử dụng hoặc chia.",
        ],
        "scope_intro": "Tranh chấp dân sự thường bắt đầu từ thỏa thuận miệng, giấy tờ sơ sài hoặc chứng cứ rời rạc. Luật sư sắp xếp lại diễn biến, xác định quyền và nghĩa vụ của mỗi bên, rồi đề xuất cách xử lý khả thi nhất.",
        "scope": [
            ("Hợp đồng dân sự", "Soạn, rà soát và xử lý tranh chấp hợp đồng vay, thuê, mua bán, đặt cọc, dịch vụ, hợp tác."),
            ("Vay nợ, đòi tiền", "Đánh giá chứng cứ vay, lãi, thời hạn; soạn yêu cầu thanh toán và đại diện đòi khoản nợ hợp pháp."),
            ("Bồi thường thiệt hại", "Xác định hành vi, thiệt hại, mối liên hệ nhân quả và mức yêu cầu bồi thường về tài sản, sức khỏe, danh dự."),
            ("Quyền sở hữu, tài sản", "Tư vấn quản lý, sử dụng, định đoạt tài sản; tranh chấp sở hữu chung, đòi lại tài sản."),
            ("Thương lượng thay anh chị", "Soạn thư yêu cầu, tham gia thương lượng, hòa giải, làm việc với cá nhân, tổ chức theo phạm vi ủy quyền."),
            ("Khởi kiện và thi hành án", "Chuẩn bị hồ sơ khởi kiện, bảo vệ quyền lợi tại Tòa án và theo dõi việc thi hành bản án."),
        ],
        "tips": [
            "Lưu giữ giấy vay, biên nhận, sao kê chuyển khoản; xuất tin nhắn, ghi âm ra bản lưu và giữ nguyên thiết bị gốc.",
            "Gửi yêu cầu trả nợ bằng văn bản hoặc tin nhắn có nội dung rõ ràng để làm căn cứ.",
            "Không tự ý đến nhà siết tài sản hay đăng thông tin lên mạng xã hội để đòi nợ – có thể vi phạm pháp luật.",
            "Thời hiệu khởi kiện tranh chấp hợp đồng là 03 năm – đừng để quá lâu.",
        ],
        "docs": [
            "Hợp đồng, giấy vay, biên nhận và chứng từ thanh toán",
            "Email, tin nhắn, ghi nhận giao nhận hoặc cam kết",
            "Giấy tờ tài sản và tài liệu chứng minh thiệt hại",
            "Đơn từ, biên bản, quyết định đã có",
        ],
        "deliverables": [
            "Đánh giá quyền, nghĩa vụ, thời hiệu và chứng cứ",
            "Phương án thương lượng hoặc khởi kiện có lộ trình",
            "Thư yêu cầu, đơn từ và văn bản được soạn sẵn",
            "Đại diện làm việc và cập nhật tiến độ theo thỏa thuận",
        ],
        "principle_title": "Đòi được mới là quan trọng",
        "principle_text": "Phương án được xây dựng từ mục tiêu thực tế, số tiền tranh chấp, khả năng chứng minh và khả năng thi hành; tránh kéo dài thủ tục khi có thể đạt thỏa thuận an toàn hơn.",
        "steps": [
            ("Nghe anh chị kể", "Các bên, giao dịch và các mốc thời gian."),
            ("Xem chứng cứ", "Hiệu lực giao dịch, thời hiệu và tài liệu còn thiếu."),
            ("Bàn cách làm", "So sánh thương lượng, hòa giải và khởi kiện."),
            ("Thực hiện", "Soạn văn bản và đại diện theo phạm vi ủy quyền."),
            ("Theo dõi thi hành", "Hỗ trợ thực hiện thỏa thuận, bản án hoặc quyết định."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Hãy giữ bản gốc giấy tờ, dữ liệu điện tử và chứng từ. Thời hiệu có thể làm mất quyền yêu cầu nên hồ sơ cần được xem sớm.",
        "faq": [
            ("Cho vay không làm giấy tờ thì có đòi được không?",
             "Có thể. Hợp đồng vay không bắt buộc phải lập thành văn bản; sao kê chuyển khoản, tin nhắn, ghi âm, người làm chứng đều có thể là chứng cứ nếu thể hiện được việc vay và nghĩa vụ trả. Điều quan trọng là thu thập và lưu giữ đúng cách để Tòa án có thể xem xét."),
            ("Thời hạn khởi kiện tranh chấp hợp đồng là bao lâu?",
             "Thời hiệu khởi kiện yêu cầu Tòa án giải quyết tranh chấp hợp đồng là 03 năm kể từ ngày người có quyền yêu cầu biết hoặc phải biết quyền và lợi ích hợp pháp của mình bị xâm phạm (<strong>Điều 429 Bộ luật Dân sự 2015</strong>)."),
            ("Lãi suất cho vay bao nhiêu thì đúng luật?",
             "Lãi suất do các bên thỏa thuận nhưng không được vượt quá 20%/năm của khoản tiền vay, trừ trường hợp luật khác có liên quan quy định khác; phần lãi vượt quá không có hiệu lực (<strong>Điều 468 Bộ luật Dân sự 2015</strong>)."),
        ],
        "laws": ["Bộ luật Dân sự 2015", "Bộ luật Tố tụng dân sự 2015 (sửa đổi, bổ sung)", "Luật Thi hành án dân sự"],
        "cta_title": "Chứng cứ đầy đủ giúp đòi lại quyền lợi dễ hơn",
        "cta_text": "Chuẩn bị sẵn hợp đồng, giấy vay, tin nhắn đang có rồi gọi điện hoặc nhắn Zalo cho luật sư. Luật sư sẽ cho biết chứng cứ đã đủ chưa và nên làm gì trước.",
        "related": ["tranh-tung-giai-quyet-tranh-chap", "dat-dai-bat-dong-san", "cong-chung"],
    },
    {
        "slug": "cong-chung",
        "name": "Công chứng",
        "icon": "i-doc",
        "short": "Hỗ trợ chuẩn bị hồ sơ, rà soát giao dịch và kết nối công chứng hợp đồng, di chúc, ủy quyền, mua bán, tặng cho.",
        "title": "Hỗ trợ thủ tục Công chứng hợp đồng, di chúc",
        "description": "Hỗ trợ chuẩn bị hồ sơ, rà soát giao dịch và kết nối công chứng hợp đồng mua bán, tặng cho, di chúc, văn bản ủy quyền đúng quy định pháp luật.",
        "image_alt": "Bút ký đặt trên văn bản hợp đồng",
        "problem_title": "Công chứng hợp đồng, di chúc, ủy quyền",
        "problem_text": "Kiểm tra giấy tờ, soạn nội dung đúng ý trước khi ký mua bán, tặng cho, lập di chúc, ủy quyền.",
        "hero_title": "Giấy tờ công chứng <em>đủ và đúng ngay từ lần đầu</em>",
        "lead": "Sắp ký mua bán, tặng cho nhà đất, lập di chúc hay làm giấy ủy quyền? Luật sư kiểm tra giấy tờ, giải thích từng điều khoản trước khi anh chị ký, và phối hợp với tổ chức hành nghề công chứng để buổi công chứng diễn ra suôn sẻ.",
        "situations": [
            "Sắp ký hợp đồng mua bán, tặng cho nhà đất và muốn có người đọc kỹ trước khi ký.",
            "Muốn lập di chúc nhưng không biết viết thế nào cho có hiệu lực, tránh tranh chấp về sau.",
            "Cần ủy quyền cho người thân làm thủ tục khi mình ở xa hoặc ở nước ngoài.",
            "Hồ sơ bị trả lại vì thiếu giấy tờ, không biết cần bổ sung gì.",
            "Vợ chồng muốn lập văn bản thỏa thuận tài sản chung, tài sản riêng.",
        ],
        "scope_intro": "Luật sư kiểm tra hồ sơ, giải thích quyền và nghĩa vụ, đề xuất điều khoản và phối hợp với tổ chức hành nghề công chứng. Việc công chứng do công chứng viên thực hiện tại tổ chức hành nghề công chứng có thẩm quyền.",
        "scope": [
            ("Nhà đất và tài sản phải đăng ký", "Rà soát hồ sơ mua bán, tặng cho, thế chấp, góp vốn, thuê và các giao dịch cần công chứng về tài sản."),
            ("Văn bản ủy quyền", "Làm rõ phạm vi, thời hạn, quyền và nghĩa vụ; soạn giấy ủy quyền hoặc hợp đồng ủy quyền đúng mục đích sử dụng."),
            ("Di chúc và thừa kế", "Chuẩn bị di chúc, văn bản khai nhận, thỏa thuận phân chia hoặc từ chối nhận di sản cùng giấy tờ cần thiết."),
            ("Thỏa thuận tài sản vợ chồng", "Hỗ trợ thỏa thuận tài sản vợ chồng, chia tài sản chung, xác nhận tài sản riêng và văn bản liên quan."),
            ("Giấy tờ nước ngoài", "Kiểm tra giấy tờ nước ngoài, bản dịch, hợp pháp hóa lãnh sự, ủy quyền và yêu cầu xác định danh tính."),
            ("Đọc kỹ trước khi ký", "Giải thích điều khoản, thuế phí, điều kiện bàn giao, thanh toán và rủi ro trước khi anh chị ký."),
        ],
        "tips": [
            "Mang bản chính giấy tờ tùy thân, giấy tờ tài sản và giấy tờ về tình trạng hôn nhân khi đi công chứng.",
            "Đọc kỹ toàn bộ văn bản trước khi ký; hỏi lại ngay những điều khoản chưa hiểu.",
            "Ghi giá trong hợp đồng đúng thực tế; ghi giá thấp hơn để giảm thuế có thể bất lợi khi tranh chấp và vi phạm pháp luật về thuế.",
            "Giữ một bản hợp đồng đã công chứng cùng các biên nhận thanh toán.",
        ],
        "docs": [
            "Căn cước, hộ chiếu và giấy tờ về tình trạng hôn nhân",
            "Giấy tờ chứng minh quyền sở hữu, sử dụng tài sản",
            "Dự thảo, thỏa thuận và giấy tờ giao dịch trước đó",
            "Giấy tờ đại diện, ủy quyền hoặc tài liệu nước ngoài",
        ],
        "docs_title": "Hồ sơ thường cần",
        "deliverables": [
            "Danh mục giấy tờ đúng với loại giao dịch",
            "Văn bản được luật sư rà soát trước khi ký",
            "Giải thích nghĩa vụ, rủi ro và việc cần làm sau công chứng",
            "Hỗ trợ sắp xếp lịch với tổ chức hành nghề công chứng",
        ],
        "principle_title": "Phân định rõ vai trò",
        "principle_text": "Công Ty Luật TNHH Luật Sư Nam tư vấn pháp lý và hỗ trợ chuẩn bị hồ sơ. Việc công chứng, lời chứng và quyết định tiếp nhận hồ sơ thuộc thẩm quyền của công chứng viên, tổ chức hành nghề công chứng.",
        "steps": [
            ("Nghe anh chị kể", "Ai ký, tài sản gì, mục đích và thời gian dự kiến."),
            ("Kiểm tra điều kiện", "Giấy tờ, quyền định đoạt và hạn chế pháp lý."),
            ("Hoàn thiện văn bản", "Đề xuất điều khoản và chuẩn bị hồ sơ cần nộp."),
            ("Phối hợp công chứng", "Bổ sung hồ sơ theo yêu cầu hợp lệ, sắp xếp lịch ký."),
            ("Sau khi ký", "Thanh toán, đăng ký sang tên và nghĩa vụ tiếp theo."),
        ],
        "note_title": "Lưu ý",
        "note_text": "Danh mục giấy tờ và việc tiếp nhận phụ thuộc từng giao dịch, tình trạng tài sản và yêu cầu của tổ chức hành nghề công chứng.",
        "faq": [
            ("Hợp đồng nào bắt buộc phải công chứng?",
             "Ví dụ: hợp đồng chuyển nhượng, tặng cho, thế chấp, góp vốn bằng quyền sử dụng đất phải được công chứng hoặc chứng thực theo <strong>Luật Đất đai 2024</strong> (trừ một số trường hợp kinh doanh bất động sản); hợp đồng mua bán, tặng cho nhà ở cũng phải công chứng hoặc chứng thực theo <strong>Luật Nhà ở 2023</strong>, trừ một số trường hợp luật định. Luật sư sẽ xác định yêu cầu cụ thể với giao dịch của anh chị."),
            ("Di chúc có bắt buộc phải công chứng không?",
             "Không bắt buộc. Di chúc bằng văn bản có thể có hoặc không có người làm chứng, có công chứng hoặc chứng thực; mỗi loại có điều kiện riêng để hợp pháp (<strong>Điều 628, 630 Bộ luật Dân sự 2015</strong>). Công chứng di chúc giúp hạn chế tranh cãi về sau, nhất là với người cao tuổi hoặc tài sản giá trị lớn."),
            ("Luật sư có công chứng hợp đồng được không?",
             "Không. Việc công chứng do công chứng viên thực hiện tại tổ chức hành nghề công chứng. Luật sư giúp anh chị kiểm tra điều kiện giao dịch, soạn hoặc rà soát văn bản, giải thích quyền và nghĩa vụ, chuẩn bị hồ sơ và sắp xếp lịch ký."),
        ],
        "laws": ["Luật Công chứng 2024", "Bộ luật Dân sự 2015", "Luật Đất đai 2024", "Luật Nhà ở 2023"],
        "cta_title": "Hồ sơ đủ, buổi công chứng sẽ nhẹ nhàng hơn",
        "cta_text": "Nhắn Zalo cho luật sư loại giấy tờ cần làm và những giấy tờ anh chị đang có. Luật sư sẽ cho biết cần chuẩn bị thêm gì.",
        "related": ["thua-ke", "dat-dai-bat-dong-san", "hon-nhan-gia-dinh"],
    },
]
SERVICE_BY_SLUG = {s["slug"]: s for s in SERVICES}

# Thứ tự thẻ "Anh chị đang gặp chuyện gì?" (trang chủ, trang Dịch vụ): việc người dân hay gặp nhất đứng trước
PROBLEM_ORDER = ["thua-ke", "dat-dai-bat-dong-san", "hon-nhan-gia-dinh", "hinh-su",
                 "dan-su", "lao-dong-viec-lam", "tranh-tung-giai-quyet-tranh-chap", "cong-chung"]

# ---------------------------------------------------------------------------
# Bài viết pháp lý. Nội dung từng bài: src/bai-viet/<slug>.html
# key_points: 3–4 ý chính hiện ở khung "Tóm tắt nhanh" đầu bài.
# ---------------------------------------------------------------------------
ARTICLES = [
    {
        "slug": "thoi-hieu-chia-di-san-thua-ke",
        "title": "Thời hiệu chia di sản thừa kế: mốc 30 năm, 10 năm và 03 năm theo Bộ luật Dân sự 2015",
        "card_title": "Thời hiệu chia di sản thừa kế: mốc 30 năm, 10 năm và 03 năm",
        "seo_title": "Thời hiệu chia di sản thừa kế theo Bộ luật Dân sự 2015",
        "description": "Thời hiệu chia di sản: 30 năm với bất động sản, 10 năm với động sản (Điều 623 Bộ luật Dân sự 2015). Hệ quả khi hết thời hiệu và việc cần làm sớm.",
        "excerpt": "Mốc tính thời hiệu, ba loại thời hiệu tại Điều 623 Bộ luật Dân sự 2015 và điều gì xảy ra với di sản khi hết thời hạn.",
        "key_points": [
            "Mọi thời hiệu thừa kế tính từ thời điểm mở thừa kế, tức ngày người để lại di sản chết.",
            "Yêu cầu chia di sản: 30 năm với nhà đất, 10 năm với động sản.",
            "Hết thời hiệu, di sản thuộc về người thừa kế đang quản lý di sản đó.",
            "Tòa án chỉ áp dụng thời hiệu khi có bên yêu cầu trước khi cấp sơ thẩm ra bản án, quyết định.",
        ],
        "service": "thua-ke",
        "category": "Thừa kế",
        "published": "2026-09-15",
        "modified": "2026-09-24",
        "image_alt": "Luật sư ký văn bản thỏa thuận phân chia di sản",
        "related_services": ["thua-ke", "cong-chung", "tranh-tung-giai-quyet-tranh-chap"],
    },
    {
        "slug": "ly-hon-don-phuong",
        "title": "Ly hôn đơn phương: căn cứ, hồ sơ và cách Tòa án xem xét quyền nuôi con",
        "card_title": "Ly hôn đơn phương: căn cứ, hồ sơ và quyền nuôi con",
        "seo_title": "Ly hôn đơn phương: căn cứ, hồ sơ, quyền nuôi con",
        "description": "Khi nào Tòa án giải quyết ly hôn theo yêu cầu của một bên, hồ sơ cần chuẩn bị, Tòa án có thẩm quyền và nguyên tắc giao con, cấp dưỡng, chia tài sản chung.",
        "excerpt": "Căn cứ ly hôn theo Điều 56 Luật Hôn nhân và Gia đình 2014, hồ sơ khởi kiện, quyền nuôi con và chia tài sản chung.",
        "key_points": [
            "Tòa án chỉ cho ly hôn theo yêu cầu của một bên khi có căn cứ tại Điều 56 Luật Hôn nhân và Gia đình 2014.",
            "Chồng không có quyền yêu cầu ly hôn khi vợ đang có thai, sinh con hoặc nuôi con dưới 12 tháng tuổi.",
            "Con dưới 36 tháng tuổi được giao cho mẹ trực tiếp nuôi, trừ ngoại lệ; con từ đủ 07 tuổi được xem xét nguyện vọng.",
            "Tài sản chung về nguyên tắc chia đôi nhưng có tính đến công sức đóng góp và lỗi của mỗi bên.",
        ],
        "service": "hon-nhan-gia-dinh",
        "category": "Hôn nhân & Gia đình",
        "published": "2026-09-10",
        "modified": "2026-10-07",
        "image_alt": "Búa phán quyết trên bàn xét xử của Tòa án",
        "related_services": ["hon-nhan-gia-dinh", "tranh-tung-giai-quyet-tranh-chap", "cong-chung"],
    },
    {
        "slug": "dat-coc-mua-ban-nha-dat",
        "title": "Đặt cọc mua bán nhà đất: 6 điểm cần kiểm tra trước khi xuống tiền",
        "card_title": "Đặt cọc mua bán nhà đất: 6 điểm cần kiểm tra trước khi xuống tiền",
        "seo_title": "Đặt cọc mua bán nhà đất: 6 điểm cần kiểm tra",
        "description": "Hậu quả của đặt cọc theo Điều 328 Bộ luật Dân sự 2015 và 6 điểm cần kiểm tra trước khi đặt cọc mua nhà đất: chủ thể, điều kiện chuyển nhượng, quy hoạch.",
        "excerpt": "Phạt cọc hoạt động thế nào, điều kiện chuyển nhượng theo Luật Đất đai 2024 và những điều khoản nên có trong hợp đồng đặt cọc.",
        "key_points": [
            "Bên bán từ chối thực hiện: trả lại cọc và thêm một khoản tương đương; bên mua từ chối: mất cọc – trừ khi có thỏa thuận khác.",
            "Kiểm tra người ký có đủ quyền định đoạt, nhất là nhà đất là tài sản chung vợ chồng.",
            "Thửa đất phải đủ điều kiện chuyển nhượng theo Luật Đất đai 2024.",
            "Ưu tiên chuyển khoản, ghi rõ nội dung; không đặt cọc lớn khi hồ sơ chưa rõ ràng.",
        ],
        "service": "dat-dai-bat-dong-san",
        "category": "Đất đai & Bất động sản",
        "published": "2026-09-05",
        "modified": "2026-09-24",
        "image_alt": "Khu cao ốc và nhà ở tại đô thị",
        "related_services": ["dat-dai-bat-dong-san", "cong-chung", "dan-su"],
    },
]
ARTICLE_BY_SLUG = {a["slug"]: a for a in ARTICLES}


def articles_for_service(slug):
    return [a for a in ARTICLES if slug in a["related_services"]]


# ---------------------------------------------------------------------------
# Câu hỏi thường gặp (chuyển từ trang Liên hệ của website cũ)
# ---------------------------------------------------------------------------
FAQ = [
    {
        "id": "chi-phi-thue-luat-su",
        "q": "Chi phí thuê luật sư được tính như thế nào?",
        "a": [
            "Thù lao luật sư được hai bên thỏa thuận trước và ghi trong hợp đồng dịch vụ pháp lý. Theo <strong>Điều 55 Luật Luật sư</strong>, căn cứ tính thù lao gồm nội dung và tính chất của dịch vụ, thời gian và công sức của luật sư, cùng kinh nghiệm và uy tín của luật sư.",
            "Cũng theo điều luật này, thù lao có thể tính theo <strong>giờ làm việc</strong>, theo <strong>vụ việc với mức trọn gói</strong>, theo <strong>tỷ lệ phần trăm</strong> giá ngạch vụ kiện hoặc giá trị hợp đồng, hoặc theo <strong>hợp đồng dài hạn</strong> với mức cố định. Luật sư đề xuất cách tính phù hợp với từng vụ việc và báo trước mọi khoản phát sinh. Xem thêm <a href=\"{{root}}vi-sao-chon-chung-toi/\">cam kết minh bạch về chi phí</a>.",
        ],
    },
    {
        "id": "cam-ket-thang-kien",
        "q": "Luật sư có cam kết chắc chắn thắng kiện không?",
        "a": [
            "Không. Luật sư phân tích thẳng thắn điểm mạnh, điểm yếu trong hồ sơ và khả năng thành công dựa trên chứng cứ cùng quy định pháp luật, nhưng không cam kết bảo đảm kết quả.",
            "Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư Việt Nam nghiêm cấm luật sư hứa hẹn, cam kết bảo đảm kết quả vụ việc về những nội dung nằm ngoài khả năng và điều kiện thực hiện của luật sư (<strong>Quy tắc 9.1.6</strong>). Nếu một đơn vị cam kết chắc chắn thắng kiện, đó là dấu hiệu anh chị nên cân nhắc rất kỹ.",
        ],
    },
    {
        "id": "bao-mat-thong-tin",
        "q": "Thông tin tôi cung cấp có được giữ bí mật không?",
        "a": [
            "Có. Luật sư không được tiết lộ thông tin về vụ việc, về khách hàng mà mình biết được trong khi hành nghề, trừ trường hợp được khách hàng đồng ý bằng văn bản hoặc pháp luật có quy định khác, theo <strong>Điều 25 Luật Luật sư</strong> và <strong>Quy tắc 7</strong> Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư Việt Nam.",
            "Nghĩa vụ bảo mật áp dụng ngay từ buổi trao đổi đầu tiên, kể cả khi sau đó hai bên không ký hợp đồng dịch vụ, và vẫn tiếp tục có hiệu lực sau khi vụ việc kết thúc.",
        ],
    },
    {
        "id": "chuan-bi-buoi-dau",
        "q": "Buổi trao đổi đầu tiên tôi cần chuẩn bị những gì?",
        "a": [
            "Anh chị nên mang theo bản sao các giấy tờ đang có: hợp đồng, giấy tờ về tài sản, thông báo hoặc quyết định đã nhận từ cơ quan nhà nước, tin nhắn và email trao đổi giữa các bên.",
            "Quan trọng không kém là một bản tóm tắt diễn biến theo thứ tự thời gian và câu trả lời cho câu hỏi: anh chị mong muốn đạt được điều gì. Danh mục chi tiết có tại trang <a href=\"{{root}}quy-trinh-lam-viec/\">Quy trình làm việc</a> và trang của từng <a href=\"{{root}}dich-vu/\">lĩnh vực dịch vụ</a>.",
        ],
    },
    {
        "id": "thoi-han-quan-trong",
        "q": "Vì sao thời hạn lại quan trọng đến vậy?",
        "a": [
            "Pháp luật quy định thời hiệu khởi kiện và thời hạn thực hiện quyền cho từng loại vụ việc. Khi thời hiệu đã hết và có đương sự yêu cầu áp dụng, quyền khởi kiện có thể không còn được bảo vệ, dù yêu cầu của anh chị là có căn cứ. Ví dụ điển hình là <a href=\"{{root}}kien-thuc-phap-ly/thoi-hieu-chia-di-san-thua-ke/\">thời hiệu chia di sản thừa kế</a>.",
            "Tương tự, thời hạn kháng cáo bản án, thời hạn khiếu nại quyết định hành chính đều rất ngắn. Vì vậy anh chị nên liên hệ luật sư <strong>càng sớm càng tốt</strong>, ngay khi nhận được văn bản đầu tiên.",
        ],
    },
    {
        "id": "vu-viec-ngoai-tphcm",
        "q": "Công ty có nhận vụ việc ngoài Thành phố Hồ Chí Minh không?",
        "a": [
            "Có. Luật sư Việt Nam được hành nghề trên phạm vi toàn quốc, nên chúng tôi nhận tư vấn và tham gia tố tụng tại các tỉnh, thành phố khác.",
            "Với vụ việc ở xa, phần lớn công đoạn tư vấn và chuẩn bị hồ sơ có thể thực hiện trực tuyến; chi phí đi lại (nếu có) được thông báo và thống nhất trước khi phát sinh.",
        ],
    },
    {
        "id": "thoi-gian-phan-hoi",
        "q": "Liên hệ luật sư bằng cách nào và bao lâu được phản hồi?",
        "a": [
            "Website chỉ cung cấp thông tin pháp lý tham khảo, không nhận yêu cầu tư vấn trực tuyến. Anh chị liên hệ trực tiếp qua hotline hoặc Zalo <a href=\"https://zalo.me/0983498499\">0983 498 499</a>; tin nhắn Zalo và email được phản hồi trong giờ làm việc, thường trong vòng 24 giờ làm việc. Với việc gấp, đặc biệt là <a href=\"{{root}}dich-vu/hinh-su/\">vụ án hình sự</a> hoặc sắp hết thời hạn kháng cáo, anh chị nên gọi trực tiếp hotline <a href=\"tel:0983498499\">0983 498 499</a>.",
            "Lưu ý: việc trao đổi ban đầu qua điện thoại, Zalo hoặc email chưa làm phát sinh quan hệ luật sư – khách hàng. Quan hệ này chỉ hình thành khi hai bên ký kết hợp đồng dịch vụ pháp lý.",
        ],
    },
]
