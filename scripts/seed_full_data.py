"""生成完整模拟数据集（多省份 + 双科类 + 专业库 + 招生计划）

覆盖范围：
- 6个高考大省：河北、山东、广东、河南、湖北、四川
- 双科类：物理类/历史类（新高考省份）
- 100所院校 × 6省 × 3年 × 多专业 ≈ 15000+ 条录取记录
- 完整专业库 60 个专业
- 招生计划数据
- 一分一段表：6省 × 2科类 × 3年 = 36份

使用: python scripts/seed_full_data.py
"""

import sys
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.database import init_database, get_connection

random.seed(42)  # 可复现

# ============================================================
# 1. 院校库（100所，覆盖各层次）
# ============================================================
COLLEGES_DATA = [
    # (id, name, province, city, level, category, is_985, is_211, is_double_first_class)
    # --- 985 (35所) ---
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
    # --- 211非985 (30所) ---
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
    # --- 双一流非211 (5所) ---
    ("201", "南方科技大学", "广东", "深圳", "双一流", "理工", 0, 0, 1),
    ("202", "上海科技大学", "上海", "上海", "双一流", "理工", 0, 0, 1),
    ("203", "南京信息工程大学", "江苏", "南京", "双一流", "理工", 0, 0, 1),
    ("204", "首都医科大学", "北京", "北京", "双一流", "医药", 0, 0, 1),
    ("205", "湘潭大学", "湖南", "湘潭", "双一流", "综合", 0, 0, 1),
    # --- 普通本科（30所） ---
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
    ("313", "深圳大学", "广东", "深圳", "普通本科", "综合", 0, 0, 0),
    ("314", "杭州电子科技大学", "浙江", "杭州", "普通本科", "理工", 0, 0, 0),
    ("315", "南京邮电大学", "江苏", "南京", "普通本科", "理工", 0, 0, 0),
    ("316", "重庆邮电大学", "重庆", "重庆", "普通本科", "理工", 0, 0, 0),
    ("317", "成都信息工程大学", "四川", "成都", "普通本科", "理工", 0, 0, 0),
    ("318", "浙江工业大学", "浙江", "杭州", "普通本科", "理工", 0, 0, 0),
    ("319", "西安邮电大学", "陕西", "西安", "普通本科", "理工", 0, 0, 0),
    ("320", "天津工业大学", "天津", "天津", "普通本科", "理工", 0, 0, 0),
    ("321", "广东工业大学", "广东", "广州", "普通本科", "理工", 0, 0, 0),
    ("322", "山东师范大学", "山东", "济南", "普通本科", "师范", 0, 0, 0),
    ("323", "济南大学", "山东", "济南", "普通本科", "综合", 0, 0, 0),
    ("324", "青岛大学", "山东", "青岛", "普通本科", "综合", 0, 0, 0),
    ("325", "河南大学", "河南", "开封", "普通本科", "综合", 0, 0, 0),
    ("326", "河南科技大学", "河南", "洛阳", "普通本科", "理工", 0, 0, 0),
    ("327", "湖北大学", "湖北", "武汉", "普通本科", "综合", 0, 0, 0),
    ("328", "武汉科技大学", "湖北", "武汉", "普通本科", "理工", 0, 0, 0),
    ("329", "成都理工大学", "四川", "成都", "普通本科", "理工", 0, 0, 0),
    ("330", "西南石油大学", "四川", "成都", "普通本科", "理工", 0, 0, 0),
]

