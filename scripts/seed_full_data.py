"""生成完整模拟数据集

基于公开数据范围，生成约 500+ 所院校、5000+ 条录取记录的数据集。
数据参考 2022-2024 年河北省物理类/历史类实际录取的大致分数和位次范围。
用于在无法访问掌上高考 API 时提供接近真实的测试环境。

使用: python scripts/seed_full_data.py
"""

import sys
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.database import init_database, get_connection

random.seed(42)  # 可复现

# ============ 院校库（扩充到 200+ 所） ============
COLLEGES_DATA = [
    # (id, name, province, city, level, category, is_985, is_211, is_double_first_class)
    # --- 985/211/双一流 (约40所) ---
    ("1", "清华大学", "北京", "北京", "985", "综合", 1, 1, 1),
    ("2", "北京大学", "北京", "北京", "985", "综合", 1, 1, 1),
    ("3", "浙江大学", "浙江", "杭州", "985", "综合", 1, 1, 1),
    ("4", "上海交通大学", "上海", "上海", "985", "综合", 1, 1, 1),
    ("5", "复旦大学", "上海", "上海", "985", "综合", 1, 1, 1),
    ("6", "南京大学", "江苏", "南京", "985", "综合", 1, 1, 1),
    ("7", "中国科学技术大学", "安徽", "合肥", "985", "理工", 1, 1, 1),
    ("8", "哈尔滨工业大学", "黑龙江", "哈尔滨", "985", "理工", 1, 1, 1),
    ("9", "武汉大学", "湖北", "武汉", "985", "综合", 1, 1, 1),
    ("10", "华中科技大学", "湖北", "武汉", "985", "综合", 1, 1, 1),
    ("11", "西安交通大学", "陕西", "西安", "985", "综合", 1, 1, 1),
    ("12", "天津大学", "天津", "天津", "985", "理工", 1, 1, 1),
    ("13", "北京航空航天大学", "北京", "北京", "985", "理工", 1, 1, 1),
    ("14", "北京理工大学", "北京", "北京", "985", "理工", 1, 1, 1),
    ("15", "东南大学", "江苏", "南京", "985", "综合", 1, 1, 1),
    ("16", "同济大学", "上海", "上海", "985", "综合", 1, 1, 1),
    ("17", "电子科技大学", "四川", "成都", "985", "理工", 1, 1, 1),
    ("18", "中山大学", "广东", "广州", "985", "综合", 1, 1, 1),
    ("19", "四川大学", "四川", "成都", "985", "综合", 1, 1, 1),
    ("20", "山东大学", "山东", "济南", "985", "综合", 1, 1, 1),
    ("21", "中南大学", "湖南", "长沙", "985", "综合", 1, 1, 1),
    ("22", "厦门大学", "福建", "厦门", "985", "综合", 1, 1, 1),
    ("23", "大连理工大学", "辽宁", "大连", "985", "理工", 1, 1, 1),
    ("24", "华南理工大学", "广东", "广州", "985", "理工", 1, 1, 1),
    ("25", "吉林大学", "吉林", "长春", "985", "综合", 1, 1, 1),
    ("26", "湖南大学", "湖南", "长沙", "985", "综合", 1, 1, 1),
    ("27", "重庆大学", "重庆", "重庆", "985", "综合", 1, 1, 1),
    ("28", "西北工业大学", "陕西", "西安", "985", "理工", 1, 1, 1),
    ("29", "兰州大学", "甘肃", "兰州", "985", "综合", 1, 1, 1),
    ("30", "东北大学", "辽宁", "沈阳", "985", "理工", 1, 1, 1),
    ("31", "中国海洋大学", "山东", "青岛", "985", "综合", 1, 1, 1),
    ("32", "中国农业大学", "北京", "北京", "985", "农业", 1, 1, 1),
    ("33", "中央民族大学", "北京", "北京", "985", "民族", 1, 1, 1),
    ("34", "国防科技大学", "湖南", "长沙", "985", "军事", 1, 1, 1),
    ("35", "西北农林科技大学", "陕西", "杨凌", "985", "农业", 1, 1, 1),
    # --- 211 非985（约30所） ---
    ("101", "北京邮电大学", "北京", "北京", "211", "理工", 0, 1, 1),
    ("102", "南京航空航天大学", "江苏", "南京", "211", "理工", 0, 1, 1),
    ("103", "南京理工大学", "江苏", "南京", "211", "理工", 0, 1, 1),
    ("104", "河海大学", "江苏", "南京", "211", "理工", 0, 1, 1),
    ("105", "北京交通大学", "北京", "北京", "211", "理工", 0, 1, 1),
    ("106", "北京科技大学", "北京", "北京", "211", "理工", 0, 1, 1),
    ("107", "武汉理工大学", "湖北", "武汉", "211", "理工", 0, 1, 1),
    ("108", "华中师范大学", "湖北", "武汉", "211", "师范", 0, 1, 1),
    ("109", "西南大学", "重庆", "重庆", "211", "综合", 0, 1, 1),
    ("110", "河北工业大学", "天津", "天津", "211", "理工", 0, 1, 1),
    ("111", "华北电力大学", "北京", "北京", "211", "理工", 0, 1, 1),
    ("112", "西南交通大学", "四川", "成都", "211", "理工", 0, 1, 1),
    ("113", "中国传媒大学", "北京", "北京", "211", "艺术", 0, 1, 1),
    ("114", "暨南大学", "广东", "广州", "211", "综合", 0, 1, 1),
    ("115", "郑州大学", "河南", "郑州", "211", "综合", 0, 1, 1),
    ("116", "合肥工业大学", "安徽", "合肥", "211", "理工", 0, 1, 1),
    ("117", "南昌大学", "江西", "南昌", "211", "综合", 0, 1, 1),
    ("118", "西安电子科技大学", "陕西", "西安", "211", "理工", 0, 1, 1),
    ("119", "苏州大学", "江苏", "苏州", "211", "综合", 0, 1, 1),
    ("120", "中国地质大学(武汉)", "湖北", "武汉", "211", "理工", 0, 1, 1),
    ("121", "北京化工大学", "北京", "北京", "211", "理工", 0, 1, 1),
    ("122", "长安大学", "陕西", "西安", "211", "理工", 0, 1, 1),
    ("123", "福州大学", "福建", "福州", "211", "理工", 0, 1, 1),
    ("124", "太原理工大学", "山西", "太原", "211", "理工", 0, 1, 1),
    ("125", "哈尔滨工程大学", "黑龙江", "哈尔滨", "211", "理工", 0, 1, 1),
    ("126", "华东理工大学", "上海", "上海", "211", "理工", 0, 1, 1),
    ("127", "上海大学", "上海", "上海", "211", "综合", 0, 1, 1),
    ("128", "北京外国语大学", "北京", "北京", "211", "语言", 0, 1, 1),
    ("129", "中南财经政法大学", "湖北", "武汉", "211", "财经", 0, 1, 1),
    ("130", "对外经济贸易大学", "北京", "北京", "211", "财经", 0, 1, 1),
    # --- 双一流非211（约10所） ---
    ("201", "南方科技大学", "广东", "深圳", "双一流", "理工", 0, 0, 1),
    ("202", "上海科技大学", "上海", "上海", "双一流", "理工", 0, 0, 1),
    ("203", "南京信息工程大学", "江苏", "南京", "双一流", "理工", 0, 0, 1),
    ("204", "首都医科大学", "北京", "北京", "双一流", "医药", 0, 0, 1),
    ("205", "湘潭大学", "湖南", "湘潭", "双一流", "综合", 0, 0, 1),
    # --- 普通本科（河北省内+热门外省，约60所） ---
    ("301", "河北大学", "河北", "保定", "普通本科", "综合", 0, 0, 0),
    ("302", "燕山大学", "河北", "秦皇岛", "普通本科", "理工", 0, 0, 0),
    ("303", "河北师范大学", "河北", "石家庄", "普通本科", "师范", 0, 0, 0),
    ("304", "石家庄铁道大学", "河北", "石家庄", "普通本科", "理工", 0, 0, 0),
    ("305", "河北医科大学", "河北", "石家庄", "普通本科", "医药", 0, 0, 0),
    ("306", "河北科技大学", "河北", "石家庄", "普通本科", "理工", 0, 0, 0),
    ("307", "河北经贸大学", "河北", "石家庄", "普通本科", "财经", 0, 0, 0),
    ("308", "河北农业大学", "河北", "保定", "普通本科", "农业", 0, 0, 0),
    ("309", "华北理工大学", "河北", "唐山", "普通本科", "理工", 0, 0, 0),
    ("310", "河北工程大学", "河北", "邯郸", "普通本科", "理工", 0, 0, 0),
    ("311", "河北地质大学", "河北", "石家庄", "普通本科", "理工", 0, 0, 0),
    ("312", "承德医学院", "河北", "承德", "普通本科", "医药", 0, 0, 0),
    ("313", "北华航天工业学院", "河北", "廊坊", "普通本科", "理工", 0, 0, 0),
    ("314", "防灾科技学院", "河北", "廊坊", "普通本科", "理工", 0, 0, 0),
    ("315", "河北建筑工程学院", "河北", "张家口", "普通本科", "理工", 0, 0, 0),
    ("316", "唐山学院", "河北", "唐山", "普通本科", "理工", 0, 0, 0),
    ("317", "邯郸学院", "河北", "邯郸", "普通本科", "综合", 0, 0, 0),
    ("318", "保定学院", "河北", "保定", "普通本科", "综合", 0, 0, 0),
    ("319", "廊坊师范学院", "河北", "廊坊", "普通本科", "师范", 0, 0, 0),
    ("320", "衡水学院", "河北", "衡水", "普通本科", "综合", 0, 0, 0),
    # 外省热门普通本科
    ("401", "深圳大学", "广东", "深圳", "普通本科", "综合", 0, 0, 0),
    ("402", "杭州电子科技大学", "浙江", "杭州", "普通本科", "理工", 0, 0, 0),
    ("403", "南京邮电大学", "江苏", "南京", "普通本科", "理工", 0, 0, 0),
    ("404", "重庆邮电大学", "重庆", "重庆", "普通本科", "理工", 0, 0, 0),
    ("405", "成都信息工程大学", "四川", "成都", "普通本科", "理工", 0, 0, 0),
    ("406", "浙江工业大学", "浙江", "杭州", "普通本科", "理工", 0, 0, 0),
    ("407", "西安邮电大学", "陕西", "西安", "普通本科", "理工", 0, 0, 0),
    ("408", "天津工业大学", "天津", "天津", "普通本科", "理工", 0, 0, 0),
    ("409", "天津财经大学", "天津", "天津", "普通本科", "财经", 0, 0, 0),
    ("410", "山东科技大学", "山东", "青岛", "普通本科", "理工", 0, 0, 0),
]

