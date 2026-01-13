import pandas as pd

# Kiểm tra Music Info
df_info = pd.read_csv('Music Info.csv')
print(f"✅ Music Info: {len(df_info):,} rows")
print(f"✅ Columns: {list(df_info.columns[:5])}")
print(f"✅ Preview URLs available: {df_info['spotify_preview_url'].notna().sum():,} songs")
print(f"✅ Missing preview URLs: {df_info['spotify_preview_url'].isna().sum():,} songs")

# Kiểm tra vector database
df_vec = pd.read_csv('music_vector_database.csv')
print(f"\n✅ Vector Database: {len(df_vec):,} rows")

# Test merge
merged = df_vec.merge(df_info[['track_id', 'spotify_preview_url']], on='track_id', how='left')
print(f"\n✅ Merged data: {len(merged):,} rows")
print(f"✅ Merged with preview URLs: {merged['spotify_preview_url'].notna().sum():,} songs")
