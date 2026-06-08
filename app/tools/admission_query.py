"""工具3: 录取查询

功能：
- 查询某院校在某省的历年录取分数线
- 查询某院校某专业的历年录取分数
- 对比多年数据看趋势
"""

from langchain_core.tools import tool
from app.data.database import get_connection


@tool
def admission_query(
    college_name: str,
    province: str,
    subject_category: str = "物理类",
    major_name: str = "",
    years: str = "2022,2023,2024"
) -> str:
    """查询指定院校在指定省份的历年录取分数线。
    
    Args:
        college_name: 院校名称（支持模糊匹配）
        province: 招生省份（考生所在省）
        subject_category: 科类（物理类/历史类/理科/文科）
        major_name: 专业名称（可选，空则查院校整体）
        years: 查询年份，逗号分隔，如"2022,2023,2024"
    
    Returns:
        该院校历年录取分数线详情，含分数趋势分析
    """
    year_list = [int(y.strip()) for y in years.split(",")]

    with get_connection() as conn:
        results = []

        for year in year_list:
            if major_name:
                # 查专业级别
                rows = conn.execute("""
                    SELECT college_name, major_name, min_score, avg_score, 
                           max_score, min_rank, plan_count, batch
                    FROM admission_scores
                    WHERE college_name LIKE ? AND province = ?
                    AND subject_category = ? AND year = ?
                    AND major_name LIKE ?
                    ORDER BY min_score DESC
                """, (f"%{college_name}%", province, subject_category,
                      year, f"%{major_name}%")).fetchall()
            else:
                # 查院校级别（所有专业）
                rows = conn.execute("""
                    SELECT college_name, major_name, min_score, avg_score,
                           max_score, min_rank, plan_count, batch
                    FROM admission_scores
                    WHERE college_name LIKE ? AND province = ?
                    AND subject_category = ? AND year = ?
                    ORDER BY min_score DESC
                    LIMIT 15
                """, (f"%{college_name}%", province, subject_category, year)).fetchall()

            if rows:
                results.append(f"\n📅 {year}年 {rows[0]['college_name']} 在{province}({subject_category})录取情况：")
                results.append(f"{'专业':<20} {'最低分':<8} {'平均分':<8} {'位次':<10} {'计划':<6}")
                results.append("-" * 60)
                for r in rows:
                    major = (r["major_name"] or "院校线")[:18]
                    min_s = str(r["min_score"] or "-")
                    avg_s = str(r["avg_score"] or "-")
                    rank_s = str(r["min_rank"] or "-")
                    plan_s = str(r["plan_count"] or "-")
                    results.append(f"{major:<20} {min_s:<8} {avg_s:<8} {rank_s:<10} {plan_s:<6}")

        if not results:
            return (f"未找到 {college_name} 在 {province}({subject_category}) 的录取数据。"
                    f"可能原因：1) 该校不在{province}招生 2) 数据库暂未收录该校数据")

        # 趋势分析
        all_mins = []
        with get_connection() as conn2:
            for year in year_list:
                min_row = conn2.execute("""
                    SELECT MIN(min_score) as lowest
                    FROM admission_scores
                    WHERE college_name LIKE ? AND province = ?
                    AND subject_category = ? AND year = ?
                    AND min_score > 0
                """, (f"%{college_name}%", province, subject_category, year)).fetchone()
                if min_row and min_row["lowest"]:
                    all_mins.append((year, min_row["lowest"]))

        if len(all_mins) >= 2:
            results.append(f"\n📈 分数趋势分析:")
            for y, s in all_mins:
                results.append(f"   {y}年最低录取分: {s}")
            diff = all_mins[-1][1] - all_mins[0][1]
            trend = "上升" if diff > 0 else "下降" if diff < 0 else "持平"
            results.append(f"   趋势: 近{len(all_mins)}年{trend}{abs(diff)}分")

        return "\n".join(results)
