"""工具1: 分数分析

功能：
- 将分数转换为省排名（位次）
- 对比省控线，判断可报批次
- 分析分数在全省的竞争力水平
"""

from langchain_core.tools import tool
from app.data.database import get_connection


@tool
def score_analysis(province: str, score: int, year: int = 2024,
                   subject_category: str = "物理类") -> str:
    """分析考生分数，返回位次、可报批次和竞争力评估。
    
    Args:
        province: 省份，如"河北"
        score: 高考分数
        year: 参考年份（默认2024）
        subject_category: 科类（物理类/历史类/理科/文科）
    
    Returns:
        包含位次、省控线对比、竞争力分析的详细报告
    """
    results = []

    with get_connection() as conn:
        # 1. 查询位次
        rank_row = conn.execute("""
            SELECT rank_number, same_score_count 
            FROM score_rank_table
            WHERE year = ? AND province = ? AND subject_category = ? AND score = ?
        """, (year, province, subject_category, score)).fetchone()

        if rank_row:
            results.append(f"📊 {year}年{province}{subject_category} {score}分对应位次: 第{rank_row['rank_number']}名（同分{rank_row['same_score_count']}人）")
        else:
            # 如果精确分数没有，查找最近的
            nearby = conn.execute("""
                SELECT score, rank_number FROM score_rank_table
                WHERE year = ? AND province = ? AND subject_category = ?
                AND score BETWEEN ? AND ?
                ORDER BY ABS(score - ?) LIMIT 3
            """, (year, province, subject_category, score - 5, score + 5, score)).fetchall()

            if nearby:
                results.append(f"📊 {year}年{province}{subject_category} {score}分附近位次参考：")
                for r in nearby:
                    results.append(f"   {r['score']}分 → 位次 {r['rank_number']}")
            else:
                results.append(f"⚠️ 暂无{year}年{province}{subject_category}的一分一段数据，建议补充数据后重试")

        # 2. 查询省控线
        lines = conn.execute("""
            SELECT batch, score as line_score FROM province_lines
            WHERE year = ? AND province = ? AND subject_category LIKE ?
            ORDER BY score DESC
        """, (year, province, f"%{subject_category}%")).fetchall()

        if lines:
            results.append(f"\n📋 {year}年{province}{subject_category}批次线：")
            for line in lines:
                diff = score - line["line_score"]
                status = f"超线{diff}分 ✅" if diff >= 0 else f"差{-diff}分 ❌"
                results.append(f"   {line['batch']}: {line['line_score']}分 | 你{status}")
        else:
            results.append(f"\n⚠️ 暂无{year}年{province}省控线数据")

        # 3. 竞争力分析
        if rank_row:
            rank = rank_row["rank_number"]
            if rank <= 1000:
                level = "🔥 极强竞争力（全省前1000名），可冲击顶尖985"
            elif rank <= 5000:
                level = "💪 强竞争力（全省前5000名），中上985可选"
            elif rank <= 20000:
                level = "👍 较强竞争力（前2万名），211/双一流目标"
            elif rank <= 50000:
                level = "📈 中等竞争力（前5万名），优质一本目标"
            elif rank <= 100000:
                level = "📊 一般竞争力（前10万名），稳一本/好二本"
            else:
                level = "📋 需要精准择校，关注往年同位次录取情况"
            results.append(f"\n🎯 竞争力评估: {level}")

    if not results:
        return f"暂无{province}{year}年{subject_category}的分析数据，请先运行数据采集。"

    return "\n".join(results)
