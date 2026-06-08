"""工具4: 录取概率计算

核心算法：位次法
- 将考生分数转换为位次
- 对比目标院校/专业历年录取位次
- 综合多年数据计算录取概率
"""

from langchain_core.tools import tool
from app.data.database import get_connection


@tool
def probability_calc(
    score: int,
    rank: int,
    college_name: str,
    province: str,
    subject_category: str = "物理类",
    major_name: str = "",
    years: str = "2022,2023,2024"
) -> str:
    """基于位次法计算考生被某院校/专业录取的概率。
    
    Args:
        score: 考生高考分数
        rank: 考生省排名（位次）
        college_name: 目标院校名称
        province: 考生所在省份
        subject_category: 科类
        major_name: 目标专业（可选）
        years: 参考年份
    
    Returns:
        录取概率分析报告，包含概率值和冲/稳/保建议
    """
    year_list = [int(y.strip()) for y in years.split(",")]

    with get_connection() as conn:
        # 获取历年录取位次
        historical_ranks = []
        historical_scores = []

        for year in year_list:
            if major_name:
                row = conn.execute("""
                    SELECT min_score, min_rank, avg_score
                    FROM admission_scores
                    WHERE college_name LIKE ? AND province = ?
                    AND subject_category = ? AND year = ?
                    AND major_name LIKE ?
                    ORDER BY min_score ASC LIMIT 1
                """, (f"%{college_name}%", province, subject_category,
                      year, f"%{major_name}%")).fetchone()
            else:
                row = conn.execute("""
                    SELECT MIN(min_score) as min_score, MAX(min_rank) as min_rank,
                           AVG(avg_score) as avg_score
                    FROM admission_scores
                    WHERE college_name LIKE ? AND province = ?
                    AND subject_category = ? AND year = ?
                    AND min_score > 0
                """, (f"%{college_name}%", province, subject_category, year)).fetchone()

            if row and row["min_rank"]:
                historical_ranks.append({"year": year, "rank": row["min_rank"], "score": row["min_score"]})
            elif row and row["min_score"]:
                historical_scores.append({"year": year, "score": row["min_score"]})

    if not historical_ranks and not historical_scores:
        return (f"❌ 无法计算概率：未找到 {college_name} "
                f"{'('+major_name+')' if major_name else ''} "
                f"在{province}的历年录取数据。")

    # 计算概率
    results = []
    target_desc = f"{college_name}{'·' + major_name if major_name else ''}"
    results.append(f"🎯 录取概率分析: {target_desc}")
    results.append(f"   你的分数: {score}分 | 位次: {rank}")
    results.append("")

    if historical_ranks:
        # 基于位次法计算
        results.append("📊 历年录取位次对比:")
        probs = []
        for hr in historical_ranks:
            diff = hr["rank"] - rank  # 正数=你的位次更靠前=更有机会
            if diff > 0:
                # 位次在录取线之上
                if diff > hr["rank"] * 0.2:
                    prob = 0.95
                elif diff > hr["rank"] * 0.1:
                    prob = 0.85
                elif diff > hr["rank"] * 0.05:
                    prob = 0.70
                else:
                    prob = 0.60
            elif diff == 0:
                prob = 0.50
            else:
                # 位次在录取线之下
                abs_diff = abs(diff)
                if abs_diff < hr["rank"] * 0.05:
                    prob = 0.35
                elif abs_diff < hr["rank"] * 0.1:
                    prob = 0.20
                elif abs_diff < hr["rank"] * 0.2:
                    prob = 0.10
                else:
                    prob = 0.05

            probs.append(prob)
            score_diff = score - (hr["score"] or 0)
            results.append(
                f"   {hr['year']}年: 录取位次{hr['rank']} | "
                f"你的位次{rank} | 差距{diff:+d} | "
                f"分差{score_diff:+d}"
            )

        # 综合概率（加权平均，近年权重更高）
        weights = list(range(1, len(probs) + 1))  # 越新的年份权重越高
        total_weight = sum(weights)
        final_prob = sum(p * w for p, w in zip(probs, weights)) / total_weight

    elif historical_scores:
        # 仅基于分数差计算（精度较低）
        results.append("📊 历年录取分数对比（无位次数据，精度较低）:")
        probs = []
        for hs in historical_scores:
            diff = score - hs["score"]
            if diff >= 30:
                prob = 0.90
            elif diff >= 15:
                prob = 0.75
            elif diff >= 5:
                prob = 0.60
            elif diff >= 0:
                prob = 0.45
            elif diff >= -10:
                prob = 0.25
            elif diff >= -20:
                prob = 0.10
            else:
                prob = 0.05
            probs.append(prob)
            results.append(f"   {hs['year']}年: 最低录取{hs['score']}分 | 你{score}分 | 差距{diff:+d}")

        weights = list(range(1, len(probs) + 1))
        total_weight = sum(weights)
        final_prob = sum(p * w for p, w in zip(probs, weights)) / total_weight

    # 给出建议
    results.append(f"\n🎲 综合录取概率: {final_prob:.0%}")

    if final_prob >= 0.80:
        level = "保"
        emoji = "🟢"
        advice = "该校/专业属于你的保底选择，录取把握很大"
    elif final_prob >= 0.55:
        level = "稳"
        emoji = "🟡"
        advice = "该校/专业录取概率较高，建议作为稳妥选择"
    elif final_prob >= 0.30:
        level = "冲"
        emoji = "🟠"
        advice = "有一定录取可能，建议作为冲刺目标"
    else:
        level = "危险"
        emoji = "🔴"
        advice = "录取风险较高，不建议作为主要志愿"

    results.append(f"{emoji} 建议等级: 【{level}】")
    results.append(f"💡 建议: {advice}")

    return "\n".join(results)