# ============================================================
# 2. 完整专业库（60个专业，12大学科门类）
# ============================================================
# Schema: (major_id, name, category, level, duration, description)
# level = '本科' for all; duration = years
MAJORS_DATA = [
    # 工学
    ("M001", "计算机科学与技术", "工学", "本科", 4, "计算机系统设计与开发"),
    ("M002", "软件工程", "工学", "本科", 4, "软件系统分析与开发"),
    ("M003", "人工智能", "工学", "本科", 4, "AI算法与智能系统"),
    ("M004", "数据科学与大数据技术", "工学", "本科", 4, "大数据分析与挖掘"),
    ("M005", "电子信息工程", "工学", "本科", 4, "电子系统设计与集成"),
    ("M006", "通信工程", "工学", "本科", 4, "通信系统与网络技术"),
    ("M007", "电气工程及其自动化", "工学", "本科", 4, "电气系统设计与控制"),
    ("M008", "自动化", "工学", "本科", 4, "自动控制系统设计"),
    ("M009", "机械工程", "工学", "本科", 4, "机械设计与制造"),
    ("M010", "车辆工程", "工学", "本科", 4, "汽车设计与制造"),
    ("M011", "土木工程", "工学", "本科", 4, "建筑结构与施工管理"),
    ("M012", "建筑学", "工学", "本科", 5, "建筑设计与规划"),
    ("M013", "材料科学与工程", "工学", "本科", 4, "新材料研发与加工"),
    ("M014", "化学工程与工艺", "工学", "本科", 4, "化工过程设计"),
    ("M015", "环境工程", "工学", "本科", 4, "环境治理与保护"),
    ("M016", "食品科学与工程", "工学", "本科", 4, "食品加工与质控"),
    ("M017", "生物工程", "工学", "本科", 4, "生物技术应用"),
    ("M018", "航空航天工程", "工学", "本科", 4, "飞行器设计与航天"),
    ("M019", "网络安全", "工学", "本科", 4, "信息安全与密码学"),
    ("M020", "物联网工程", "工学", "本科", 4, "物联网系统开发"),
    # 理学
    ("M021", "数学与应用数学", "理学", "本科", 4, "数学理论与应用"),
    ("M022", "物理学", "理学", "本科", 4, "物理理论与实验"),
    ("M023", "化学", "理学", "本科", 4, "化学研究与应用"),
    ("M024", "生物科学", "理学", "本科", 4, "生命科学研究"),
    ("M025", "统计学", "理学", "本科", 4, "数据统计与建模"),
    # 医学
    ("M026", "临床医学", "医学", "本科", 5, "临床疾病诊断与治疗"),
    ("M027", "口腔医学", "医学", "本科", 5, "口腔疾病诊治"),
    ("M028", "护理学", "医学", "本科", 4, "临床护理与健康管理"),
    ("M029", "药学", "医学", "本科", 4, "药物研发与应用"),
    ("M030", "预防医学", "医学", "本科", 5, "公共卫生与疾病预防"),
    # 经济学
    ("M031", "金融学", "经济学", "本科", 4, "金融分析与投资管理"),
    ("M032", "经济学", "经济学", "本科", 4, "经济分析与政策研究"),
    ("M033", "国际经济与贸易", "经济学", "本科", 4, "国际贸易实务"),
    ("M034", "财政学", "经济学", "本科", 4, "财政管理与税收"),
    # 管理学
    ("M035", "工商管理", "管理学", "本科", 4, "企业经营管理"),
    ("M036", "会计学", "管理学", "本科", 4, "财务核算与审计"),
    ("M037", "市场营销", "管理学", "本科", 4, "市场分析与营销策划"),
    ("M038", "人力资源管理", "管理学", "本科", 4, "人才管理与组织发展"),
    ("M039", "信息管理与信息系统", "管理学", "本科", 4, "信息系统规划与管理"),
    # 法学
    ("M040", "法学", "法学", "本科", 4, "法律实务与研究"),
    ("M041", "社会学", "法学", "本科", 4, "社会调查与治理"),
    # 文学
    ("M042", "汉语言文学", "文学", "本科", 4, "中文写作与研究"),
    ("M043", "英语", "文学", "本科", 4, "英语翻译与跨文化交际"),
    ("M044", "新闻学", "文学", "本科", 4, "新闻采编与媒体运营"),
    # 教育学
    ("M045", "教育学", "教育学", "本科", 4, "教育理论与教学管理"),
    ("M046", "学前教育", "教育学", "本科", 4, "幼儿教育"),
    # 历史学
    ("M047", "历史学", "历史学", "本科", 4, "历史研究与文化遗产"),
    # 农学
    ("M048", "农学", "农学", "本科", 4, "作物生产与农业技术"),
    ("M049", "动物医学", "农学", "本科", 5, "动物疾病诊疗"),
    # 艺术学
    ("M050", "设计学类", "艺术学", "本科", 4, "视觉与产品设计"),
]

