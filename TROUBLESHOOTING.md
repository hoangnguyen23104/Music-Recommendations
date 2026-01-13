# 🔧 TROUBLESHOOTING GUIDE

## 🚨 XỬ LÝ LỖI THƯỜNG GẶP

---

## 1. ❌ App không khởi động được

### Triệu chứng:
```
ModuleNotFoundError: No module named 'streamlit'
```

### Giải pháp:
```bash
pip install -r requirements.txt
```

Hoặc cài từng package:
```bash
pip install streamlit pandas numpy tensorflow scikit-learn plotly
```

---

## 2. ❌ Không load được model

### Triệu chứng:
```
FileNotFoundError: ncf_model_sampled.h5 not found
```

### Giải pháp:
Kiểm tra files:
```bash
python health_check.py
```

Cần có đủ 6 files:
- ✅ ncf_model_sampled.h5
- ✅ user_encoder.pkl
- ✅ track_encoder.pkl
- ✅ Music Info.csv
- ✅ music_vector_database.csv
- ✅ app.py

---

## 3. ❌ Không phát được nhạc

### Triệu chứng:
- Click Play nhưng không nghe thấy gì
- Hoặc báo "Preview không khả dụng"

### Nguyên nhân:
1. Một số bài Spotify block preview
2. Internet bị chậm/disconnect
3. Browser block audio autoplay

### Giải pháp:
```
1. Thử bài khác
2. Check internet connection
3. Click vào audio player để unmute (nếu browser block)
4. F12 → Console → Xem error log
```

---

## 4. ❌ Nút Play không hoạt động

### Triệu chứng:
- Click button không có phản ứng
- Hoặc app reload nhưng không phát nhạc

### Giải pháp:
**ĐÃ SỬA** trong version 2.0. Nếu vẫn lỗi:
```bash
# Clear Streamlit cache
streamlit cache clear

# Restart app
streamlit run app.py
```

---

## 5. ❌ Personalized recommendations trống

### Triệu chứng:
- Đã login nhưng "Dành riêng cho bạn" không hiện

### Nguyên nhân:
User ID mới chưa có trong training data

### Giải pháp:
```
1. Đây là BÌNH THƯỜNG với Guest users mới
2. Hệ thống sẽ hiện Content-Based recommendations thay thế
3. Muốn test Collaborative → Dùng User ID có trong training data:
   
   Mở user_encoder.pkl → Lấy 1 user_id mẫu
   Login bằng ID đó
```

Test script:
```python
import pickle
with open('user_encoder.pkl', 'rb') as f:
    enc = pickle.load(f)
print("Sample user ID:", enc.classes_[0])
```

---

## 6. ❌ Playlist biến mất

### Triệu chứng:
- Tạo playlist xong refresh → Mất hết

### Nguyên nhân:
Session state mất khi reload

### Giải pháp:
**ĐÚNG BEHAVIOR** - Session-based storage.

Nếu muốn persistent:
```python
# Thêm vào app.py (tùy chỉnh)
import json

# Lưu playlist khi tạo
def save_playlists():
    with open('playlists.json', 'w') as f:
        json.dump(st.session_state['my_playlists'], f)

# Load khi khởi động
def load_playlists():
    try:
        with open('playlists.json', 'r') as f:
            st.session_state['my_playlists'] = json.load(f)
    except:
        st.session_state['my_playlists'] = {}
```

---

## 7. ❌ Context-Aware không ra kết quả

### Triệu chứng:
- Click Workout/Study/Party → Không có bài nào

### Nguyên nhân:
- Audio features bị thiếu
- Threshold quá strict

### Giải pháp:
Kiểm tra merge:
```python
import pandas as pd
df = pd.read_csv('music_vector_database.csv')
info = pd.read_csv('Music Info.csv')
merged = df.merge(info, on='track_id', how='left')
print(merged[['energy', 'tempo', 'danceability']].describe())
```

Nếu thiếu features → Re-merge trong app.py

---

## 8. ❌ "Out of Memory" error

### Triệu chứng:
```
MemoryError: Unable to allocate array
```

### Nguyên nhân:
Dataset quá lớn cho RAM

