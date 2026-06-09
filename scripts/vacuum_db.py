"""压缩数据库文件"""
import sqlite3
import os
from pathlib import Path

db_path = str(Path(__file__).parent.parent / "data" / "gaokao.db")
print(f"Before: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=DELETE")
conn.execute("VACUUM")
conn.close()

# 删除WAL文件
wal_path = db_path + "-wal"
shm_path = db_path + "-shm"
if os.path.exists(wal_path):
    os.remove(wal_path)
    print(f"Removed WAL file")
if os.path.exists(shm_path):
    os.remove(shm_path)
    print(f"Removed SHM file")

print(f"After: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")