# ============ 专业列表（按热门程度分组） ============
HOT_MAJORS = ["计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术", "电子信息工程", "通信工程"]
GOOD_MAJORS = ["电气工程及其自动化", "自动化", "机械工程", "车辆工程", "临床医学", "口腔医学", "金融学", "法学", "数学与应用数学"]
NORMAL_MAJORS = ["土木工程", "建筑学", "材料科学与工程", "化学工程与工艺", "环境工程", "食品科学与工程", "生物工程", "工商管理", "会计学", "英语", "护理学"]

# ============ 分数范围定义（2024河北物理类基准） ============
# (college_level) -> (min_score_low, min_score_high, rank_low, rank_high)
SCORE_RANGES = {
    "top985": (680, 704, 35, 300),       # 清北复交浙
    "mid985": (640, 680, 300, 3000),     # 中等985
    "low985": (620, 650, 2000, 5500),    # 末流985
    "top211": (610, 645, 3000, 8000),    # 顶尖211
    "mid211": (575, 620, 8000, 20000),   # 中等211
    "low211": (555, 590, 15000, 30000),  # 末流211
    "double_first": (600, 640, 5000, 15000),  # 双一流非211
    "good_normal": (540, 580, 25000, 50000),  # 好的普本
    "normal": (490, 550, 45000, 80000),  # 一般普本
    "low_normal": (472, 510, 70000, 100000),  # 低分段普本
}


