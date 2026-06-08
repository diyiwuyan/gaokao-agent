"""工具8: 策略建议

功能：
- 生成冲/稳/保完整方案
- 志愿排序建议
- 风险评估
"""

from langchain_core.tools import tool
from app.data.database import get_connection


@tool
def strategy_suggest(
    score: int,
    rank: int,
    province: str,
    subject_category: str = "物理类",
    preferred_cities: str = "",
    preferred_majors: str = "",
    year: int = 2024,
    志愿数: int = 45
) -> str:
    """基于考生信息生成完整的冲稳保志愿填报方案。
    
    Args:
        score: 高考分数
        rank: 省排名位次
        province: 考生所在省份
        subject_category: 科类
        preferred_cities: 意向城市（逗号分隔，可选）
        preferred_majors: 意向专业方向（逗号分隔，可选）
        year: 参考年份
        志愿数: 可填志愿数量（默认45）
    
    Returns:
        包含冲/稳/保三档的完整志愿方案和填报策略
    """
    city_list = [c.strip() for c in preferred_cities.split(",") if c.strip()]
    major_list = [m.strip() for m in preferred_majors.split(",") if m.strip()]

    with get_connection() as conn:
        # 查询不同位次范围的院校
        # 冲: 位次比考生高 5%-15%
        chong_rank_min = int(rank * 0.85)
        chong_rank_max = int(rank * 0.95)

        # 稳: 位次与考生接近 ±5%
        wen_rank_min = int(rank * 0.95)
        wen_rank_max = int(rank * 1.05)

        # 保: 位次比考生低 10%-25%
        bao_rank_min = int(rank * 1.10)
        bao_rank_max = int(rank * 1.25)

        def query_by_rank(rank_min, rank_max, limit):
            """按位次范围查询院校"""
            query = """
                SELECT DISTINCT college_name, major_name, min_score, min_rank,
                       plan_count
                FROM admission_scores
                WHERE province = ? AND subject_category = ? AND year = ?
                AND min_rank BETWEEN ? AND ?
                AND min_score > 0
            """
            params = [province, subject_category, year, rank_min, rank_max]

            if city_list:
                city_conditions = " OR ".join(["college_name LIKE ?" for _ in city_list])
                # 简化：通过院校名大致匹配地区（实际应关联院校表）

            query += " ORDER BY min_rank ASC LIMIT ?"
            params.append(limit)
            return conn.execute(query, params).fetchall()

        # 如果位次查不到，尝试用分数查
        def query_by_score(score_min, score_max, limit):
            """按分数范围查询院校"""
            return conn.execute("""
                SELECT DISTINCT college_name, major_name, min_score, min_rank,
                       plan_count
                FROM admission_scores
                WHERE province = ? AND subject_category = ? AND year = ?
                AND min_score BETWEEN ? AND ?
                AND min_score > 0
                ORDER BY min_score DESC LIMIT ?
            """, (province, subject_category, year,
                  score_min, score_max, limit)).fetchall()

        # 尝试位次查询
        chong_rows = query_by_rank(chong_rank_min, chong_rank_max, 15)
        wen_rows = query_by_rank(wen_rank_min, wen_rank_max, 20)
        bao_rows = query_by_rank(bao_rank_min, bao_rank_max, 15)

        # 位次数据不足时用分数补充
        if len(chong_rows) < 5:
            chong_rows = query_by_score(score + 5, score + 25, 15)
        if len(wen_rows) < 5:
            wen_rows = query_by_score(score - 5, score + 5, 20)
        if len(bao_rows) < 5:
            bao_rows = query_by_score(score - 25, score - 5, 15)

    # 生成方案
    results = []
    results.append(f"📋 志愿填报方案（{province} {subject_category} {score}分 位次{rank}）")
    results.append(f"{'='*60}")
    results.append(f"参考数据年份: {year} | 可填志愿数: {志愿数}个")
    if city_list:
        results.append(f"意向城市: {', '.join(city_list)}")
    if major_list:
        results.append(f"意向专业: {', '.join(major_list)}")
    results.append("")

    # 冲
    results.append(f"🔴 【冲刺档】建议 {志愿数 // 5} 个志愿 (录取概率 30-50%)")
    results.append("-" * 50)
    if chong_rows:
        seen = set()
        count = 0
        for r in chong_rows:
            if r["college_name"] not in seen and count < 志愿数 // 5:
                seen.add(r["college_name"])
                rank_info = f"位次{r['min_rank']}" if r["min_rank"] else f"{r['min_score']}分"
                results.append(f"  {count+1}. {r['college_name']} - {r['major_name'] or '待选专业'}")
                results.append(f"     {year}年录取: {rank_info} | 计划{r['plan_count'] or '?'}人")
                count += 1
    else:
        results.append("  (数据不足，建议补充数据后重新生成)")
    results.append("")

    # 稳
    results.append(f"🟡 【稳妥档】建议 {志愿数 * 3 // 5} 个志愿 (录取概率 60-80%)")
    results.append("-" * 50)
    if wen_rows:
        seen = set()
        count = 0
        for r in wen_rows:
            if r["college_name"] not in seen and count < 志愿数 * 3 // 5:
                seen.add(r["college_name"])
                rank_info = f"位次{r['min_rank']}" if r["min_rank"] else f"{r['min_score']}分"
                results.append(f"  {count+1}. {r['college_name']} - {r['major_name'] or '待选专业'}")
                results.append(f"     {year}年录取: {rank_info} | 计划{r['plan_count'] or '?'}人")
                count += 1
    else:
        results.append("  (数据不足，建议补充数据后重新生成)")
    results.append("")

    # 保
    results.append(f"🟢 【保底档】建议 {志愿数 // 5} 个志愿 (录取概率 85%+)")
    results.append("-" * 50)
    if bao_rows:
        seen = set()
        count = 0
        for r in bao_rows:
            if r["college_name"] not in seen and count < 志愿数 // 5:
                seen.add(r["college_name"])
                rank_info = f"位次{r['min_rank']}" if r["min_rank"] else f"{r['min_score']}分"
                results.append(f"  {count+1}. {r['college_name']} - {r['major_name'] or '待选专业'}")
                results.append(f"     {year}年录取: {rank_info} | 计划{r['plan_count'] or '?'}人")
                count += 1
    else:
        results.append("  (数据不足，建议补充数据后重新生成)")

    # 填报策略建议
    results.append(f"\n{'='*60}")
    results.append("⚡ 填报策略建议:")
    results.append("  1. 志愿顺序严格按 冲→稳→保 排列，不要打乱")
    results.append("  2. 每档内部也有梯度，同档志愿分数也应递减")
    results.append("  3. 务必勾选「服从专业调剂」，尤其是冲刺档")
    results.append("  4. 最后2-3个志愿一定要确保能录取（真正的兜底）")
    results.append("  5. 关注院校招生章程，确认无单科/体检限制")

    if not (chong_rows or wen_rows or bao_rows):
        results.append(f"\n⚠️ 当前数据库中缺少{province}{year}年{subject_category}的录取数据")
        results.append("   请先运行数据采集脚本填充数据，或手动添加目标院校的录取信息。")

    return "\n".join(results)