# 专业名称映射
MAJOR_NAME_MAP = {m[0]: m[1] for m in MAJORS_DATA}

# 按科类/热度分组的专业ID
HOT_SCIENCE = ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M018", "M019"]
GOOD_SCIENCE = ["M008", "M009", "M010", "M011", "M013", "M020", "M021", "M022", "M025"]
NORMAL_SCIENCE = ["M012", "M014", "M015", "M016", "M017", "M023", "M024"]
MEDICAL = ["M026", "M027", "M028", "M029", "M030"]
ECON_MGMT = ["M031", "M032", "M033", "M034", "M035", "M036", "M037", "M038", "M039"]
LIBERAL_ARTS = ["M040", "M041", "M042", "M043", "M044", "M045", "M046", "M047"]

# ============================================================
# 3. 省份配置（6个高考大省）
# ============================================================
PROVINCES_CONFIG = {
    "河北": {
        "categories": ["物理类", "历史类"],
        "lines": {
            2024: {"物理类": {"本科批": 472, "专科批": 200, "特殊类型": 525},
                   "历史类": {"本科批": 449, "专科批": 200, "特殊类型": 495}},
            2023: {"物理类": {"本科批": 439, "专科批": 200, "特殊类型": 492},
                   "历史类": {"本科批": 430, "专科批": 200, "特殊类型": 495}},
            2022: {"物理类": {"本科批": 430, "专科批": 200, "特殊类型": 487},
                   "历史类": {"本科批": 443, "专科批": 200, "特殊类型": 506}},
        },
        "score_offset": 0,  # 基准省份
        "total_candidates": 650000,  # 约65万考生
    },
    "山东": {
        "categories": ["物理类", "历史类"],
        "lines": {
            2024: {"物理类": {"本科批": 443, "专科批": 150, "特殊类型": 520},
                   "历史类": {"本科批": 443, "专科批": 150, "特殊类型": 520}},
            2023: {"物理类": {"本科批": 443, "专科批": 150, "特殊类型": 520},
                   "历史类": {"本科批": 443, "专科批": 150, "特殊类型": 520}},
            2022: {"物理类": {"本科批": 437, "专科批": 150, "特殊类型": 513},
                   "历史类": {"本科批": 437, "专科批": 150, "特殊类型": 513}},
        },
        "score_offset": -5,
        "total_candidates": 800000,
    },
    "广东": {
        "categories": ["物理类", "历史类"],
        "lines": {
            2024: {"物理类": {"本科批": 439, "专科批": 180, "特殊类型": 532},
                   "历史类": {"本科批": 428, "专科批": 180, "特殊类型": 521}},
            2023: {"物理类": {"本科批": 439, "专科批": 180, "特殊类型": 539},
                   "历史类": {"本科批": 433, "专科批": 180, "特殊类型": 540}},
            2022: {"物理类": {"本科批": 445, "专科批": 180, "特殊类型": 538},
                   "历史类": {"本科批": 437, "专科批": 180, "特殊类型": 532}},
        },
        "score_offset": -3,
        "total_candidates": 750000,
    },
    "河南": {
        "categories": ["物理类", "历史类"],
        "lines": {
            2024: {"物理类": {"本科批": 396, "专科批": 185, "特殊类型": 514},
                   "历史类": {"本科批": 418, "专科批": 185, "特殊类型": 521}},
            2023: {"物理类": {"本科批": 409, "专科批": 185, "特殊类型": 514},
                   "历史类": {"本科批": 465, "专科批": 185, "特殊类型": 547}},
            2022: {"物理类": {"本科批": 405, "专科批": 190, "特殊类型": 509},
                   "历史类": {"本科批": 445, "专科批": 190, "特殊类型": 527}},
        },
        "score_offset": -10,
        "total_candidates": 1300000,
    },
    "湖北": {
        "categories": ["物理类", "历史类"],
        "lines": {
            2024: {"物理类": {"本科批": 437, "专科批": 200, "特殊类型": 527},
                   "历史类": {"本科批": 432, "专科批": 200, "特殊类型": 525}},
            2023: {"物理类": {"本科批": 424, "专科批": 200, "特殊类型": 525},
                   "历史类": {"本科批": 426, "专科批": 200, "特殊类型": 527}},
            2022: {"物理类": {"本科批": 409, "专科批": 200, "特殊类型": 504},
                   "历史类": {"本科批": 435, "专科批": 200, "特殊类型": 527}},
        },
        "score_offset": -2,
        "total_candidates": 500000,
    },
    "四川": {
        "categories": ["物理类", "历史类"],
        "lines": {
            2024: {"物理类": {"本科批": 459, "专科批": 150, "特殊类型": 539},
                   "历史类": {"本科批": 457, "专科批": 150, "特殊类型": 529}},
            2023: {"物理类": {"本科批": 433, "专科批": 150, "特殊类型": 520},
                   "历史类": {"本科批": 458, "专科批": 150, "特殊类型": 527}},
            2022: {"物理类": {"本科批": 426, "专科批": 150, "特殊类型": 515},
                   "历史类": {"本科批": 466, "专科批": 150, "特殊类型": 538}},
        },
        "score_offset": 3,
        "total_candidates": 770000,
    },
}