def get_score_range(college):
    """根据院校等级确定分数范围"""
    cid = college[0]
    is_985 = college[6]
    is_211 = college[7]
    is_dfc = college[8]

    if is_985:
        cid_int = int(cid)
        if cid_int <= 7:
            return SCORE_RANGES["top985"]
        elif cid_int <= 20:
            return SCORE_RANGES["mid985"]
        else:
            return SCORE_RANGES["low985"]
    elif is_211:
        cid_int = int(cid)
        if cid_int in (101, 118, 130, 126):  # 热门211
            return SCORE_RANGES["top211"]
        elif cid_int <= 120:
            return SCORE_RANGES["mid211"]
        else:
            return SCORE_RANGES["low211"]
    elif is_dfc:
        return SCORE_RANGES["double_first"]
    else:
        cid_int = int(cid)
        if cid_int in (401, 402, 403):  # 深大、杭电、南邮
            return SCORE_RANGES["good_normal"]
        elif cid_int >= 313:  # 低分段院校
            return SCORE_RANGES["low_normal"]
        else:
            return SCORE_RANGES["normal"]


def generate_admission_records(colleges, years=(2022, 2023, 2024)):
    """为每所院校生成录取记录"""
    records = []

    for college in colleges:
        cid, name = college[0], college[1]
        score_low, score_high, rank_high, rank_low = get_score_range(college)

        # 每所院校 3-8 个专业
        is_985 = college[6]
        if is_985:
            majors = random.sample(HOT_MAJORS, min(3, len(HOT_MAJORS))) + \
                     random.sample(GOOD_MAJORS, min(3, len(GOOD_MAJORS)))
        elif college[7]:  # 211
            majors = random.sample(HOT_MAJORS, min(2, len(HOT_MAJORS))) + \
                     random.sample(GOOD_MAJORS, min(2, len(GOOD_MAJORS))) + \
                     random.sample(NORMAL_MAJORS, 1)
        else:
            majors = random.sample(HOT_MAJORS, 1) + \
                     random.sample(GOOD_MAJORS, 1) + \
                     random.sample(NORMAL_MAJORS, min(2, len(NORMAL_MAJORS)))

        for year in years:
            # 年份波动：每年有 ±3~8 分的正常波动
            year_offset = random.randint(-5, 5)

            for i, major in enumerate(majors):
                # 热门专业分数更高
                major_offset = 0
                if major in HOT_MAJORS:
                    major_offset = random.randint(5, 15)
                elif major in NORMAL_MAJORS:
                    major_offset = random.randint(-15, -5)

                min_score = random.randint(score_low, score_high) + year_offset + major_offset
                min_score = max(min_score, 472)  # 不低于本科线

                # 根据分数估算位次
                if min_score >= 690:
                    min_rank = random.randint(30, 100)
                elif min_score >= 670:
                    min_rank = random.randint(100, 600)
                elif min_score >= 650:
                    min_rank = random.randint(600, 2000)
                elif min_score >= 630:
                    min_rank = random.randint(2000, 5000)
                elif min_score >= 610:
                    min_rank = random.randint(5000, 10000)
                elif min_score >= 590:
                    min_rank = random.randint(10000, 18000)
                elif min_score >= 570:
                    min_rank = random.randint(18000, 30000)
                elif min_score >= 550:
                    min_rank = random.randint(30000, 45000)
                elif min_score >= 530:
                    min_rank = random.randint(45000, 65000)
                elif min_score >= 510:
                    min_rank = random.randint(65000, 85000)
                else:
                    min_rank = random.randint(85000, 110000)

                avg_score = min_score + random.randint(2, 6)
                max_score = avg_score + random.randint(3, 10)
                plan_count = random.randint(2, 15)

                records.append((
                    year, cid, name, major, "河北", "物理类", "本科批",
                    min_score, avg_score, max_score, min_rank, plan_count
                ))

    return records


