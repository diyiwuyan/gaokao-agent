"""工具2: 院校检索

功能：
- 按层次（985/211/双一流）筛选
- 按地区、类型筛选
- 按分数范围筛选有录取可能的院校
"""

from langchain_core.tools import tool
from app.data.database import get_connection


@tool
def college_search(
    province: str = "",
    level: str = "",
    category: str = "",
    score_min: int = 0,
    score_max: int = 750,
    target_province: str = "",
    year: int = 2024,
    subject_category: str = "物理类",
    limit: int = 20
) -> str:
    """根据条件检索院校，支持按层次/地区/分数范围等多维筛选。
    
    Args:
        province: 院校所在省份（空=不限）
        level: 院校层次筛选，如"985""211""双一流"
        category: 院校类型，如"理工""综合""师范""医药"
        score_min: 最低分数要求
        score_max: 最高分数上限
        target_province: 招生省份（考生所在省）
        year: 参考年份
        subject_category: 科类
        limit: 返回数量上限
    
    Returns:
        符合条件的院校列表，含基本信息和历年录取分数
    """
    with get_connection() as conn:
        # 构建查询
        conditions = []
        params = []

        if province:
            conditions.append("c.province LIKE ?")
            params.append(f"%{province}%")
        if level:
            if "985" in level:
                conditions.append("c.is_985 = 1")
            elif "211" in level:
                conditions.append("c.is_211 = 1")
            elif "双一流" in level:
                conditions.append("c.is_double_first_class = 1")
        if category:
            conditions.append("c.category LIKE ?")
            params.append(f"%{category}%")

        # 如果有分数条件，关联录取分数表
        if target_province and (score_min > 0 or score_max < 750):
            query = """
                SELECT DISTINCT c.name, c.province, c.city, c.level, c.category,
                       c.is_985, c.is_211, c.is_double_first_class,
                       a.min_score, a.min_rank, a.year as record_year
                FROM colleges c
                JOIN admission_scores a ON c.college_id = a.college_id
                WHERE a.province = ? AND a.year = ? AND a.subject_category = ?
                AND a.min_score BETWEEN ? AND ?
            """
            params_full = [target_province, year, subject_category, score_min, score_max]

            if conditions:
                query += " AND " + " AND ".join(conditions)
                params_full.extend(params)

            query += " ORDER BY a.min_score DESC LIMIT ?"
            params_full.append(limit)

            rows = conn.execute(query, params_full).fetchall()
        else:
            # 仅按院校属性查询
            query = "SELECT name, province, city, level, category, is_985, is_211, is_double_first_class FROM colleges c"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()

        if not rows:
            return f"未找到符合条件的院校。可能原因：1) 数据库中暂无相关数据 2) 筛选条件过于严格，建议放宽条件重试。"

        # 格式化输出
        results = [f"🏫 找到 {len(rows)} 所符合条件的院校：\n"]
        for i, row in enumerate(rows, 1):
            tags = []
            if row["is_985"]:
                tags.append("985")
            if row["is_211"]:
                tags.append("211")
            if row["is_double_first_class"]:
                tags.append("双一流")
            tag_str = f" [{'/'.join(tags)}]" if tags else ""

            city = row["city"] if "city" in row.keys() else ""
            category = row["category"] if "category" in row.keys() else ""
            line = f"{i}. {row['name']}{tag_str} | {row['province']}{city} | {category}"

            # 如果有分数信息
            if "min_score" in row.keys() and row["min_score"]:
                record_year = row["record_year"] if "record_year" in row.keys() else year
                line += f" | {record_year}年最低{row['min_score']}分"
                if "min_rank" in row.keys() and row["min_rank"]:
                    line += f"(位次{row['min_rank']})"

            results.append(line)

        return "\n".join(results)