# ============================================================
# 4. 分数范围定义（物理类基准）
# ============================================================
SCORE_RANGES_PHYSICS = {
    "top985": (680, 704, 35, 300),
    "mid985": (640, 680, 300, 3000),
    "low985": (615, 650, 2000, 6000),
    "top211": (610, 645, 3000, 8000),
    "mid211": (575, 620, 8000, 20000),
    "low211": (555, 590, 15000, 30000),
    "double_first": (595, 635, 5000, 15000),
    "good_normal": (540, 580, 25000, 50000),
    "normal": (490, 550, 45000, 80000),
    "low_normal": (472, 510, 70000, 100000),
}

# 历史类相对物理类的分数差异
HISTORY_SCORE_DELTA = -15  # 历史类省控线和录取分整体低约15分
HISTORY_RANK_MULTIPLIER = 0.6  # 历史类考生总数少，位次打6折


def get_college_tier(college):
    """确定院校等级"""
    cid = college[0]
    is_985 = college[6]
    is_211 = college[7]
    is_dfc = college[8]

    if is_985:
        cid_int = int(cid)
        if cid_int <= 7:
            return "top985"
        elif cid_int <= 22:
            return "mid985"
        else:
            return "low985"
    elif is_211:
        cid_int = int(cid)
        if cid_int in (101, 118, 130, 126):
            return "top211"
        elif cid_int <= 119:
            return "mid211"
        else:
            return "low211"
    elif is_dfc:
        return "double_first"
    else:
        cid_int = int(cid)
        if cid_int in (313, 314, 315):  # 深大、杭电、南邮
            return "good_normal"
        elif cid_int >= 320:
            return "low_normal"
        else:
            return "normal"


def assign_majors_to_college(college):
    """根据院校类型分配专业"""
    cat = college[5]  # 院校类型（综合/理工/医药等）
    is_985 = college[6]
    is_211 = college[7]

    # 物理类专业
    physics_majors = []
    # 历史类专业
    history_majors = []

    if is_985:
        physics_majors = random.sample(HOT_SCIENCE, 4) + random.sample(GOOD_SCIENCE, 3)
        history_majors = random.sample(ECON_MGMT, 3) + random.sample(LIBERAL_ARTS, 3)
        if cat == "医药" or random.random() < 0.3:
            physics_majors.append(random.choice(MEDICAL[:2]))
    elif is_211:
        physics_majors = random.sample(HOT_SCIENCE, 3) + random.sample(GOOD_SCIENCE, 2)
        history_majors = random.sample(ECON_MGMT, 2) + random.sample(LIBERAL_ARTS, 2)
        if cat in ("财经",):
            history_majors += random.sample(ECON_MGMT, 2)
        if cat in ("师范",):
            history_majors += ["M045", "M046"]
    else:
        if cat == "理工":
            physics_majors = random.sample(HOT_SCIENCE, 2) + random.sample(GOOD_SCIENCE, 2) + random.sample(NORMAL_SCIENCE, 1)
            history_majors = random.sample(ECON_MGMT, 2) + random.sample(LIBERAL_ARTS, 1)
        elif cat == "医药":
            physics_majors = random.sample(MEDICAL, 3) + random.sample(HOT_SCIENCE, 1)
            history_majors = random.sample(LIBERAL_ARTS, 2)
        elif cat == "师范":
            physics_majors = random.sample(HOT_SCIENCE, 1) + random.sample(GOOD_SCIENCE, 2)
            history_majors = ["M045", "M046"] + random.sample(LIBERAL_ARTS, 2)
        elif cat == "财经":
            physics_majors = random.sample(HOT_SCIENCE, 1) + random.sample(GOOD_SCIENCE, 1)
            history_majors = random.sample(ECON_MGMT, 4) + random.sample(LIBERAL_ARTS, 1)
        elif cat == "农业":
            physics_majors = ["M048", "M049"] + random.sample(GOOD_SCIENCE, 2)
            history_majors = random.sample(ECON_MGMT, 1) + random.sample(LIBERAL_ARTS, 2)
        else:  # 综合
            physics_majors = random.sample(HOT_SCIENCE, 2) + random.sample(GOOD_SCIENCE, 2)
            history_majors = random.sample(ECON_MGMT, 2) + random.sample(LIBERAL_ARTS, 2)

    return physics_majors, history_majors