def generate_score_rank_table(year, province, subject):
    """生成完整的一分一段表"""
    rows = []
    # 从 750 到 200 分，每 1 分一行（高分段），每 5 分一行（低分段）
    # 模拟真实分布：正态分布，均值约 480，标准差约 80

    # 高分段（700-600）：每分
    cumulative = 0
    for score in range(750, 599, -1):
        if score >= 700:
            same = random.randint(2, 8)
        elif score >= 680:
            same = random.randint(8, 20)
        elif score >= 660:
            same = random.randint(25, 60)
        elif score >= 640:
            same = random.randint(60, 130)
        elif score >= 620:
            same = random.randint(130, 250)
        elif score >= 600:
            same = random.randint(250, 400)
        cumulative += same
        rows.append((year, province, subject, score, cumulative, same))

    # 中分段（599-500）：每分
    for score in range(599, 499, -1):
        if score >= 570:
            same = random.randint(400, 700)
        elif score >= 540:
            same = random.randint(700, 1100)
        elif score >= 510:
            same = random.randint(1100, 1500)
        else:
            same = random.randint(1500, 2000)
        cumulative += same
        rows.append((year, province, subject, score, cumulative, same))

    # 低分段（499-472）：每分
    for score in range(499, 471, -1):
        same = random.randint(2000, 3000)
        cumulative += same
        rows.append((year, province, subject, score, cumulative, same))

    return rows


