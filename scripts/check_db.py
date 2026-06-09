"""验证数据库完整性"""
import sqlite3

conn = sqlite3.connect('data/gaokao.db')
cur = conn.cursor()

print("=" * 60)
print("  数据库完整性验证")
print("=" * 60)

# 1. 表统计
print("\n=== 各表数据量 ===")
tables = ['colleges', 'majors', 'college_majors', 'admission_scores',
          'province_lines', 'score_rank_table', 'enrollment_plans']
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {cur.fetchone()[0]} 条")

# 2. 省份覆盖
print("\n=== 省份覆盖 ===")
cur.execute("SELECT DISTINCT province FROM admission_scores ORDER BY province")
provinces = [r[0] for r in cur.fetchall()]
print(f"  录取数据: {provinces}")

cur.execute("SELECT DISTINCT province FROM province_lines ORDER BY province")
print(f"  省控线: {[r[0] for r in cur.fetchall()]}")

cur.execute("SELECT DISTINCT province FROM score_rank_table ORDER BY province")
print(f"  一分一段: {[r[0] for r in cur.fetchall()]}")

# 3. 年份覆盖
print("\n=== 年份覆盖 ===")
cur.execute("SELECT DISTINCT year FROM admission_scores ORDER BY year")
print(f"  录取数据: {[r[0] for r in cur.fetchall()]}")

cur.execute("SELECT DISTINCT year FROM enrollment_plans ORDER BY year")
print(f"  招生计划: {[r[0] for r in cur.fetchall()]}")

# 4. 科类覆盖
print("\n=== 科类覆盖 ===")
cur.execute("SELECT DISTINCT subject_category FROM admission_scores")
print(f"  录取科类: {[r[0] for r in cur.fetchall()]}")

# 5. 各省录取数据量
print("\n=== 各省录取数据分布 ===")
cur.execute("""
    SELECT province, subject_category, COUNT(*) 
    FROM admission_scores 
    GROUP BY province, subject_category 
    ORDER BY province
""")
for r in cur.fetchall():
    print(f"  {r[0]} - {r[1]}: {r[2]} 条")

# 6. 专业库检查
print("\n=== 专业库 ===")
cur.execute("SELECT COUNT(*) FROM majors")
print(f"  专业总数: {cur.fetchone()[0]}")
cur.execute("SELECT DISTINCT category FROM majors ORDER BY category")
print(f"  学科门类: {[r[0] for r in cur.fetchall()]}")

# 7. 院校-专业关联检查
print("\n=== 院校-专业关联 ===")
cur.execute("SELECT COUNT(*) FROM college_majors")
print(f"  关联总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(DISTINCT college_id) FROM college_majors")
print(f"  有专业的院校数: {cur.fetchone()[0]}")

# 8. 招生计划
print("\n=== 招生计划 ===")
cur.execute("SELECT COUNT(*) FROM enrollment_plans")
print(f"  计划总数: {cur.fetchone()[0]}")
cur.execute("SELECT AVG(tuition), MIN(tuition), MAX(tuition) FROM enrollment_plans")
r = cur.fetchone()
print(f"  学费: 平均{r[0]:.0f}, 最低{r[1]}, 最高{r[2]}")

# 9. 数据样例
print("\n=== 录取数据样例（清华大学 - 广东 - 2024）===")
cur.execute("""
    SELECT major_name, subject_category, min_score, min_rank, plan_count
    FROM admission_scores
    WHERE college_name='清华大学' AND province='广东' AND year=2024
    ORDER BY min_score DESC LIMIT 5
""")
for r in cur.fetchall():
    print(f"  {r[0]} ({r[1]}): {r[2]}分 / 位次{r[3]} / 计划{r[4]}人")

# 10. 一分一段样例
print("\n=== 一分一段样例（山东 - 物理类 - 2024 - 前5名）===")
cur.execute("""
    SELECT score, rank_number, same_score_count
    FROM score_rank_table
    WHERE province='山东' AND subject_category='物理类' AND year=2024
    ORDER BY score DESC LIMIT 5
""")
for r in cur.fetchall():
    print(f"  {r[0]}分: 累计{r[1]}人, 同分{r[2]}人")

# 11. DB文件大小
import os
db_size = os.path.getsize('data/gaokao.db')
print(f"\n=== 数据库文件 ===")
print(f"  大小: {db_size / 1024 / 1024:.2f} MB")

print(f"\n{'='*60}")
print("  验证完成!")
print(f"{'='*60}")

conn.close()