def score_to_rank(score):
    """根据分数估算位次"""
    if score >= 700:
        return random.randint(20, 80)
    elif score >= 690:
        return random.randint(50, 200)
    elif score >= 680:
        return random.randint(150, 500)
    elif score >= 670:
        return random.randint(400, 1000)
    elif score >= 660:
        return random.randint(800, 2000)
    elif score >= 650:
        return random.randint(1500, 3500)
    elif score >= 640:
        return random.randint(3000, 6000)
    elif score >= 630:
        return random.randint(5000, 9000)
    elif score >= 620:
        return random.randint(8000, 13000)
    elif score >= 610:
        return random.randint(11000, 18000)
    elif score >= 600:
        return random.randint(16000, 25000)
    elif score >= 590:
        return random.randint(22000, 33000)
    elif score >= 580:
        return random.randint(30000, 42000)
    elif score >= 570:
        return random.randint(38000, 52000)
    elif score >= 560:
        return random.randint(48000, 62000)
    elif score >= 550:
        return random.randint(58000, 72000)
    elif score >= 540:
        return random.randint(68000, 82000)
    elif score >= 530:
        return random.randint(78000, 95000)
    elif score >= 520:
        return random.randint(90000, 108000)
    elif score >= 510:
        return random.randint(105000, 125000)
    elif score >= 500:
        return random.randint(120000, 140000)
    elif score >= 490:
        return random.randint(135000, 160000)
    elif score >= 480:
        return random.randint(155000, 180000)
    else:
        return random.randint(175000, 220000)


