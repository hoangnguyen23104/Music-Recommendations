# 🚀 QUICK START GUIDE

## Chạy ngay trong 3 bước

### Bước 1: Kiểm tra hệ thống
```bash
cd d:\ALLNEW
python health_check.py
```

✅ Nếu thấy "Production Ready" → Sang bước 2

---

### Bước 2: Chạy ứng dụng
```bash
streamlit run app.py
```

✅ Browser tự động mở tại: http://localhost:8501

---

### Bước 3: Sử dụng

#### 🔑 Login
1. Bấm "**🔑 Login as Guest**" (tự tạo ID)
2. **HOẶC** nhập User ID cũ nếu đã có

#### 🎵 Nghe nhạc
1. Trang chủ hiển thị 12 bài random
2. Bấm "**▶️ Play**" để phát nhạc
3. Nhạc phát trong sidebar (bên trái)

#### 📚 Tạo Playlist
1. Vào tab "**💿 PLAYLIST**"
2. Nhập tên playlist → Bấm "**Create**"
3. Khi nghe nhạc → Chọn playlist → "**➕ Thêm bài hát**"

#### 🌍 Ngữ cảnh
1. Vào tab "**🌍 NGỮ CẢNH**"
2. Chọn:
   - **💪 Workout** → Nhạc mạnh mẽ
   - **📚 Study** → Nhạc nhẹ nhàng
   - **🎉 Party** → Nhạc vui tươi
3. Bấm Play bất kỳ bài nào

---

## ⚡ Tips

### 🎯 Personalized Recommendations
- Login → Nghe ít nhất 5 bài
- Quay lại trang chủ → Xem "**🎯 Dành riêng cho bạn**"
- Hệ thống học sở thích và gợi ý

### 🔍 Tìm kiếm thông minh
- Nhập tên bài/nghệ sĩ vào tab "**🔍 TÌM KIẾM**"
- Hệ thống hiển thị:
  - **🎼 Giai điệu tương tự** (Audio features)
  - **👥 Fan cũng nghe** (Collaborative filtering)

### 💾 Lưu User ID
- Copy ID hiển thị ở sidebar: `User: a3f8e2c1...`
- Paste vào Notepad để dùng lại lần sau
- Login lại bằng ID này để giữ lịch sử

---

## ❓ FAQ

**Q: Tại sao một số bài không phát được?**  
A: Spotify không cung cấp preview cho tất cả bài hát. Thử bài khác.

**Q: Dữ liệu lưu ở đâu?**  
A: File `user_listening_history_new.csv` trong cùng thư mục.

**Q: Có cần internet không?**  
A: Có, để phát nhạc từ Spotify CDN.

**Q: Làm sao biết hệ thống đang track?**  
A: Mỗi lần bấm Play → Toast notification "▶️ Đang phát: [Tên bài]"

---

## 🆘 Gặp lỗi?

### Lỗi: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Lỗi: "File not found"
```bash
python health_check.py  # Kiểm tra files
```

### Lỗi: "Model loading failed"
- Kiểm tra file `.h5` và `.pkl` có tồn tại
- Download lại từ backup nếu bị corrupt

---

## 📖 Đọc thêm

- `README.md` - Full documentation
- `README_USER_TRACKING.md` - User tracking system
- `REPORT_BUG_FIXES.md` - Bug fixes report

---

**Happy listening! 🎧**
