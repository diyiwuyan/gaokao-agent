import sqlite3
conn = sqlite3.connect('data/gaokao.db')
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for r in cur.fetchall():
    if r[0]:
        print(r[0])
        print()
conn.close()
