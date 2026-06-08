"""工具5: 专业推荐

功能：
- 基于兴趣方向推荐专业
- 结合就业前景和薪资数据
- 考虑选科限制
"""

from langchain_core.tools import tool


# 专业数据（内置知识库，后续可从数据库加载）
MAJOR_DATABASE = {
    "计算机科学与技术": {
        "category": "工学",
        "hot_level": 5,
        "salary_rank": "A+",
        "employment_rate": 0.95,
        "description": "学习计算机系统和软件开发，就业面极广",
        "careers": ["软件工程师", "算法工程师", "产品经理", "数据分析师"],
        "subjects_required": ["物理"],
        "difficulty": "中高",
    },
    "人工智能": {
        "category": "工学",
        "hot_level": 5,
        "salary_rank": "A+",
        "employment_rate": 0.92,
        "description": "前沿交叉学科，研究机器学习、深度学习等",
        "careers": ["AI工程师", "算法研究员", "数据科学家"],
        "subjects_required": ["物理", "数学强"],
        "difficulty": "高",
    },
    "电子信息工程": {
        "category": "工学",
        "hot_level": 4,
        "salary_rank": "A",
        "employment_rate": 0.93,
        "description": "学习电子电路和信号处理，硬件+软件兼备",
        "careers": ["硬件工程师", "通信工程师", "嵌入式开发"],
        "subjects_required": ["物理"],
        "difficulty": "中高",
    },
    "临床医学": {
        "category": "医学",
        "hot_level": 4,
        "salary_rank": "A",
        "employment_rate": 0.88,
        "description": "培养临床医生，学制长（5+3），社会地位高",
        "careers": ["临床医生", "外科医生", "医学研究"],
        "subjects_required": ["物理", "化学", "生物"],
        "difficulty": "极高",
    },
    "金融学": {
        "category": "经济学",
        "hot_level": 4,
        "salary_rank": "A",
        "employment_rate": 0.85,
        "description": "学习金融市场运作，就业方向多元",
        "careers": ["投行分析师", "基金经理", "风控", "银行"],
        "subjects_required": [],
        "difficulty": "中",
    },
    "法学": {
        "category": "法学",
        "hot_level": 3,
        "salary_rank": "B+",
        "employment_rate": 0.72,
        "description": "需通过法考，门槛高但上限高",
        "careers": ["律师", "法官", "检察官", "法务"],
        "subjects_required": [],
        "difficulty": "高",
    },
    "机械工程": {
        "category": "工学",
        "hot_level": 3,
        "salary_rank": "B+",
        "employment_rate": 0.90,
        "description": "传统工科，就业稳定但起薪一般",
        "careers": ["机械设计", "制造工程师", "质量工程师"],
        "subjects_required": ["物理"],
        "difficulty": "中",
    },
    "汉语言文学": {
        "category": "文学",
        "hot_level": 3,
        "salary_rank": "B",
        "employment_rate": 0.80,
        "description": "就业方向广泛，偏公务员/教师/编辑",
        "careers": ["教师", "编辑", "公务员", "文案策划"],
        "subjects_required": [],
        "difficulty": "中",
    },
    "电气工程及其自动化": {
        "category": "工学",
        "hot_level": 4,
        "salary_rank": "A",
        "employment_rate": 0.94,
        "description": "国家电网等央企对口专业，就业稳定收入高",
        "careers": ["电力工程师", "自动化工程师", "国家电网"],
        "subjects_required": ["物理"],
        "difficulty": "中高",
    },
    "口腔医学": {
        "category": "医学",
        "hot_level": 5,
        "salary_rank": "A+",
        "employment_rate": 0.95,
        "description": "高收入医学方向，不用值夜班，回报率极高",
        "careers": ["口腔医生", "正畸医生", "口腔外科"],
        "subjects_required": ["物理", "化学", "生物"],
        "difficulty": "高",
    },
    "数据科学与大数据技术": {
        "category": "工学",
        "hot_level": 5,
        "salary_rank": "A",
        "employment_rate": 0.93,
        "description": "新兴交叉学科，结合统计+计算机",
        "careers": ["数据分析师", "数据工程师", "商业分析"],
        "subjects_required": ["物理"],
        "difficulty": "中高",
    },
    "会计学": {
        "category": "管理学",
        "hot_level": 3,
        "salary_rank": "B+",
        "employment_rate": 0.82,
        "description": "就业面广，需考CPA，AI替代风险中等",
        "careers": ["审计", "会计", "财务管理", "税务"],
        "subjects_required": [],
        "difficulty": "中",
    },
}


@tool
def major_recommend(
    interests: str = "",
    subjects: str = "",
    priority: str = "就业",
    avoid: str = "",
) -> str:
    """根据考生兴趣、选科和优先级推荐合适的专业方向。
    
    Args:
        interests: 兴趣方向，如"编程""医学""金融""文学"等，逗号分隔
        subjects: 选科组合，如"物理,化学,生物"
        priority: 优先考虑因素："就业"/"薪资"/"兴趣"/"稳定"
        avoid: 排除方向，如"医学""工科"
    
    Returns:
        专业推荐列表，附带就业分析和薪资参考
    """
    interest_list = [i.strip() for i in interests.split(",") if i.strip()]
    subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
    avoid_list = [a.strip() for a in avoid.split(",") if a.strip()]

    # 筛选和评分
    scored_majors = []

    for name, info in MAJOR_DATABASE.items():
        # 排除
        skip = False
        for avoid_item in avoid_list:
            if avoid_item in name or avoid_item in info["category"]:
                skip = True
                break
        if skip:
            continue

        # 选科限制检查
        if subject_list and info["subjects_required"]:
            has_required = any(
                req in subject_list or any(req in s for s in subject_list)
                for req in info["subjects_required"]
            )
            if not has_required:
                continue

        # 评分
        score = 0

        # 兴趣匹配
        for interest in interest_list:
            if interest in name or interest in info["description"] or interest in info["category"]:
                score += 30
            for career in info["careers"]:
                if interest in career:
                    score += 20

        # 优先级加分
        if priority == "就业":
            score += info["employment_rate"] * 30
        elif priority == "薪资":
            salary_scores = {"A+": 40, "A": 30, "B+": 20, "B": 10}
            score += salary_scores.get(info["salary_rank"], 5)
        elif priority == "稳定":
            score += info["employment_rate"] * 25
            if info["hot_level"] <= 3:  # 非热门=竞争小=更稳
                score += 10

        # 热度加分
        score += info["hot_level"] * 5

        scored_majors.append((name, info, score))

    # 排序
    scored_majors.sort(key=lambda x: x[2], reverse=True)
    top_majors = scored_majors[:8]

    if not top_majors:
        return "未找到符合条件的专业推荐，建议放宽筛选条件。"

    # 格式化输出
    results = [f"🎓 专业推荐（优先级: {priority}）\n"]

    for i, (name, info, _score) in enumerate(top_majors, 1):
        results.append(f"{'='*50}")
        results.append(f"  {i}. {name}")
        results.append(f"     学科门类: {info['category']} | 薪资等级: {info['salary_rank']} | 就业率: {info['employment_rate']:.0%}")
        results.append(f"     热门程度: {'🔥' * info['hot_level']} | 学习难度: {info['difficulty']}")
        results.append(f"     简介: {info['description']}")
        results.append(f"     典型就业: {', '.join(info['careers'])}")
        if info["subjects_required"]:
            results.append(f"     选科要求: {', '.join(info['subjects_required'])}")
        results.append("")

    results.append("💡 提示: 专业选择建议结合个人兴趣、就业前景和学科实力综合考虑")
    return "\n".join(results)
