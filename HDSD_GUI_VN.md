# Hướng Dẫn Sử Dụng Giao Diện OmniVoice (GUI)

Chào mừng bạn đến với công cụ **OmniVoice Local GUI** — ứng dụng giao diện trực quan, hoạt động hoàn toàn offline trên máy tính cá nhân để tạo và sao chép giọng nói (Voice Cloning) chuyên nghiệp.

Tài liệu này sẽ hướng dẫn bạn cách sử dụng các tính năng của ứng dụng.

---

## 1. Khởi động ứng dụng
Chỉ cần nhấp đúp vào file **`run_gui.bat`** tại thư mục cài đặt gốc. Ứng dụng sẽ tự động tải các thư viện cần thiết và hiển thị giao diện chính.

*Giao diện bao gồm 3 tab chính: Voice Clone, Voice Design, và Audio Library.*

---

## 2. Các chức năng chính

### 🎵 Tab 1: Voice Clone (Sao chép giọng nói)
Dùng để nhân bản một giọng nói có sẵn dựa trên một file âm thanh mẫu (Reference Audio) rất ngắn (khuyên dùng từ 3-10 giây).

1. **Nhập / Ghi âm file mẫu**: 
   - Bạn có thể **chọn file âm thanh** có sẵn từ máy tính.
   - Hoặc bấm nút **Ghi âm (Record)** để trực tiếp thu âm giọng của chính bạn thông qua Micro.
2. **Text của File Mẫu (Reference Text)**: Nhập vào nội dung văn bản mà người nói trong file âm thanh đang nói. (Nếu để trống, AI sẽ tự động phân tích và nhận dạng, nhưng nhập thủ công sẽ cho kết quả chuẩn nhất).
3. **Text cần đọc (Synthesize Text)**: Nhập đoạn văn bản mới mà bạn muốn AI đọc lên bằng giọng điệu của người mẫu.
4. **Mẫu giọng (Presets)**: 
   - Sau khi chọn xong file âm thanh và nhập Text của file mẫu, bạn có thể bấm **Lưu mẫu** để lưu lại thành một preset.
   - Lần sau, bạn chỉ cần chọn tên từ danh sách thả xuống, hệ thống sẽ tự động điền lại thông tin, tiết kiệm rất nhiều thời gian.

### 🎭 Tab 2: Voice Design (Tạo giọng theo thuộc tính)
Nếu bạn không có file giọng mẫu, bạn có thể dùng tính năng này để yêu cầu AI tự tạo ra một giọng đọc theo ý muốn.
- **Văn bản cần đọc**: Nhập nội dung bạn muốn AI đọc.
- **Thiết lập thuộc tính**: Chọn Giới tính (Nam/Nữ), Độ tuổi, Cao độ (Pitch), Trọng âm (Anh, Mỹ, tiếng địa phương...) hoặc phong cách nói (VD: nói thầm - whisper).
- *Lưu ý: Tính năng thiết kế giọng được tối ưu hóa nhất trên tiếng Anh và tiếng Trung.*

### 📚 Tab 3: Audio Library (Thư viện Audio & Quản lý)
Nơi tự động lưu trữ và quản lý tất cả các file âm thanh bạn đã tạo ra.
- **Danh sách bên trái**: Hiển thị tất cả file đã tạo kèm thời gian và 1 dòng văn bản xem trước.
- **Tính năng Multi-select (Chọn nhiều)**: 
  - Bấm **Ctrl + Click chuột** để bôi đen/chọn nhiều file cùng lúc.
  - Sử dụng thanh công cụ phía trên để **Chọn tất cả**, **Bỏ chọn** hoặc **Xóa đã chọn** (xóa hàng loạt).
- **Chi tiết bên phải**: Khi click vào 1 file, bạn có thể xem lại toàn bộ nội dung văn bản (dù dài đến đâu) và các thông số cài đặt cũ.
- **Các nút hành động**:
  - **▶ Load & Phát Audio**: Nạp file cũ vào trình phát nhạc bên dưới màn hình.
  - **✏ Sửa / Re-clone**: Tự động lấy lại văn bản và file âm thanh mẫu của lịch sử đó, ném qua tab Voice Clone để bạn chỉnh sửa thông số và tạo lại file mới.
  - **🗑 Xóa**: Xóa file khỏi lịch sử và xóa luôn file `.wav` khỏi ổ cứng máy tính.

---

## 3. Trình phát nhạc nâng cao (Media Player)
Nằm ở dưới cùng của ứng dụng. Mỗi khi bạn tạo giọng thành công hoặc load từ Thư viện, âm thanh sẽ xuất hiện ở đây.
- Có thể **Tua nhanh (Seek / Scrubbing)** thông qua thanh trượt.
- Hỗ trợ lưu nhanh file âm thanh đang phát ra một thư mục bất kỳ trên máy (Nút Save Audio).

---

## 4. Giải thích các thông số "Generation Settings"
Bạn sẽ thấy cột cài đặt này bên phải của màn hình Clone và Design. Tinh chỉnh chúng để có kết quả tốt nhất:

* **Inference Steps (Mặc định 32)**: Số vòng lặp mà AI sẽ xử lý. Số càng cao (VD: 40-50) thì âm thanh càng chi tiết, tự nhiên nhưng thời gian tạo càng lâu. Dùng 16 nếu bạn muốn test nhanh kết quả.
* **Guidance Scale (CFG - Mặc định 2.0)**: Chỉ số quyết định AI sẽ bám sát vào giọng mẫu (hoặc yêu cầu của bạn) đến mức nào. Quá cao có thể làm méo tiếng, quá thấp sẽ khiến giọng bị mờ nhạt. 
* **Speed Factor (Tốc độ đọc - Mặc định 1.0)**:
  - Lớn hơn 1.0 (VD: 1.2): Nói nhanh hơn.
  - Nhỏ hơn 1.0 (VD: 0.8): Nói chậm lại.
* **Fixed Duration (Thời lượng cố định - tính bằng giây)**: Nếu bạn nhập số vào đây (VD: 10), AI sẽ ép đoạn hội thoại phải dài đúng 10 giây (rất hợp để làm dubbing khớp video). *Thông số này sẽ ghi đè lên Speed Factor.*

**Các tuỳ chọn xử lý (Checkboxes):**
* **Denoise Audio (Lọc nhiễu)**: Bật để yêu cầu AI tạo ra giọng nói sạch sẽ, lọc bớt tạp âm/tiếng ồn.
* **Preprocess Prompt**: Ứng dụng tự động cắt bỏ khoảng im lặng thừa ở file âm thanh mẫu của bạn và thêm dấu câu cần thiết.
* **Postprocess Output**: Tự động cắt bỏ những khoảng lặng/thở quá dài ở file kết quả sau khi tạo xong.

---
*Chúc bạn có những trải nghiệm tuyệt vời với OmniVoice GUI!*
