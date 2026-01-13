import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go
import time
from datetime import datetime
import hashlib

# ====================================================
# 1. CẤU HÌNH HỆ THỐNG & CSS
# ====================================================
st.set_page_config(
    page_title="Melody Mind | AI Music Streaming",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { border-radius: 20px; font-weight: bold; border: none; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(0, 204, 255, 0.5); }
    .song-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #00CCFF; transition: 0.3s; }
    .song-card:hover { background-color: #262730; transform: translateX(5px); }
    .big-card { background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%); padding: 30px; border-radius: 20px; border: 1px solid #333; margin-bottom: 20px; text-align: center; }
    
    /* Highlight input login */
    input[type="text"] { border: 1px solid #00CCFF !important; }
</style>
""", unsafe_allow_html=True)

# ====================================================
# 2. KHỞI TẠO SESSION STATE
# ====================================================
if 'current_song' not in st.session_state: st.session_state['current_song'] = None
if 'my_playlists' not in st.session_state: st.session_state['my_playlists'] = {}
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'listening_history' not in st.session_state: st.session_state['listening_history'] = []
if 'playing' not in st.session_state: st.session_state['playing'] = False
if 'play_progress' not in st.session_state: st.session_state['play_progress'] = 0
if 'music_queue' not in st.session_state: st.session_state['music_queue'] = []
if 'queue_index' not in st.session_state: st.session_state['queue_index'] = 0

if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'discovery' 
if 'now_playing_recs' not in st.session_state: st.session_state['now_playing_recs'] = None

# ====================================================
# 3. LOAD DỮ LIỆU & MODEL
# ====================================================
@st.cache_resource
def load_backend():
    try:
        # Load vector database
        df = pd.read_csv('music_vector_database.csv')
        vector_cols = [c for c in df.columns if c.startswith('emb_')]
        matrix_vectors = df[vector_cols].values
        
        # Load Music Info để lấy spotify_preview_url VÀ audio features
        music_info = pd.read_csv('Music Info.csv')
        
        # Merge để có đầy đủ thông tin (audio features + preview URL)
        merge_cols = ['track_id', 'spotify_preview_url', 'spotify_id', 
                     'danceability', 'energy', 'valence', 'acousticness', 'tempo',
                     'loudness', 'speechiness', 'instrumentalness', 'liveness', 
                     'duration_ms', 'genre', 'year', 'tags']
        
        # Chỉ merge các cột có trong Music Info
        available_cols = [c for c in merge_cols if c in music_info.columns]
        df = df.merge(music_info[available_cols], on='track_id', how='left')
        
        # Load NCF Model
        ncf_model = tf.keras.models.load_model('ncf_model_sampled.h5', compile=False)
        with open('user_encoder.pkl', 'rb') as f: user_enc = pickle.load(f)
        with open('track_encoder.pkl', 'rb') as f: track_enc = pickle.load(f)
            
        return df, matrix_vectors, vector_cols, ncf_model, user_enc, track_enc
    except Exception as e:
        st.error(f"Lỗi khởi động: {e}")
        return None, None, None, None, None, None

df, matrix_vec, vec_cols, ncf_model, user_enc, track_enc = load_backend()
if df is None: st.stop()

# ====================================================
# 4. HÀM LOGIC GỢI Ý
# ====================================================
def generate_user_id():
    return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()

def save_listening_history(user_id, track_id):
    """Lưu lịch sử nghe nhạc vào file CSV thực tế cho Collaborative Filtering"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Lưu vào session state
    st.session_state['listening_history'].append({
        'user_id': user_id, 'track_id': track_id, 'timestamp': timestamp
    })
    
    # Ghi vào file CSV để train lại model sau này
    try:
        import os
        file_path = 'user_listening_history_new.csv'
        
        # Tạo file mới nếu chưa có
        if not os.path.exists(file_path):
            pd.DataFrame([{'user_id': user_id, 'track_id': track_id, 'timestamp': timestamp}]).to_csv(
                file_path, index=False
            )
        else:
            # Append vào file có sẵn
            pd.DataFrame([{'user_id': user_id, 'track_id': track_id, 'timestamp': timestamp}]).to_csv(
                file_path, mode='a', header=False, index=False
            )
    except Exception as e:
        pass  # Không crash app nếu lỗi file I/O

def recommend_content_based(song_name, top_k=10):
    matches = df[df['name'].str.contains(song_name, case=False, na=False)]
    if matches.empty: return None
    target_idx = matches.index[0]
    target_vec = matrix_vec[target_idx].reshape(1, -1)
    sim_scores = cosine_similarity(target_vec, matrix_vec).flatten()
    top_indices = sim_scores.argsort()[::-1][1:top_k+1]
    results = df.iloc[top_indices].copy()
    results['score'] = sim_scores[top_indices]
    return results

def recommend_collaborative(user_id_raw, top_k=10):
    if ncf_model is None: return None
    try:
        user_idx = user_enc.transform([user_id_raw])[0]
        all_track_idxs = np.arange(len(track_enc.classes_))
        user_idxs = np.full(len(all_track_idxs), user_idx)
        predictions = ncf_model.predict([user_idxs, all_track_idxs], batch_size=4096, verbose=0).flatten()
        top_indices = predictions.argsort()[::-1][:top_k]
        top_track_ids = track_enc.inverse_transform(all_track_idxs[top_indices])
        results = df[df['track_id'].isin(top_track_ids)].copy()
        results['score'] = predictions[top_indices]
        return results
    except: return None

def recommend_item_to_item(song_id_raw, top_k=5):
    if ncf_model is None: return None
    try:
        track_emb_layer = ncf_model.get_layer('track_embedding')
        track_weights = track_emb_layer.get_weights()[0]
        target_idx = track_enc.transform([song_id_raw])[0]
        target_vec = track_weights[target_idx].reshape(1, -1)
        sim_scores = cosine_similarity(target_vec, track_weights).flatten()
        top_indices = sim_scores.argsort()[::-1][1:top_k+1]
        top_track_ids = track_enc.inverse_transform(top_indices)
        results = df[df['track_id'].isin(top_track_ids)].copy()
        results = results.set_index('track_id').loc[top_track_ids].reset_index()
        return results
    except: return None

def filter_by_context(mode, top_k=10):
    filtered = df.copy()
    if mode == "💪 Workout":
        if 'energy' in df.columns: filtered = filtered[filtered['energy'] > 0.7]
        if 'tempo' in df.columns: filtered = filtered[filtered['tempo'] > 0.6]
    elif mode == "📚 Study":
        if 'energy' in df.columns: filtered = filtered[filtered['energy'] < 0.5]
        if 'acousticness' in df.columns: filtered = filtered[filtered['acousticness'] > 0.5]
    elif mode == "🎉 Party":
        if 'danceability' in df.columns: filtered = filtered[filtered['danceability'] > 0.7]
        if 'valence' in df.columns: filtered = filtered[filtered['valence'] > 0.6]
    return filtered.sample(min(top_k, len(filtered)))

# ====================================================
# 5. HÀM PLAYER
# ====================================================
def play_song(song_row, context_queue=None):
    song_data = song_row.to_dict() if isinstance(song_row, pd.Series) else song_row
    st.session_state['current_song'] = song_data
    st.session_state['playing'] = True
    st.session_state['play_progress'] = 0
    st.session_state['view_mode'] = 'now_playing' 
    
    rec_cb = recommend_content_based(song_data['name'], top_k=6)
    rec_cf = recommend_item_to_item(song_data['track_id'], top_k=6)
    st.session_state['now_playing_recs'] = {'cb': rec_cb, 'cf': rec_cf}

    if context_queue is not None:
        queue_list = context_queue.to_dict('records') if isinstance(context_queue, pd.DataFrame) else context_queue
        st.session_state['music_queue'] = queue_list
        target_id = song_data['track_id']
        for idx, s in enumerate(queue_list):
            if s['track_id'] == target_id:
                st.session_state['queue_index'] = idx
                break

    if st.session_state['user_id']:
        save_listening_history(st.session_state['user_id'], song_data['track_id'])
    st.toast(f"▶️ Đang phát: {song_data['name']}", icon="🎵")

def play_next():
    queue = st.session_state['music_queue']
    idx = st.session_state['queue_index']
    if queue and idx < len(queue) - 1:
        st.session_state['queue_index'] = idx + 1
        play_song(queue[idx + 1], context_queue=None)
        st.rerun()

def play_prev():
    queue = st.session_state['music_queue']
    idx = st.session_state['queue_index']
    if queue and idx > 0:
        st.session_state['queue_index'] = idx - 1
        play_song(queue[idx - 1], context_queue=None)
        st.rerun()

def add_to_playlist(song_row, playlist_name="Favorites"):
    song_data = song_row.to_dict() if isinstance(song_row, pd.Series) else song_row
    if playlist_name not in st.session_state['my_playlists']: st.session_state['my_playlists'][playlist_name] = []
    
    existing = [s['track_id'] for s in st.session_state['my_playlists'][playlist_name]]
    if song_data['track_id'] not in existing:
        st.session_state['my_playlists'][playlist_name].append(song_data)
        st.toast(f"✅ Đã thêm vào '{playlist_name}'", icon="❤️")
    else:
        st.toast("⚠️ Đã có trong playlist!", icon="⚠️")

def create_playlist(name):
    if name and name not in st.session_state['my_playlists']:
        st.session_state['my_playlists'][name] = []
        st.toast(f"✅ Tạo playlist '{name}'", icon="🎉")

# ====================================================
# 6. SIDEBAR - PROFILE & PLAYER (DÙNG LINK GỐC)
# ====================================================
with st.sidebar:
    st.title("🎛️ MELODY MIND")
    st.markdown("---")
    
    # === 1. LOGIN SECTION ===
    st.subheader("👤 User Profile")
    if st.session_state['user_id'] is None:
        if st.button("🔑 Login as Guest", use_container_width=True):
            st.session_state['user_id'] = generate_user_id()
            st.rerun()
        st.markdown("<div style='text-align: center; margin: 5px 0; color: #666; font-size: 0.8em;'>--- HOẶC ---</div>", unsafe_allow_html=True)
        uid_input = st.text_input("Nhập User ID cũ:", placeholder="Dán ID vào đây...")
        if st.button("Đăng nhập", use_container_width=True, type="primary"):
            if uid_input.strip():
                st.session_state['user_id'] = uid_input.strip()
                st.rerun()
    else:
        st.success(f"User: {st.session_state['user_id'][:8]}...")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['user_id'] = None
            st.rerun()
    
    st.markdown("---")
    
    # === 2. PLAYER SECTION ===
    st.subheader("🎵 NOW PLAYING")
    current = st.session_state['current_song']
    
    if current:
        # Ảnh bìa
        st.image("https://i.gifer.com/origin/a3/a3623b6b610c5989709d73d9e4367c29_w200.gif", width=200)
        
        # Thông tin bài hát
        st.markdown(f"### {current['name']}")
        st.caption(f"🎤 {current['artist']}")
        
        # Lấy link Spotify Preview từ dataset
        audio_url = current.get('spotify_preview_url')
        
        if pd.notna(audio_url) and isinstance(audio_url, str) and audio_url.startswith('http'):
            # Link hợp lệ -> Phát nhạc
            st.audio(audio_url, format="audio/mp3", start_time=0)
        else:
            # Không có preview URL
            st.warning("⚠️ Bài này không có preview audio từ Spotify")
            st.caption("💡 Một số bài hát không được Spotify cung cấp đoạn nghe thử")

        # Biểu đồ DNA Âm thanh
        if all(col in current for col in ['energy', 'valence', 'danceability', 'acousticness']):
            vals = [current['energy'], current['valence'], current['danceability'], current['acousticness']]
            fig = go.Figure(go.Scatterpolar(r=vals, theta=['Energy','Valence','Dance','Acoustic'], fill='toself', line_color='#00CCFF'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False)), height=120, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color='white', size=8))
            st.plotly_chart(fig, use_container_width=True)

        # Các nút điều khiển
        c1, c2, c3 = st.columns([1, 1, 1])
        c1.button("⏮", key="sb_prev", on_click=play_prev)
        
        # Nút Play/Pause (Visual only)
        play_lbl = "⏸" if st.session_state['playing'] else "▶️"
        if c2.button(play_lbl, key="sb_pp"): 
            st.session_state['playing'] = not st.session_state['playing']
            st.rerun()
            
        c3.button("⏭", key="sb_next", on_click=play_next)
        
        # Thanh tiến trình giả lập
        if st.session_state['playing']: 
            st.session_state['play_progress'] = min(st.session_state['play_progress']+0.01, 1.0)
        st.progress(st.session_state['play_progress'])
        
        # Thêm vào Playlist
        st.markdown("---")
        pl_opts = ["❤️ Favorites"] + list(st.session_state['my_playlists'].keys())
        sel_pl = st.selectbox("Lưu vào:", list(dict.fromkeys(pl_opts)), key="sb_pl_sel")
        if st.button("➕ Thêm bài hát", use_container_width=True): 
            if sel_pl == "❤️ Favorites" and "Favorites" not in st.session_state['my_playlists']: create_playlist("Favorites")
            add_to_playlist(current, sel_pl)
            
    else:
        st.info("😴 Chưa phát nhạc")
        st.caption("Chọn một bài hát để bắt đầu")

# ====================================================
# 7. MAIN AREA
# ====================================================
tab1, tab2, tab3, tab4 = st.tabs(["🏠 TRANG CHỦ", "🔍 TÌM KIẾM", "🌍 NGỮ CẢNH", "💿 PLAYLIST"])

with tab1:
    mode = st.session_state.get('view_mode', 'discovery')
    
    # === CHẾ ĐỘ 1: KHÁM PHÁ ===
    if mode == 'discovery':
        st.header("🎧 Khám phá âm nhạc")
        if st.button("🎲 Random mới"): st.session_state['home_random_songs'] = df.sample(12); st.rerun()
            
        if 'home_random_songs' not in st.session_state: st.session_state['home_random_songs'] = df.sample(12)
        random_songs = st.session_state['home_random_songs']
        
        cols = st.columns(3)
        for idx, (i, row) in enumerate(random_songs.iterrows()):
            with cols[idx%3]:
                st.markdown('<div class="song-card">', unsafe_allow_html=True)
                st.write(f"**{row['name']}**")
                st.caption(row['artist'])
                
                # Fix: Dùng callback thay vì if statement
                st.button("▶️ Play", key=f"home_rand_{i}", 
                         on_click=play_song, args=(row, random_songs))
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        if st.session_state['user_id']:
            st.markdown("---")
            st.subheader("🎯 Dành riêng cho bạn")
            pers_recs = recommend_collaborative(st.session_state['user_id'])
            if pers_recs is not None:
                pcols = st.columns(3)
                for idx, (i, row) in enumerate(pers_recs.iterrows()):
                    with pcols[idx%3]:
                        st.markdown('<div class="song-card">', unsafe_allow_html=True)
                        st.write(f"**{row['name']}**")
                        st.caption(f"{row['artist']} ({int(row.get('score',0)*100)}%)")
                        
                        # Fix: Dùng callback
                        st.button("▶️ Play", key=f"home_pers_{i}",
                                 on_click=play_song, args=(row, pers_recs))
                        
                        st.markdown('</div>', unsafe_allow_html=True)

    # === CHẾ ĐỘ 2: NOW PLAYING ===
    elif mode == 'now_playing':
        if st.button("⬅️ Quay lại Khám phá"): st.session_state['view_mode'] = 'discovery'; st.rerun()
            
        curr = st.session_state['current_song']
        if curr:
            st.markdown(f"""<div class="big-card"><h1>🎵 Đang phát: {curr['name']}</h1><h3>🎤 Nghệ sĩ: {curr['artist']}</h3><p>ID: {curr['track_id']}</p></div>""", unsafe_allow_html=True)
            recs = st.session_state.get('now_playing_recs', {})
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🎼 Giai điệu tương tự")
                if recs.get('cb') is not None:
                    for i, row in recs['cb'].iterrows():
                        with st.container():
                            cl, cr = st.columns([4, 1])
                            cl.write(f"**{row['name']}** - {row['artist']}")
                            
                            # Fix: Callback
                            cr.button("▶️", key=f"np_cb_{i}",
                                     on_click=play_song, args=(row, recs['cb']))
                            
                            st.divider()
            with c2:
                st.subheader("👥 Fan cũng nghe")
                if recs.get('cf') is not None:
                    for i, row in recs['cf'].iterrows():
                        with st.container():
                            cl, cr = st.columns([4, 1])
                            cl.write(f"**{row['name']}** - {row['artist']}")
                            
                            # Fix: Callback
                            cr.button("▶️", key=f"np_cf_{i}",
                                     on_click=play_song, args=(row, recs['cf']))
                            
                            st.divider()

with tab2:
    st.header("🔍 Tìm kiếm")
    q = st.text_input("Nhập tên bài...")
    if st.button("Tìm") and q:
        matches = df[df['name'].str.contains(q, case=False, na=False)|df['artist'].str.contains(q, case=False, na=False)]
        if not matches.empty:
            row = matches.iloc[0]
            st.success(f"Tìm thấy: {row['name']}")
            
            # Fix: Callback
            st.button("▶️ Phát ngay", key="search_play",
                     on_click=play_song, args=(row, matches.head(10)))
        else: 
            st.warning("Không thấy!")

with tab3:
    st.header("🌍 Moods")
    c1, c2, c3 = st.columns(3)
    m = None
    if c1.button("Workout", use_container_width=True): m="💪 Workout"
    if c2.button("Study", use_container_width=True): m="📚 Study"
    if c3.button("Party", use_container_width=True): m="🎉 Party"
    if m:
        # Lưu kết quả vào session để không bị mất khi rerun
        if 'context_results' not in st.session_state or st.session_state.get('last_context_mode') != m:
            st.session_state['context_results'] = filter_by_context(m)
            st.session_state['last_context_mode'] = m
        
        res = st.session_state['context_results']
        
        st.subheader(f"Playlist: {m}")
        cols = st.columns(4)
        for idx, (i, row) in enumerate(res.iterrows()):
            with cols[idx%4]:
                st.markdown('<div class="song-card">', unsafe_allow_html=True)
                st.write(f"**{row['name']}**")
                st.caption(f"{row['artist']}")
                
                # Fix: Callback để không mất playlist
                st.button("▶️", key=f"ctx_{i}",
                         on_click=play_song, args=(row, res))
                
                st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.header("💿 My Playlists")
    new_pl = st.text_input("New Playlist:")
    if st.button("Create"): create_playlist(new_pl); st.rerun()
    for pl, songs in st.session_state['my_playlists'].items():
        with st.expander(f"📂 {pl} ({len(songs)})"):
            if songs:
                # Fix: Callback cho Play All
                st.button(f"▶️ Play All", key=f"pall_{pl}",
                         on_click=play_song, args=(pd.Series(songs[0]), pd.DataFrame(songs)))
                
                st.markdown("---")
                
                # Hiển thị từng bài
                for idx, s in enumerate(songs):
                    col_info, col_btn = st.columns([4, 1])
                    col_info.write(f"{idx+1}. **{s['name']}** - {s['artist']}")
                    
                    # Nút play từng bài
                    col_btn.button("▶️", key=f"pl_{pl}_{idx}",
                                  on_click=play_song, args=(pd.Series(s), pd.DataFrame(songs)))
            else:
                st.caption("Playlist trống")