### Giải pháp:
```python
# Giảm top_k trong recommendations
def recommend_content_based(song_name, top_k=5):  # Thay vì 10

# Hoặc sample dataset
df = df.sample(10000)  # Chỉ dùng 10K bài
```

---

## 9. ❌ Không tạo được tracking file

### Triệu chứng:
```
PermissionError: user_listening_history_new.csv
```

### Nguyên nhân:
Không có quyền ghi file

### Giải pháp:
```bash
# Windows: Chạy terminal as Admin
Right-click PowerShell → Run as Administrator

# Hoặc thay đổi permissions
icacls "d:\ALLNEW" /grant Users:F
```

---

## 10. ❌ App chạy chậm

### Triệu chứng:
- Mỗi lần click đợi lâu
- Loading spinner liên tục

### Nguyên nhân:
- Model load lại mỗi lần
- Cache không hoạt động

### Giải pháp:
```python
# Đảm bảo có @st.cache_resource
@st.cache_resource
def load_backend():
    ...

# Clear cache và restart
streamlit cache clear
streamlit run app.py
```

---

## 🔍 DEBUG MODE

### Bật debug để xem logs chi tiết:

```python
# Thêm vào đầu app.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Hoặc trong terminal
streamlit run app.py --logger.level=debug
```

---

## 🧪 TEST SCRIPTS

### Test 1: Kiểm tra models
```python
import tensorflow as tf
import pickle

model = tf.keras.models.load_model('ncf_model_sampled.h5')
print("✅ Model loaded:", len(model.layers), "layers")

with open('user_encoder.pkl', 'rb') as f:
    user_enc = pickle.load(f)
print("✅ User encoder:", len(user_enc.classes_), "users")
```

### Test 2: Kiểm tra merge
```python
import pandas as pd

df_vec = pd.read_csv('music_vector_database.csv')
df_info = pd.read_csv('Music Info.csv')

merged = df_vec.merge(df_info[['track_id', 'spotify_preview_url']], 
                      on='track_id', how='left')

print("✅ Total songs:", len(merged))
print("✅ With preview:", merged['spotify_preview_url'].notna().sum())
print("✅ Missing preview:", merged['spotify_preview_url'].isna().sum())
```

### Test 3: Kiểm tra recommendations
```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load data
df = pd.read_csv('music_vector_database.csv')
vec_cols = [c for c in df.columns if c.startswith('emb_')]
matrix = df[vec_cols].values

# Test similarity
target = matrix[0].reshape(1, -1)
scores = cosine_similarity(target, matrix).flatten()
top_5 = scores.argsort()[::-1][1:6]

print("✅ Top 5 similar songs:")
for idx in top_5:
    print(f"  - {df.iloc[idx]['name']} (score: {scores[idx]:.3f})")
```

---

## 📞 EMERGENCY CONTACTS

### Nếu demo bị crash giữa chừng:

**Plan B:**
1. Có slides backup với screenshots
2. Có video recording sẵn (quay trước)
3. Giải thích bằng diagram thay vì live demo

**Quick fixes:**
```bash
# Restart ngay
Ctrl+C → streamlit run app.py

# Hoặc kill process
taskkill /F /IM streamlit.exe
streamlit run app.py
```

---

## 🆘 LAST RESORT

### Nếu không fix được:

1. **Rollback về version backup:**
```bash
# Copy backup
copy app_backup.py app.py
streamlit run app.py
```

2. **Reinstall từ đầu:**
```bash
pip uninstall streamlit tensorflow -y
pip install -r requirements.txt
streamlit run app.py
```

3. **Use colab/cloud:**
- Upload lên Google Colab
- Chạy trên Streamlit Cloud
- Demo bằng ngrok tunnel

---

## ✅ PREVENTION CHECKLIST

Trước khi demo, check:

- [ ] Đã test app ít nhất 1 lần
- [ ] Internet ổn định
- [ ] Battery laptop đầy
- [ ] Tắt notifications
- [ ] Đóng apps không cần thiết
- [ ] Clear browser cache
- [ ] Có backup slides/video
- [ ] Có cheat sheet sẵn
- [ ] Đã rehearsal 2-3 lần

---

**🔧 Remember: Stay calm, có backup plan! 💪**