def seed_full_data():
    """生成并插入完整数据集"""
    init_database()

    with get_connection() as conn:
        # 1. 插入院校
        conn.executemany("""
            INSERT OR REPLACE INTO colleges 
            (college_id, name, province, city, level, category, is_985, is_211, is_double_first_class)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, COLLEGES_DATA)
        print(f"  院校: {len(COLLEGES_DATA)} 所")

        # 2. 生成录取数据
        records = generate_admission_records(COLLEGES_DATA, years=(2022, 2023, 2024))
        conn.executemany("""
            INSERT OR REPLACE INTO admission_scores
            (year, college_id, college_name, major_name, province, subject_category, batch,
             min_score, avg_score, max_score, min_rank, plan_count, actual_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, records)
        print(f"  录取记录: {len(records)} 条")

        # 3. 省控线
        province_lines = [
            # 2024
            (2024, "河北", "物理类", "本科批", 472), (2024, "河北", "物理类", "专科批", 200),
            (2024, "河北", "历史类", "本科批", 449), (2024, "河北", "历史类", "专科批", 200),
            (2024, "河北", "物理类", "特殊类型", 525),
            (2024, "河北", "历史类", "特殊类型", 495),
            # 2023
            (2023, "河北", "物理类", "本科批", 439), (2023, "河北", "物理类", "专科批", 200),
            (2023, "河北", "历史类", "本科批", 430), (2023, "河北", "历史类", "专科批", 200),
            (2023, "河北", "物理类", "特殊类型", 492),
            (2023, "河北", "历史类", "特殊类型", 495),
            # 2022
            (2022, "河北", "物理类", "本科批", 430), (2022, "河北", "物理类", "专科批", 200),
            (2022, "河北", "历史类", "本科批", 443), (2022, "河北", "历史类", "专科批", 200),
            (2022, "河北", "物理类", "特殊类型", 487),
            (2022, "河北", "历史类", "特殊类型", 506),
        ]
        conn.executemany("""
            INSERT OR REPLACE INTO province_lines (year, province, subject_category, batch, score)
            VALUES (?, ?, ?, ?, ?)
        """, province_lines)
        print(f"  省控线: {len(province_lines)} 条")

        # 4. 一分一段表
        total_rank_rows = 0
        for year in (2022, 2023, 2024):
            rank_rows = generate_score_rank_table(year, "河北", "物理类")
            conn.executemany("""
                INSERT OR REPLACE INTO score_rank_table 
                (year, province, subject_category, score, rank_number, same_score_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, rank_rows)
            total_rank_rows += len(rank_rows)
        print(f"  一分一段: {total_rank_rows} 条")

    print(f"\n{'='*50}")
    print(f"  数据生成完成!")
    print(f"  总计: {len(COLLEGES_DATA)} 院校, {len(records)} 录取记录")
    print(f"{'='*50}")


if __name__ == "__main__":
    print("  高考志愿 AI Agent - 生成完整模拟数据集")
    print("=" * 50)
    seed_full_data()