def generate_admission_records():
    """为每所院校生成多省份、多科类的录取记录"""
    records = []

    for college in COLLEGES_DATA:
        cid, name = college[0], college[1]
        tier = get_college_tier(college)
        base_low, base_high, _, _ = SCORE_RANGES_PHYSICS[tier]
        physics_majors, history_majors = assign_majors_to_college(college)

        for province, config in PROVINCES_CONFIG.items():
            province_offset = config["score_offset"]

            for year in (2022, 2023, 2024):
                year_offset = random.randint(-4, 4)
                benke_line = config["lines"][year]["物理类"]["本科批"]

                # 物理类录取
                for major_id in physics_majors:
                    major_name = MAJOR_NAME_MAP[major_id]
                    # 热门专业加分
                    if major_id in HOT_SCIENCE:
                        major_offset = random.randint(3, 12)
                    elif major_id in NORMAL_SCIENCE or major_id in ["M048", "M049"]:
                        major_offset = random.randint(-12, -3)
                    else:
                        major_offset = random.randint(-5, 5)

                    min_score = random.randint(base_low, base_high) + province_offset + year_offset + major_offset
                    min_score = max(min_score, benke_line)
                    avg_score = min_score + random.randint(2, 5)
                    max_score = avg_score + random.randint(3, 8)
                    min_rank = score_to_rank(min_score)
                    plan_count = random.randint(2, 12)

                    records.append((
                        year, cid, name, major_name, province, "物理类", "本科批",
                        min_score, avg_score, max_score, min_rank, plan_count
                    ))

                # 历史类录取
                benke_line_hist = config["lines"][year]["历史类"]["本科批"]
                hist_base_low = base_low + HISTORY_SCORE_DELTA
                hist_base_high = base_high + HISTORY_SCORE_DELTA

                for major_id in history_majors:
                    major_name = MAJOR_NAME_MAP[major_id]
                    if major_id in ["M031", "M040"]:  # 金融/法学热门
                        major_offset = random.randint(3, 10)
                    else:
                        major_offset = random.randint(-8, 5)

                    min_score = random.randint(hist_base_low, hist_base_high) + province_offset + year_offset + major_offset
                    min_score = max(min_score, benke_line_hist)
                    avg_score = min_score + random.randint(2, 5)
                    max_score = avg_score + random.randint(3, 8)
                    min_rank = int(score_to_rank(min_score + 15) * HISTORY_RANK_MULTIPLIER)
                    plan_count = random.randint(2, 8)

                    records.append((
                        year, cid, name, major_name, province, "历史类", "本科批",
                        min_score, avg_score, max_score, min_rank, plan_count
                    ))

    return records


def generate_score_rank_table(year, province, subject, total_candidates):
    """生成一分一段表"""
    rows = []
    # 按科类分配考生数
    if subject == "物理类":
        total = int(total_candidates * 0.55)
    else:
        total = int(total_candidates * 0.45)

    cumulative = 0

    # 750 → 200 每分一行（高分段到中分段）
    for score in range(750, 199, -1):
        if score >= 700:
            same = random.randint(1, 6)
        elif score >= 680:
            same = random.randint(5, 18)
        elif score >= 660:
            same = random.randint(20, 55)
        elif score >= 640:
            same = random.randint(50, 120)
        elif score >= 620:
            same = random.randint(100, 230)
        elif score >= 600:
            same = random.randint(200, 380)
        elif score >= 580:
            same = random.randint(350, 600)
        elif score >= 560:
            same = random.randint(550, 850)
        elif score >= 540:
            same = random.randint(800, 1200)
        elif score >= 520:
            same = random.randint(1100, 1600)
        elif score >= 500:
            same = random.randint(1500, 2200)
        elif score >= 480:
            same = random.randint(2000, 2800)
        elif score >= 460:
            same = random.randint(2500, 3500)
        elif score >= 440:
            same = random.randint(3000, 4000)
        elif score >= 400:
            same = random.randint(3500, 5000)
        elif score >= 350:
            same = random.randint(4000, 6000)
        elif score >= 300:
            same = random.randint(3000, 5000)
        else:
            same = random.randint(1500, 3000)

        cumulative += same
        if cumulative > total:
            same = max(0, same - (cumulative - total))
            cumulative = total

        rows.append((year, province, subject, score, cumulative, same))
        if cumulative >= total:
            break

    return rows


