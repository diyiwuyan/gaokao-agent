"""工具6: 院校对比

功能：
- 多院校横向对比（分数线、位次、就业等）
- 同层次院校对比
- 帮助考生在多个选择间做决策
"""

from langchain_core.tools import tool
from app.data.database import get_connection


@tool
def college_compare(
    colleges: str,
    province: str,
    subject_category: str = "物理类",
    year: int = 2024
) -> str:
    """对比多所院校的录取数据和综合实力，帮助考生做出选择。
    
    Args:
        colleges: 要对比的院校名称，逗号分隔（2-5所）
        province: 考生所在省份
        subject_category: 科类
        year: 参考年份
    
    Returns:
        院校对比报告，包含各维度对比分析
    """
    college_list = [c.strip() for c in colleges.split(",") if c.strip()]

    if len(college_list) < 2:
        return "请提供至少2所院校进行对比，用逗号分隔。"
    if len(college_list) > 5:
        college_list = college_list[:5]

    results = [f"📊 院校对比分析 ({province} {subject_category} {year}年)\n"]
    results.append(f"{'='*70}")

    compare_data = []

    with get_connection() as conn:
        for college_name in college_list:
            # 查询院校基本信息
            info = conn.execute("""
                SELECT name, province, level, category, 
                       is_985, is_211, is_double_first_class
                FROM colleges WHERE name LIKE ? LIMIT 1
            """, (f"%{college_name}%",)).fetchone()

            # 查询录取数据
            scores = conn.execute("""
                SELECT MIN(min_score) as lowest_score,
                       AVG(min_score) as avg_score,
                       MIN(min_rank) as best_rank,
                       MAX(min_rank) as worst_rank,
                       COUNT(DISTINCT major_name) as major_count,
                       SUM(plan_count) as total_plan
                FROM admission_scores
                WHERE college_name LIKE ? AND province = ?
                AND subject_category = ? AND year = ?
                AND min_score > 0
            """, (f"%{college_name}%", province, subject_category, year)).fetchone()

            data = {
                "name": college_name,
                "info": info,
                "scores": scores,
            }
            compare_data.append(data)

    # 格式化对比表
    results.append(f"\n{'院校':<15} {'层次':<12} {'所在地':<8} {'最低分':<8} {'最低位次':<10} {'专业数':<6}")
    results.append("-" * 70)

    for d in compare_data:
        name = d["name"][:12]
        if d["info"]:
            tags = []
            if d["info"]["is_985"]:
                tags.append("985")
            elif d["info"]["is_211"]:
                tags.append("211")
            elif d["info"]["is_double_first_class"]:
                tags.append("双一流")
            else:
                tags.append("普通本科")
            level = "/".join(tags) if tags else "-"
            location = d["info"]["province"] or "-"
        else:
            level = "-"
            location = "-"

        if d["scores"] and d["scores"]["lowest_score"]:
            min_score = str(int(d["scores"]["lowest_score"]))
            worst_rank = str(d["scores"]["worst_rank"] or "-")
            major_count = str(d["scores"]["major_count"] or "-")
        else:
            min_score = "无数据"
            worst_rank = "-"
            major_count = "-"

        results.append(f"{name:<15} {level:<12} {location:<8} {min_score:<8} {worst_rank:<10} {major_count:<6}")

    # 分析建议
    results.append(f"\n{'='*70}")
    results.append("💡 对比分析:")

    # 找出最容易和最难的
    valid_data = [d for d in compare_data if d["scores"] and d["scores"]["lowest_score"]]
    if valid_data:
        easiest = min(valid_data, key=lambda x: x["scores"]["lowest_score"])
        hardest = max(valid_data, key=lambda x: x["scores"]["lowest_score"])
        results.append(f"   📈 录取门槛最高: {hardest['name']} ({int(hardest['scores']['lowest_score'])}分)")
        results.append(f"   📉 录取门槛最低: {easiest['name']} ({int(easiest['scores']['lowest_score'])}分)")

        score_gap = int(hardest["scores"]["lowest_score"] - easiest["scores"]["lowest_score"])
        results.append(f"   📏 分差范围: {score_gap}分")

        if score_gap <= 10:
            results.append("   🤔 这几所院校录取分相近，建议从专业实力、地理位置、校园环境等维度综合考虑")
        elif score_gap <= 30:
            results.append("   💡 分差适中，可以形成合理的冲-稳-保梯度")
        else:
            results.append("   ⚠️ 分差较大，建议确认是否都是同一梯度的选择")

    return "\n".join(results)
