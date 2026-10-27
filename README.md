# Việt Dịch — Anh → Việt cho PDF và Word

App chạy trên máy với giao diện tiếng Việt. Tải tài liệu lên, nhập OpenAI API key, chọn model và tải bản dịch. Hỗ trợ PDF có lớp chữ, DOCX và TXT UTF-8.

## Chạy nhanh

Cần Python 3.10 trở lên; hỗ trợ **Python 3.14 bản tiêu chuẩn 64-bit**.

**Windows / Python 3.14:** giải nén bản app mới vào thư mục riêng rồi nhấp đúp `run.bat`. File này ưu tiên `py -3.14`, cài các thư viện có sẵn gói nhị phân và tự mở trình duyệt khi app sẵn sàng. Nếu không có Python Launcher, app thử lệnh `python` trên PATH. Không cần cài Visual Studio Build Tools hoặc Rust.

App tạo môi trường riêng theo phiên bản Python, ví dụ `.venv-3.14`, nên không dùng nhầm `.venv` của Python cũ. Lần đầu cần Internet để cài thư viện; các lần sau vẫn kiểm tra phụ thuộc. Giữ cửa sổ chạy app mở khi sử dụng. Nếu có lỗi, cửa sổ sẽ giữ lại thông báo để bạn xem.

Nếu muốn chạy thủ công bằng Python 3.14 trên Windows:

```bat
py -3.14 launcher.py
```

Hoặc cài và chạy trực tiếp (không dùng trình khởi động):

```sh
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Hoặc nhấp đúp `run.bat` trên Windows / chạy `sh run.sh` trên macOS, Linux để cài phụ thuộc và khởi động.

Khi tự cài trực tiếp trên Python 3.14, hãy nâng cấp pip trước bằng `python -m pip install --upgrade pip`. Nếu dùng bản Python thử nghiệm, bản free-threaded (`3.14t`) hoặc Windows 32-bit, khả năng có gói nhị phân phụ thuộc từng thư viện; khuyến nghị bản Python 3.14 tiêu chuẩn 64-bit.

Mở http://127.0.0.1:5000. Nhập API key trong mục **Tùy chọn dịch & API key**, hoặc cấu hình biến môi trường `OPENAI_API_KEY` trước khi chạy. Không đưa key lên GitHub. OpenAI API tính phí riêng theo tài khoản của bạn. Key nhập ở giao diện được giữ trong ô của tab hiện tại để dùng lại; tải lại trang để xóa; app không ghi key hay tài liệu vào file. Nội dung chữ cần dịch được gửi tới OpenAI. API có timeout và có thể tự thử lại khi lỗi mạng.

Chạy trên địa chỉ loopback mặc định; không đưa Flask development server này trực tiếp lên Internet. Một yêu cầu xử lý đồng bộ, tài liệu dài có thể mất nhiều phút. Tối đa 20 MB/file và 100 trang PDF. Hãy giữ trang mở trong lúc dịch.

## Bảo toàn định dạng và công thức

**Không cam kết bố cục hoặc chất lượng dịch đúng 100%.** Độ dài tiếng Việt khác tiếng Anh; Word có thể đổi ngắt dòng/trang. Cần đối chiếu kết quả với tài liệu gốc.

- **DOCX:** sửa trực tiếp nội dung các thẻ chữ `w:t`; không dựng lại tài liệu. Giữ nguyên byte của XML ngoài phần chữ được dịch và nội dung các thành phần khác trong gói ZIP. Style, bảng, hình ảnh và đối tượng toán Word/OMML được giữ lại. Có dịch chữ ở header, footer, footnote, endnote và comment. Bỏ qua đoạn chứa trường tự động như mục lục, tham chiếu và số trang (kể cả trường kéo dài qua nhiều đoạn). Không dịch chữ trong ảnh, SmartArt, biểu đồ, công thức hoặc đối tượng nhúng. Một số XML đặc biệt bị từ chối thay vì cố chuyển đổi. Word cũ `.doc` chưa hỗ trợ.
- **PDF (thử nghiệm):** nhận diện vùng chữ theo tọa độ; bỏ qua cả vùng có font toán hoặc dấu hiệu toán học (ví dụ `=`, `∫`, ký tự Hy Lạp). Xóa chữ gốc trong vùng được dịch và đặt bản dịch vào cùng khung; không xóa ảnh hoặc vector. Giữ số trang, dùng font DejaVu Sans/Arial có tiếng Việt, giảm cỡ chữ tới tối thiểu 5 pt để vừa khung. Có thể thay đổi font, kiểu nhấn mạnh và ngắt dòng. Dừng xuất nếu bản dịch không vừa. Nhận diện công thức là heuristic, **không bảo đảm mọi công thức được phát hiện**; vùng công thức không có dấu hiệu rõ có thể bị dịch. Phần văn bản nằm chung vùng công thức cũng sẽ được giữ tiếng Anh. Không hỗ trợ chữ xoay, trang xoay, scan/OCR, PDF mã hóa hoặc có chữ ký số. PDF nhiều cột, nền phức tạp, font đặc biệt cần kiểm tra thủ công; nếu có Word nguồn, nên dùng Word.
- **TXT:** giữ BOM UTF-8, xuống dòng, công thức trong `$…$`, `$$…$$`, `\(…\)`, `\[…\]` và đoạn code có backtick. TXT hỗ trợ công thức nhiều dòng. Với Word, công thức cần nằm cùng run; đoạn có LaTeX bị chia qua nhiều run được giữ nguyên để tránh sửa công thức. Công thức dạng chữ thường không có dấu phân cách không được bảo vệ tự động. Nên dùng công thức Word gốc để có thể dịch phần chữ xung quanh công thức.

PDF cần font tiếng Việt trên máy. App tìm DejaVu Sans trên Linux và Arial trên Windows/macOS. Nếu không có, đặt `VIET_FONT_PATH` trỏ tới file `.ttf` phù hợp. Đây là font cục bộ; app không tải font từ bên ngoài.

## Kiểm thử

```sh
python -m pip install pytest
python -m pytest -q
```

Kiểm thử bằng dịch vụ giả lập: bảo toàn XML, công thức OMML/LaTeX, style và ảnh; field Word; BOM/xuống dòng; PDF có công thức; lỗi thiếu lớp chữ và tràn khung; validation và tải kết quả qua HTTP. Không cần API key khi chạy test. Các test này kiểm tra cơ chế xử lý file, không xác nhận chất lượng bản dịch của model hoặc bố cục trên mọi trình đọc PDF/Word.

## Khi đã nhập key nhưng dịch không được

App báo riêng lỗi xác thực (401), hết tín dụng/hạn mức API (429 insufficient_quota), giới hạn tốc độ (429 rate_limit), quyền truy cập (403), model không khả dụng (404), kết nối và quá thời gian chờ. Key không bị tự xóa sau mỗi lần thử; vẫn được che trong ô và không lưu vào localStorage, sessionStorage hoặc file. Tải lại trang để xóa key đã nhập. Không gửi API key cho người hỗ trợ.

Với `insufficient_quota`, kiểm tra Billing và hạn mức dự án trên OpenAI Platform. Tạo key mới không tự bổ sung tín dụng; ChatGPT Plus/Pro có thanh toán riêng với API. Với `document_processing_error`, thử TXT ngắn để phân biệt lỗi xử lý PDF/Word. Các lỗi OpenAI trả về không được hiển thị nguyên văn, tránh lộ key hoặc nội dung tài liệu. Chưa có file kết quả nếu yêu cầu thất bại.