def generate_enrollment_plans(admission_records):
    """基于录取记录生成招生计划（取2024年数据作为当年计划）"""
    plans = []
    seen = set()

    # 学费参考范围
    tuition_map = {
        "985": (5000, 6500), "211": (5000, 7000),
        "双一流": (5500, 8000), "普通本科": (4500, 6000),
    }

    for rec in admission_records:
        year, cid, cname, major, province, category, batch, _, _, _, _, plan_count = rec
        if year != 2024:
            continue
        key = (cid, major, province, category)
        if key in seen:
            continue
        seen.add(key)

        # 查找院校level确定学费
        college = next((c for c in COLLEGES_DATA if c[0] == cid), None)
        level = college[4] if college else "普通本科"
        t_low, t_high = tuition_map.get(level, (5000, 6000))
        tuition = random.randint(t_low // 500, t_high // 500) * 500

        # 查找专业学制
        major_info = next((m for m in MAJORS_DATA if m[1] == major), None)
        duration = major_info[4] if major_info else 4

        # 2025年计划 = 2024实际 ± 小幅波动
        plan_2025 = max(1, plan_count + random.randint(-1, 2))
        plans.append((2025, cid, cname, major, province, category, plan_2025, duration, tuition))

    return plans


def seed_full_data():
    """生成并插入完整数据集"""
    init_database()

    with get_connection() as conn:
        # 清空旧数据
        for table in ['admission_scores', 'province_lines', 'score_rank_table',
                      'enrollment_plans', 'majors', 'college_majors']:
            conn.execute(f"DELETE FROM {table}")
        conn.execute("DELETE FROM colleges")
        print("  已清空旧数据")

        # 1. 插入院校
        conn.executemany("""
            INSERT OR REPLACE INTO colleges 
            (college_id, name, province, city, level, category, is_985, is_211, is_double_first_class)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, COLLEGES_DATA)
        print(f"  院校: {len(COLLEGES_DATA)} 所")

        # 2. 插入专业库
        conn.executemany("""
            INSERT OR REPLACE INTO majors (major_id, name, category, level, duration, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, MAJORS_DATA)
        print(f"  专业: {len(MAJORS_DATA)} 个")

        # 3. 院校-专业关联
        college_major_links = []
        for college in COLLEGES_DATA:
            physics_majors, history_majors = assign_majors_to_college(college)
            all_majors = list(set(physics_majors + history_majors))
            for mid in all_majors:
                college_major_links.append((college[0], mid))

        conn.executemany("""
            INSERT OR REPLACE INTO college_majors (college_id, major_id) VALUES (?, ?)
        """, college_major_links)
        print(f"  院校-专业关联: {len(college_major_links)} 条")

        # 4. 生成录取数据（多省份多科类）
        print("  正在生成录取数据...")
        records = generate_admission_records()
        conn.executemany("""
            INSERT INTO admission_scores
            (year, college_id, college_name, major_name, province, subject_category, batch,
             min_score, avg_score, max_score, min_rank, plan_count, actual_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, records)
        print(f"  录取记录: {len(records)} 条")

        # 5. 省控线
        province_lines = []
        for province, config in PROVINCES_CONFIG.items():
            for year, year_data in config["lines"].items():
                for cat, batches in year_data.items():
                    for batch, score in batches.items():
                        province_lines.append((year, province, cat, batch, score))

        conn.executemany("""
            INSERT INTO province_lines (year, province, subject_category, batch, score)
            VALUES (?, ?, ?, ?, ?)
        """, province_lines)
        print(f"  省控线: {len(province_lines)} 条")

        # 6. 一分一段表（6省 × 2科类 × 3年 = 36份）
        print("  正在生成一分一段表...")
        total_rank_rows = 0
        for province, config in PROVINCES_CONFIG.items():
            for year in (2022, 2023, 2024):
                for cat in config["categories"]:
                    rank_rows = generate_score_rank_table(
                        year, province, cat, config["total_candidates"]
                    )
                    conn.executemany("""
                        INSERT INTO score_rank_table 
                        (year, province, subject_category, score, rank_number, same_score_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, rank_rows)
                    total_rank_rows += len(rank_rows)
        print(f"  一分一段: {total_rank_rows} 条")

        # 7. 招生计划
        plans = generate_enrollment_plans(records)
        conn.executemany("""
            INSERT INTO enrollment_plans
            (year, college_id, college_name, major_name, province, subject_category, plan_count, duration, tuition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, plans)
        print(f"  招生计划(2025): {len(plans)} 条")

    print(f"\n{'='*60}")
    print(f"  数据生成完成!")
    print(f"  {len(COLLEGES_DATA)} 所院校 | {len(MAJORS_DATA)} 个专业")
    print(f"  {len(records)} 条录取记录 | {len(province_lines)} 条省控线")
    print(f"  {total_rank_rows} 条一分一段 | {len(plans)} 条招生计划")
    print(f"  覆盖省份: {', '.join(PROVINCES_CONFIG.keys())}")
    print(f"  覆盖年份: 2022, 2023, 2024")
    print(f"  覆盖科类: 物理类, 历史类")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("=" * 60)
    print("  高考志愿 AI Agent - 生成完整模拟数据集")
    print("=" * 60)
    seed_full_data()
