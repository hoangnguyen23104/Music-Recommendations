# 📊 Hệ thống User Tracking & Data Collection

## 🆔 Cơ chế User ID

### 1. **Login as Guest** (Chế độ Khách)
Khi bấm nút "🔑 Login as Guest":
- Hệ thống tự động tạo một **User ID ngẫu nhiên** duy nhất
- ID được tạo bằng MD5 hash của timestamp hiện tại
- Format: `a3f8e2c1d9b7...` (32 ký tự hex)
- ID này **CHỈ tồn tại trong phiên làm việc hiện tại** (session)
- Nếu **đóng browser** hoặc **refresh page** → Mất ID cũ, phải login lại

### 2. **Login bằng User ID cũ**
Nếu muốn giữ lại lịch sử:
- Copy User ID từ lần trước (hiển thị ở sidebar: `User: a3f8e2c1...`)
- Paste vào ô "Nhập User ID cũ:" → Bấm "Đăng nhập"
- Hệ thống sẽ dùng ID đó để tiếp tục tracking

---

## 💾 Cách Hệ thống Lưu Dữ liệu

### **File: `user_listening_history_new.csv`**

Mỗi khi người dùng **phát một bài hát**, hệ thống tự động ghi vào file này:

```csv
user_id,track_id,timestamp
a3f8e2c1d9b7f4e6...,TRIOREW128F424EAF0,2025-12-04 14:35:22
a3f8e2c1d9b7f4e6...,TRRIVDJ128F429B0E8,2025-12-04 14:37:45
b9c4f1e2a7d3...,TROUVHL128F426C441,2025-12-04 15:12:10
...
```

### **Cột dữ liệu:**
- `user_id`: ID người dùng (Guest hoặc custom)
- `track_id`: Mã bài hát trong hệ thống
- `timestamp`: Thời gian nghe (YYYY-MM-DD HH:MM:SS)

### **Lưu ở đâu?**
- Cùng thư mục với `app.py`
- Đường dẫn: `d:\ALLNEW\user_listening_history_new.csv`

---

## 🔄 Quy trình Train lại Model

### Bước 1: Thu thập dữ liệu
Sau khi có nhiều user sử dụng → file `user_listening_history_new.csv` chứa đủ dữ liệu

### Bước 2: Merge với dataset cũ
```python
import pandas as pd

# Đọc dữ liệu cũ
old_data = pd.read_csv('User Listening History.csv')

# Đọc dữ liệu mới
new_data = pd.read_csv('user_listening_history_new.csv')

# Gộp lại
combined = pd.concat([old_data, new_data], ignore_index=True)

# Loại bỏ trùng lặp
combined = combined.drop_duplicates(subset=['user_id', 'track_id', 'timestamp'])

# Lưu lại
combined.to_csv('User Listening History.csv', index=False)
```

### Bước 3: Train lại NCF Model
Mở notebook `Collabrative_flitering.ipynb` và chạy lại từ đầu với dataset mới.

---

## 📈 Tracking Metrics

### **Session State (Tạm thời)**
Trong mỗi phiên làm việc, hệ thống lưu:
```python
st.session_state['listening_history'] = [
    {'user_id': '...', 'track_id': '...', 'timestamp': '...'},
    {'user_id': '...', 'track_id': '...', 'timestamp': '...'},
    ...
]
```

### **File CSV (Vĩnh viễn)**
Mỗi lần phát nhạc → Append vào file `user_listening_history_new.csv`

---

## 🎯 Tại sao cần tracking?

### 1. **Collaborative Filtering**
- Model NCF cần biết **ai nghe gì** để gợi ý cho người khác
- Ví dụ: User A nghe Rock → User B cũng nghe Rock → Gợi ý cho User C

### 2. **Personalized Recommendations**
- Phần "🎯 Dành riêng cho bạn" dựa trên lịch sử nghe của chính user đó

### 3. **Cải thiện Model**
- Càng nhiều dữ liệu → Model càng chính xác
- Định kỳ train lại với dữ liệu mới

---

## ⚠️ Lưu ý

### ✅ Điều CÓ:
- ✅ Lưu lịch sử nghe nhạc vào file CSV
- ✅ Guest Mode tạo ID tự động
- ✅ Có thể login lại bằng ID cũ
- ✅ File CSV tăng dần theo thời gian

### ❌ Điều KHÔNG CÓ:
- ❌ **Không có database** (PostgreSQL/MongoDB)
- ❌ **Không có authentication** (password)
- ❌ **Không có user profile** (tên, email, avatar)
- ❌ **Không tự động sync** giữa các device

---

## 🚀 Nâng cấp trong tương lai

1. **Database thực tế**: SQLite/PostgreSQL
2. **User authentication**: Login bằng email/password
3. **Cloud storage**: Lưu file CSV lên Google Drive/S3
4. **Auto retrain**: Script tự động train lại model khi có đủ dữ liệu mới
5. **Analytics dashboard**: Biểu đồ thống kê user behavior

---

## 📞 Support

Nếu file `user_listening_history_new.csv` không được tạo:
1. Kiểm tra quyền ghi file trong thư mục `d:\ALLNEW\`
2. Xem console log nếu có lỗi
3. Chạy thử: `pd.DataFrame([{'user_id': 'test', 'track_id': 'test', 'timestamp': '2025-01-01'}]).to_csv('test.csv', index=False)`

---

**Cập nhật:** 2025-12-04  
**Version:** 2.0  
**Author:** AI Music Recommendation System
