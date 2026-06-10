"""生成全国完整模拟数据集 v2

覆盖范围（对标教育部2024年数据）：
- 全国31个省/自治区/直辖市
- 本科院校约1308所 + 高职专科约1560所 = 约2868所
- 2022-2025年4年数据
- 物理类/历史类双科类
- 56个本科专业 + 20个专科专业 = 76个

控制数据量策略（目标DB < 95MB）：
- 985/211: 全国招生，每省每年2-3个专业
- 双一流/普本: 5-12个省招生，每省每年2个专业
- 专科: 本省+1-3个邻省，每省每年2个专业
- 一分一段表: 每3分一档

使用: python scripts/seed_full_data.py
"""

import sys
import random
import math
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.database import init_database

random.seed(42)

# ============================================================
# 1. 全国31省份配置
# ============================================================
PROVINCES_CONFIG = {
    # 省份: (本科线基准(物理), 本科线基准(历史), 专科线, 考生人数万)
    "北京": (434, 434, 150, 7),
    "天津": (463, 463, 150, 6),
    "河北": (472, 449, 200, 65),
    "山西": (434, 440, 150, 33),
    "内蒙古": (360, 392, 160, 18),
    "辽宁": (360, 404, 150, 22),
    "吉林": (343, 369, 150, 12),
    "黑龙江": (353, 365, 150, 19),
    "上海": (405, 405, 100, 5),
    "江苏": (448, 474, 220, 44),
    "浙江": (488, 488, 280, 36),
    "安徽": (462, 453, 200, 65),
    "福建": (449, 453, 220, 23),
    "江西": (448, 472, 200, 54),
    "山东": (443, 443, 150, 80),
    "河南": (396, 418, 185, 130),
    "湖北": (437, 432, 200, 50),
    "湖南": (422, 428, 200, 65),
    "广东": (439, 428, 180, 75),
    "广西": (371, 400, 180, 46),
    "海南": (483, 483, 250, 7),
    "重庆": (427, 428, 180, 33),
    "四川": (459, 457, 150, 77),
    "贵州": (380, 442, 180, 48),
    "云南": (396, 450, 200, 39),
    "西藏": (300, 320, 200, 3),
    "陕西": (443, 400, 150, 33),
    "甘肃": (370, 418, 160, 24),
    "青海": (330, 365, 150, 5),
    "宁夏": (354, 421, 150, 7),
    "新疆": (360, 380, 140, 22),
}

ALL_PROVINCES = list(PROVINCES_CONFIG.keys())

# 邻省关系（专科招生用）
NEIGHBOR_PROVINCES = {
    "北京": ["天津", "河北"],
    "天津": ["北京", "河北"],
    "河北": ["北京", "天津", "山东", "河南", "山西"],
    "山西": ["河北", "河南", "陕西", "内蒙古"],
    "内蒙古": ["山西", "河北", "黑龙江", "吉林", "辽宁"],
    "辽宁": ["吉林", "内蒙古", "河北"],
    "吉林": ["辽宁", "黑龙江", "内蒙古"],
    "黑龙江": ["吉林", "内蒙古"],
    "上海": ["江苏", "浙江"],
    "江苏": ["上海", "浙江", "安徽", "山东"],
    "浙江": ["上海", "江苏", "安徽", "福建", "江西"],
    "安徽": ["江苏", "浙江", "河南", "湖北", "江西"],
    "福建": ["浙江", "江西", "广东"],
    "江西": ["浙江", "福建", "广东", "湖南", "湖北", "安徽"],
    "山东": ["河北", "河南", "安徽", "江苏"],
    "河南": ["河北", "山东", "安徽", "湖北", "山西", "陕西"],
    "湖北": ["河南", "安徽", "江西", "湖南", "重庆", "陕西"],
    "湖南": ["湖北", "江西", "广东", "广西", "贵州", "重庆"],
    "广东": ["湖南", "江西", "福建", "广西", "海南"],
    "广西": ["广东", "湖南", "贵州", "云南"],
    "海南": ["广东"],
    "重庆": ["四川", "贵州", "湖北", "湖南", "陕西"],
    "四川": ["重庆", "贵州", "云南", "西藏", "青海", "甘肃", "陕西"],
    "贵州": ["四川", "重庆", "湖南", "云南", "广西"],
    "云南": ["四川", "贵州", "广西", "西藏"],
    "西藏": ["四川", "云南", "青海", "新疆"],
    "陕西": ["山西", "河南", "湖北", "重庆", "四川", "甘肃", "宁夏"],
    "甘肃": ["陕西", "四川", "青海", "宁夏", "新疆", "内蒙古"],
    "青海": ["甘肃", "四川", "西藏", "新疆"],
    "宁夏": ["陕西", "甘肃", "内蒙古"],
    "新疆": ["甘肃", "青海", "西藏"],
}


def get_province_lines(province, base_phys, base_hist, base_spec):
    """生成2022-2025年省控线"""
    lines = []
    for year in (2022, 2023, 2024, 2025):
        offset = random.randint(-15, 15)
        phys_line = base_phys + offset
        hist_line = base_hist + offset + random.randint(-5, 5)
        spec_line = base_spec
        special_phys = phys_line + random.randint(50, 80)
        special_hist = hist_line + random.randint(50, 75)
        lines.extend([
            (year, province, "物理类", "本科批", phys_line),
            (year, province, "物理类", "专科批", spec_line),
            (year, province, "物理类", "特殊类型", special_phys),
            (year, province, "历史类", "本科批", hist_line),
            (year, province, "历史类", "专科批", spec_line),
            (year, province, "历史类", "特殊类型", special_hist),
        ])
    return lines


# ============================================================
# 2. 院校库生成 (目标: 本科~1308 + 专科~1560 = ~2868)
# ============================================================

def generate_colleges():
    """程序化生成全国院校库，对标教育部2024年数据"""
    colleges = []
    cid = 1

    # =============================================
    # A. 985院校 (39所) - 实名
    # =============================================
    c985_list = [
        ("清华大学", "北京", "北京", "综合"),
        ("北京大学", "北京", "北京", "综合"),
        ("浙江大学", "浙江", "杭州", "综合"),
        ("上海交通大学", "上海", "上海", "综合"),
        ("复旦大学", "上海", "上海", "综合"),
        ("南京大学", "江苏", "南京", "综合"),
        ("中国科学技术大学", "安徽", "合肥", "理工"),
        ("哈尔滨工业大学", "黑龙江", "哈尔滨", "理工"),
        ("武汉大学", "湖北", "武汉", "综合"),
        ("华中科技大学", "湖北", "武汉", "理工"),
        ("西安交通大学", "陕西", "西安", "综合"),
        ("天津大学", "天津", "天津", "理工"),
        ("北京航空航天大学", "北京", "北京", "理工"),
        ("北京理工大学", "北京", "北京", "理工"),
        ("东南大学", "江苏", "南京", "综合"),
        ("同济大学", "上海", "上海", "理工"),
        ("电子科技大学", "四川", "成都", "理工"),
        ("中山大学", "广东", "广州", "综合"),
        ("四川大学", "四川", "成都", "综合"),
        ("山东大学", "山东", "济南", "综合"),
        ("中南大学", "湖南", "长沙", "综合"),
        ("厦门大学", "福建", "厦门", "综合"),
        ("大连理工大学", "辽宁", "大连", "理工"),
        ("华南理工大学", "广东", "广州", "理工"),
        ("吉林大学", "吉林", "长春", "综合"),
        ("湖南大学", "湖南", "长沙", "综合"),
        ("重庆大学", "重庆", "重庆", "综合"),
        ("西北工业大学", "陕西", "西安", "理工"),
        ("兰州大学", "甘肃", "兰州", "综合"),
        ("东北大学", "辽宁", "沈阳", "理工"),
        ("中国人民大学", "北京", "北京", "综合"),
        ("北京师范大学", "北京", "北京", "师范"),
        ("中国海洋大学", "山东", "青岛", "综合"),
        ("中国农业大学", "北京", "北京", "农林"),
        ("中央民族大学", "北京", "北京", "民族"),
        ("国防科技大学", "湖南", "长沙", "理工"),
        ("西北农林科技大学", "陕西", "杨凌", "农林"),
        ("华东师范大学", "上海", "上海", "师范"),
        ("南开大学", "天津", "天津", "综合"),
    ]
    for name, prov, city, cat in c985_list:
        colleges.append((str(cid), name, prov, city, "985", cat, 1, 1, 1, "本科"))
        cid += 1

    # =============================================
    # B. 211非985 (73所)
    # =============================================
    c211_list = [
        ("北京邮电大学", "北京", "北京", "理工"),
        ("北京交通大学", "北京", "北京", "理工"),
        ("北京科技大学", "北京", "北京", "理工"),
        ("北京化工大学", "北京", "北京", "理工"),
        ("北京外国语大学", "北京", "北京", "语言"),
        ("中国传媒大学", "北京", "北京", "文法"),
        ("中央财经大学", "北京", "北京", "财经"),
        ("对外经济贸易大学", "北京", "北京", "财经"),
        ("华北电力大学", "北京", "北京", "理工"),
        ("中国政法大学", "北京", "北京", "政法"),
        ("北京中医药大学", "北京", "北京", "医药"),
        ("中国地质大学(北京)", "北京", "北京", "理工"),
        ("中国矿业大学(北京)", "北京", "北京", "理工"),
        ("中国石油大学(北京)", "北京", "北京", "理工"),
        ("北京林业大学", "北京", "北京", "农林"),
        ("北京体育大学", "北京", "北京", "体育"),
        ("南京航空航天大学", "江苏", "南京", "理工"),
        ("南京理工大学", "江苏", "南京", "理工"),
        ("河海大学", "江苏", "南京", "理工"),
        ("苏州大学", "江苏", "苏州", "综合"),
        ("中国药科大学", "江苏", "南京", "医药"),
        ("江南大学", "江苏", "无锡", "综合"),
        ("南京师范大学", "江苏", "南京", "师范"),
        ("南京农业大学", "江苏", "南京", "农林"),
        ("中国矿业大学", "江苏", "徐州", "理工"),
        ("上海大学", "上海", "上海", "综合"),
        ("华东理工大学", "上海", "上海", "理工"),
        ("上海财经大学", "上海", "上海", "财经"),
        ("上海外国语大学", "上海", "上海", "语言"),
        ("东华大学", "上海", "上海", "理工"),
        ("武汉理工大学", "湖北", "武汉", "理工"),
        ("华中师范大学", "湖北", "武汉", "师范"),
        ("华中农业大学", "湖北", "武汉", "农林"),
        ("中南财经政法大学", "湖北", "武汉", "财经"),
        ("中国地质大学(武汉)", "湖北", "武汉", "理工"),
        ("西南大学", "重庆", "重庆", "综合"),
        ("西南交通大学", "四川", "成都", "理工"),
        ("西南财经大学", "四川", "成都", "财经"),
        ("四川农业大学", "四川", "雅安", "农林"),
        ("西安电子科技大学", "陕西", "西安", "理工"),
        ("长安大学", "陕西", "西安", "理工"),
        ("陕西师范大学", "陕西", "西安", "师范"),
        ("西北大学", "陕西", "西安", "综合"),
        ("暨南大学", "广东", "广州", "综合"),
        ("华南师范大学", "广东", "广州", "师范"),
        ("郑州大学", "河南", "郑州", "综合"),
        ("河北工业大学", "天津", "天津", "理工"),
        ("太原理工大学", "山西", "太原", "理工"),
        ("大连海事大学", "辽宁", "大连", "理工"),
        ("辽宁大学", "辽宁", "沈阳", "综合"),
        ("东北师范大学", "吉林", "长春", "师范"),
        ("延边大学", "吉林", "延吉", "综合"),
        ("哈尔滨工程大学", "黑龙江", "哈尔滨", "理工"),
        ("东北农业大学", "黑龙江", "哈尔滨", "农林"),
        ("东北林业大学", "黑龙江", "哈尔滨", "农林"),
        ("合肥工业大学", "安徽", "合肥", "理工"),
        ("安徽大学", "安徽", "合肥", "综合"),
        ("福州大学", "福建", "福州", "理工"),
        ("南昌大学", "江西", "南昌", "综合"),
        ("湖南师范大学", "湖南", "长沙", "师范"),
        ("广西大学", "广西", "南宁", "综合"),
        ("海南大学", "海南", "海口", "综合"),
        ("贵州大学", "贵州", "贵阳", "综合"),
        ("云南大学", "云南", "昆明", "综合"),
        ("西藏大学", "西藏", "拉萨", "综合"),
        ("青海大学", "青海", "西宁", "综合"),
        ("宁夏大学", "宁夏", "银川", "综合"),
        ("新疆大学", "新疆", "乌鲁木齐", "综合"),
        ("石河子大学", "新疆", "石河子", "综合"),
        ("内蒙古大学", "内蒙古", "呼和浩特", "综合"),
        ("中国石油大学(华东)", "山东", "青岛", "理工"),
        ("南京信息工程大学", "江苏", "南京", "理工"),
        ("第二军医大学", "上海", "上海", "医药"),
    ]
    for name, prov, city, cat in c211_list:
        colleges.append((str(cid), name, prov, city, "211", cat, 0, 1, 1, "本科"))
        cid += 1

    # =============================================
    # C. 双一流非211 (约35所)
    # =============================================
    syl_list = [
        ("南方科技大学", "广东", "深圳", "理工"),
        ("上海科技大学", "上海", "上海", "理工"),
        ("首都医科大学", "北京", "北京", "医药"),
        ("湘潭大学", "湖南", "湘潭", "综合"),
        ("成都理工大学", "四川", "成都", "理工"),
        ("河南大学", "河南", "开封", "综合"),
        ("广州医科大学", "广东", "广州", "医药"),
        ("南京医科大学", "江苏", "南京", "医药"),
        ("华南农业大学", "广东", "广州", "农林"),
        ("山西大学", "山西", "太原", "综合"),
        ("南京林业大学", "江苏", "南京", "农林"),
        ("上海海洋大学", "上海", "上海", "农林"),
        ("中国美术学院", "浙江", "杭州", "艺术"),
        ("天津工业大学", "天津", "天津", "理工"),
        ("天津中医药大学", "天津", "天津", "医药"),
        ("南京邮电大学", "江苏", "南京", "理工"),
        ("浙江工业大学", "浙江", "杭州", "理工"),
        ("河北工业大学", "河北", "天津", "理工"),
        ("武汉科技大学", "湖北", "武汉", "理工"),
        ("南华大学", "湖南", "衡阳", "综合"),
    ]
    for name, prov, city, cat in syl_list:
        colleges.append((str(cid), name, prov, city, "双一流", cat, 0, 0, 1, "本科"))
        cid += 1

    # =============================================
    # D. 普通本科 (目标: ~1300 - 39 - 73 - 20 ≈ 1168所)
    # =============================================
    # 各省本科数量分配（参考真实分布）
    province_benke_target = {
        "北京": 67, "天津": 31, "河北": 61, "山西": 36,
        "内蒙古": 22, "辽宁": 63, "吉林": 37, "黑龙江": 39,
        "上海": 40, "江苏": 78, "浙江": 60, "安徽": 47,
        "福建": 39, "江西": 45, "山东": 71, "河南": 59,
        "湖北": 68, "湖南": 53, "广东": 68, "广西": 38,
        "海南": 12, "重庆": 27, "四川": 58, "贵州": 30,
        "云南": 33, "西藏": 7, "陕西": 57, "甘肃": 22,
        "青海": 6, "宁夏": 13, "新疆": 21,
    }

    benke_suffixes = {
        "理工": ["理工大学", "工业大学", "科技大学", "工程大学", "信息工程学院",
                 "电子科技学院", "科技学院", "工程学院", "工学院", "技术学院"],
        "师范": ["师范大学", "师范学院", "教育学院"],
        "医药": ["医科大学", "中医药大学", "医学院", "药科大学"],
        "财经": ["财经大学", "经贸大学", "商学院", "金融学院", "经济学院"],
        "综合": ["大学", "学院", "文理学院"],
        "农林": ["农业大学", "林业大学", "农学院"],
        "政法": ["政法大学", "法学院"],
        "语言": ["外国语学院", "外语学院"],
        "艺术": ["美术学院", "艺术学院", "音乐学院"],
        "体育": ["体育学院"],
    }

    # 各省城市（用于多样化命名）
    province_cities = {
        "北京": ["北京"],
        "天津": ["天津"],
        "河北": ["石家庄", "保定", "唐山", "邯郸", "秦皇岛", "廊坊", "承德", "张家口"],
        "山西": ["太原", "大同", "运城", "长治", "临汾", "晋中"],
        "内蒙古": ["呼和浩特", "包头", "赤峰", "鄂尔多斯"],
        "辽宁": ["沈阳", "大连", "鞍山", "锦州", "营口", "抚顺"],
        "吉林": ["长春", "吉林", "四平", "通化"],
        "黑龙江": ["哈尔滨", "齐齐哈尔", "牡丹江", "大庆", "佳木斯"],
        "上海": ["上海"],
        "江苏": ["南京", "苏州", "无锡", "常州", "南通", "徐州", "扬州", "盐城"],
        "浙江": ["杭州", "宁波", "温州", "嘉兴", "金华", "台州", "绍兴"],
        "安徽": ["合肥", "芜湖", "蚌埠", "阜阳", "安庆", "淮南", "马鞍山"],
        "福建": ["福州", "厦门", "泉州", "漳州", "莆田", "龙岩"],
        "江西": ["南昌", "赣州", "九江", "上饶", "景德镇", "吉安"],
        "山东": ["济南", "青岛", "烟台", "潍坊", "临沂", "济宁", "淄博", "德州"],
        "河南": ["郑州", "洛阳", "开封", "新乡", "南阳", "信阳", "商丘", "许昌"],
        "湖北": ["武汉", "宜昌", "襄阳", "荆州", "黄冈", "十堰"],
        "湖南": ["长沙", "株洲", "湘潭", "衡阳", "岳阳", "常德", "邵阳"],
        "广东": ["广州", "深圳", "东莞", "佛山", "珠海", "惠州", "中山", "汕头", "湛江"],
        "广西": ["南宁", "桂林", "柳州", "梧州", "北海"],
        "海南": ["海口", "三亚"],
        "重庆": ["重庆"],
        "四川": ["成都", "绵阳", "德阳", "宜宾", "南充", "泸州", "乐山"],
        "贵州": ["贵阳", "遵义", "六盘水", "毕节"],
        "云南": ["昆明", "曲靖", "大理", "玉溪", "红河"],
        "西藏": ["拉萨"],
        "陕西": ["西安", "咸阳", "宝鸡", "渭南", "延安", "汉中"],
        "甘肃": ["兰州", "天水", "酒泉"],
        "青海": ["西宁"],
        "宁夏": ["银川"],
        "新疆": ["乌鲁木齐", "昌吉", "伊宁", "喀什"],
    }

    # 各省知名普通本科（精选100所）
    famous_normals = [
        ("深圳大学", "广东", "深圳", "综合"), ("杭州电子科技大学", "浙江", "杭州", "理工"),
        ("重庆邮电大学", "重庆", "重庆", "理工"), ("燕山大学", "河北", "秦皇岛", "理工"),
        ("河北大学", "河北", "保定", "综合"), ("广东工业大学", "广东", "广州", "理工"),
        ("山东科技大学", "山东", "青岛", "理工"), ("青岛大学", "山东", "青岛", "综合"),
        ("济南大学", "山东", "济南", "综合"), ("山东师范大学", "山东", "济南", "师范"),
        ("河南科技大学", "河南", "洛阳", "理工"), ("河南师范大学", "河南", "新乡", "师范"),
        ("湖北大学", "湖北", "武汉", "综合"), ("长沙理工大学", "湖南", "长沙", "理工"),
        ("西南石油大学", "四川", "成都", "理工"), ("成都信息工程大学", "四川", "成都", "理工"),
        ("昆明理工大学", "云南", "昆明", "理工"), ("浙江师范大学", "浙江", "金华", "师范"),
        ("浙江理工大学", "浙江", "杭州", "理工"), ("西安邮电大学", "陕西", "西安", "理工"),
        ("天津财经大学", "天津", "天津", "财经"), ("东北财经大学", "辽宁", "大连", "财经"),
        ("首都经济贸易大学", "北京", "北京", "财经"), ("北京工商大学", "北京", "北京", "财经"),
        ("上海理工大学", "上海", "上海", "理工"), ("上海师范大学", "上海", "上海", "师范"),
        ("华侨大学", "福建", "泉州", "综合"), ("集美大学", "福建", "厦门", "综合"),
        ("江西财经大学", "江西", "南昌", "财经"), ("南昌航空大学", "江西", "南昌", "理工"),
        ("桂林电子科技大学", "广西", "桂林", "理工"), ("贵州师范大学", "贵州", "贵阳", "师范"),
        ("兰州交通大学", "甘肃", "兰州", "理工"), ("兰州理工大学", "甘肃", "兰州", "理工"),
        ("石家庄铁道大学", "河北", "石家庄", "理工"), ("河北师范大学", "河北", "石家庄", "师范"),
        ("河北医科大学", "河北", "石家庄", "医药"), ("山东财经大学", "山东", "济南", "财经"),
        ("哈尔滨理工大学", "黑龙江", "哈尔滨", "理工"), ("哈尔滨医科大学", "黑龙江", "哈尔滨", "医药"),
        ("大连交通大学", "辽宁", "大连", "理工"), ("沈阳工业大学", "辽宁", "沈阳", "理工"),
        ("长春理工大学", "吉林", "长春", "理工"), ("吉林师范大学", "吉林", "四平", "师范"),
        ("安徽工业大学", "安徽", "马鞍山", "理工"), ("安徽师范大学", "安徽", "芜湖", "师范"),
        ("福建师范大学", "福建", "福州", "师范"), ("南京工业大学", "江苏", "南京", "理工"),
        ("苏州科技大学", "江苏", "苏州", "理工"), ("扬州大学", "江苏", "扬州", "综合"),
        ("常州大学", "江苏", "常州", "理工"), ("温州大学", "浙江", "温州", "综合"),
        ("宁波大学", "浙江", "宁波", "综合"), ("中国计量大学", "浙江", "杭州", "理工"),
        ("河南农业大学", "河南", "郑州", "农林"), ("河南工业大学", "河南", "郑州", "理工"),
        ("河南理工大学", "河南", "焦作", "理工"), ("郑州轻工业大学", "河南", "郑州", "理工"),
        ("湖南科技大学", "湖南", "湘潭", "理工"), ("湖南工业大学", "湖南", "株洲", "理工"),
        ("中南林业科技大学", "湖南", "长沙", "农林"), ("广东外语外贸大学", "广东", "广州", "语言"),
        ("广东财经大学", "广东", "广州", "财经"), ("广州大学", "广东", "广州", "综合"),
        ("东莞理工学院", "广东", "东莞", "理工"), ("佛山科学技术学院", "广东", "佛山", "综合"),
        ("重庆交通大学", "重庆", "重庆", "理工"), ("重庆师范大学", "重庆", "重庆", "师范"),
        ("重庆工商大学", "重庆", "重庆", "财经"), ("成都大学", "四川", "成都", "综合"),
        ("西南科技大学", "四川", "绵阳", "理工"), ("西华大学", "四川", "成都", "综合"),
        ("贵州财经大学", "贵州", "贵阳", "财经"), ("云南师范大学", "云南", "昆明", "师范"),
        ("云南财经大学", "云南", "昆明", "财经"), ("西安理工大学", "陕西", "西安", "理工"),
        ("西安建筑科技大学", "陕西", "西安", "理工"), ("西安科技大学", "陕西", "西安", "理工"),
        ("陕西科技大学", "陕西", "西安", "理工"), ("西北师范大学", "甘肃", "兰州", "师范"),
        ("北方工业大学", "北京", "北京", "理工"), ("北京建筑大学", "北京", "北京", "理工"),
        ("北京信息科技大学", "北京", "北京", "理工"), ("首都师范大学", "北京", "北京", "师范"),
        ("天津理工大学", "天津", "天津", "理工"), ("天津师范大学", "天津", "天津", "师范"),
        ("天津科技大学", "天津", "天津", "理工"), ("上海海事大学", "上海", "上海", "理工"),
        ("上海电力大学", "上海", "上海", "理工"), ("上海应用技术大学", "上海", "上海", "理工"),
    ]
    for name, prov, city, cat in famous_normals:
        colleges.append((str(cid), name, prov, city, "普通本科", cat, 0, 0, 0, "本科"))
        cid += 1

    # 按省批量生成剩余普通本科
    cat_cycle = ["理工", "综合", "理工", "师范", "医药", "财经", "综合", "理工",
                 "农林", "综合", "理工", "综合", "财经", "师范", "理工",
                 "综合", "医药", "理工", "艺术", "综合", "理工", "语言",
                 "综合", "理工", "综合", "体育", "理工", "综合"]

    for prov in ALL_PROVINCES:
        target = province_benke_target.get(prov, 20)
        existing = sum(1 for c in colleges if c[2] == prov and c[9] == "本科")
        need = max(0, target - existing)

        cities = province_cities.get(prov, [prov])

        # 用于命名多样化的前缀词
        name_prefixes = ["新", "华", "明", "达", "博", "和", "嘉", "恒", "卓", "启",
                         "东方", "南方", "中原", "北方", "西部", "远东", "华南", "华北"]

        for i in range(need):
            cat = cat_cycle[i % len(cat_cycle)]
            suffixes = benke_suffixes.get(cat, benke_suffixes["综合"])
            suffix = suffixes[i % len(suffixes)]
            city = cities[i % len(cities)]

            # 命名策略：城市名 + 后缀，或 省名 + 后缀，或加前缀词
            if i < len(cities):
                name = f"{city}{suffix}"
            elif i < len(cities) * 2:
                name = f"{city}{cat_cycle[(i+3) % len(cat_cycle)]}{suffix}" if random.random() > 0.5 else f"{prov}{suffix}"
            else:
                prefix = name_prefixes[i % len(name_prefixes)]
                name = f"{city}{prefix}{suffix}" if random.random() > 0.3 else f"{prov}{prefix}{suffix}"

            # 避免重名
            dup_counter = 0
            while any(c[1] == name for c in colleges):
                prefix2 = name_prefixes[(i + dup_counter + 7) % len(name_prefixes)]
                name = f"{city}{prefix2}{suffix}"
                dup_counter += 1
                if dup_counter > len(name_prefixes):
                    name = f"{city}{prefix2}{dup_counter}{suffix}"
                    break

            colleges.append((str(cid), name, prov, city, "普通本科", cat, 0, 0, 0, "本科"))
            cid += 1

    # =============================================
    # E. 专科院校 (目标: ~1560所)
    # =============================================
    province_zhuanke_target = {
        "北京": 25, "天津": 26, "河北": 67, "山西": 53,
        "内蒙古": 35, "辽宁": 52, "吉林": 31, "黑龙江": 42,
        "上海": 20, "江苏": 93, "浙江": 63, "安徽": 78,
        "福建": 52, "江西": 62, "山东": 86, "河南": 106,
        "湖北": 64, "湖南": 77, "广东": 97, "广西": 52,
        "海南": 15, "重庆": 45, "四川": 83, "贵州": 49,
        "云南": 55, "西藏": 7, "陕西": 42, "甘肃": 28,
        "青海": 8, "宁夏": 14, "新疆": 33,
    }

    zk_suffixes = [
        "职业技术学院", "职业学院", "高等专科学校",
        "工程职业技术学院", "信息职业技术学院",
        "交通职业技术学院", "商贸职业学院",
        "工业职业技术学院", "建筑职业技术学院",
        "旅游职业学院", "艺术职业学院",
        "卫生职业学院", "农业职业技术学院",
        "电子职业技术学院", "科技职业学院",
        "轻工职业技术学院", "化工职业技术学院",
        "铁路职业技术学院", "航空职业技术学院",
        "水利职业技术学院", "城市职业学院",
        "财贸职业学院", "民政职业技术学院",
        "文化艺术职业学院", "幼儿师范高等专科学校",
    ]

    zk_cats = ["综合", "理工", "综合", "理工", "理工",
               "理工", "财经", "理工", "理工",
               "旅游", "艺术", "医药", "农林",
               "理工", "理工", "理工", "理工",
               "理工", "理工", "理工", "综合",
               "财经", "综合", "艺术", "师范"]

    for prov in ALL_PROVINCES:
        target = province_zhuanke_target.get(prov, 20)
        cities = province_cities.get(prov, [prov])

        for i in range(target):
            suffix = zk_suffixes[i % len(zk_suffixes)]
            cat = zk_cats[i % len(zk_cats)]
            city = cities[i % len(cities)]

            if i < len(cities):
                name = f"{city}{suffix}"
            elif i < len(zk_suffixes):
                name = f"{prov}{suffix}"
            else:
                name = f"{city}{zk_suffixes[(i*3) % len(zk_suffixes)]}"

            zk_prefixes = ["新", "华", "明", "达", "博", "和", "嘉", "恒", "卓", "启",
                           "东方", "南方", "中原", "北方", "西部"]
            dup_counter = 0
            while any(c[1] == name for c in colleges):
                zk_prefix = zk_prefixes[(i + dup_counter) % len(zk_prefixes)]
                name = f"{city}{zk_prefix}{suffix}"
                dup_counter += 1
                if dup_counter > len(zk_prefixes):
                    name = f"{city}{zk_prefix}{dup_counter}{suffix}"
                    break

            colleges.append((str(cid), name, prov, city, "专科", cat, 0, 0, 0, "专科"))
            cid += 1

    return colleges


# ============================================================
# 3. 专业库（本科56 + 专科20 = 76个）
# ============================================================
MAJORS_DATA = [
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
    ("M021", "数学与应用数学", "理学", "本科", 4, "数学理论与应用"),
    ("M022", "物理学", "理学", "本科", 4, "物理理论与实验"),
    ("M023", "化学", "理学", "本科", 4, "化学研究与应用"),
    ("M024", "生物科学", "理学", "本科", 4, "生命科学研究"),
    ("M025", "统计学", "理学", "本科", 4, "数据统计与建模"),
    ("M026", "临床医学", "医学", "本科", 5, "临床疾病诊断与治疗"),
    ("M027", "口腔医学", "医学", "本科", 5, "口腔疾病诊治"),
    ("M028", "护理学", "医学", "本科", 4, "临床护理与健康管理"),
    ("M029", "药学", "医学", "本科", 4, "药物研发与应用"),
    ("M030", "预防医学", "医学", "本科", 5, "公共卫生与疾病预防"),
    ("M031", "金融学", "经济学", "本科", 4, "金融分析与投资管理"),
    ("M032", "经济学", "经济学", "本科", 4, "经济分析与政策研究"),
    ("M033", "国际经济与贸易", "经济学", "本科", 4, "国际贸易实务"),
    ("M034", "财政学", "经济学", "本科", 4, "财政管理与税收"),
    ("M035", "工商管理", "管理学", "本科", 4, "企业经营管理"),
    ("M036", "会计学", "管理学", "本科", 4, "财务核算与审计"),
    ("M037", "市场营销", "管理学", "本科", 4, "市场分析与营销策划"),
    ("M038", "人力资源管理", "管理学", "本科", 4, "人才管理与组织发展"),
    ("M039", "信息管理与信息系统", "管理学", "本科", 4, "信息系统规划与管理"),
    ("M040", "法学", "法学", "本科", 4, "法律实务与研究"),
    ("M041", "社会学", "法学", "本科", 4, "社会调查与治理"),
    ("M042", "政治学与行政学", "法学", "本科", 4, "政治分析与行政管理"),
    ("M043", "汉语言文学", "文学", "本科", 4, "中文写作与研究"),
    ("M044", "英语", "文学", "本科", 4, "英语翻译与跨文化交际"),
    ("M045", "新闻学", "文学", "本科", 4, "新闻采编与媒体运营"),
    ("M046", "广播电视学", "文学", "本科", 4, "广播电视节目制作"),
    ("M047", "教育学", "教育学", "本科", 4, "教育理论与教学管理"),
    ("M048", "学前教育", "教育学", "本科", 4, "幼儿教育"),
    ("M049", "小学教育", "教育学", "本科", 4, "小学教育教学"),
    ("M050", "历史学", "历史学", "本科", 4, "历史研究与文化遗产"),
    ("M051", "农学", "农学", "本科", 4, "作物生产与农业技术"),
    ("M052", "动物医学", "农学", "本科", 5, "动物疾病诊疗"),
    ("M053", "园林", "农学", "本科", 4, "园林规划与景观设计"),
    ("M054", "设计学类", "艺术学", "本科", 4, "视觉与产品设计"),
    ("M055", "音乐学", "艺术学", "本科", 4, "音乐表演与教育"),
    ("M056", "哲学", "哲学", "本科", 4, "哲学思辨与人文素养"),
    ("M101", "计算机应用技术", "电子与信息", "专科", 3, "计算机应用与维护"),
    ("M102", "软件技术", "电子与信息", "专科", 3, "软件开发与测试"),
    ("M103", "大数据技术", "电子与信息", "专科", 3, "大数据处理与应用"),
    ("M104", "电子商务", "财经商贸", "专科", 3, "电商运营与管理"),
    ("M105", "会计信息管理", "财经商贸", "专科", 3, "会计核算与信息化"),
    ("M106", "市场营销", "财经商贸", "专科", 3, "市场开发与营销策划"),
    ("M107", "护理", "医药卫生", "专科", 3, "临床护理与保健"),
    ("M108", "临床医学", "医药卫生", "专科", 3, "基层临床医疗"),
    ("M109", "口腔医学技术", "医药卫生", "专科", 3, "口腔修复技术"),
    ("M110", "学前教育", "教育与体育", "专科", 3, "幼儿教育与保育"),
    ("M111", "小学教育", "教育与体育", "专科", 3, "小学教学"),
    ("M112", "机电一体化技术", "装备制造", "专科", 3, "机电设备运行与维护"),
    ("M113", "汽车检测与维修技术", "交通运输", "专科", 3, "汽车故障诊断与维修"),
    ("M114", "建筑工程技术", "土木建筑", "专科", 3, "建筑施工与管理"),
    ("M115", "工程造价", "土木建筑", "专科", 3, "工程造价编制与管理"),
    ("M116", "旅游管理", "旅游", "专科", 3, "旅游服务与管理"),
    ("M117", "酒店管理与数字化运营", "旅游", "专科", 3, "酒店运营与数字化管理"),
    ("M118", "现代物流管理", "财经商贸", "专科", 3, "物流运营与信息化"),
    ("M119", "数字媒体艺术设计", "文化艺术", "专科", 3, "数字媒体创意设计"),
    ("M120", "畜牧兽医", "农林牧渔", "专科", 3, "畜禽养殖与疾病防治"),
]

MAJOR_NAME_MAP = {m[0]: m[1] for m in MAJORS_DATA}
MAJOR_DURATION_MAP = {m[0]: m[4] for m in MAJORS_DATA}

# 本科专业分组
HOT_SCIENCE = ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M018", "M019"]
GOOD_SCIENCE = ["M008", "M009", "M010", "M011", "M013", "M020", "M021", "M022", "M025"]
NORMAL_SCIENCE = ["M012", "M014", "M015", "M016", "M017", "M023", "M024"]
MEDICAL = ["M026", "M027", "M028", "M029", "M030", "M031"]
ECON_MGMT = ["M032", "M033", "M034", "M035", "M036", "M037", "M038", "M039"]
LIBERAL_ARTS = ["M040", "M041", "M042", "M043", "M044", "M045", "M047", "M048", "M050", "M056"]

ZK_TECH = ["M101", "M102", "M103", "M112", "M113", "M114", "M115"]
ZK_BUSINESS = ["M104", "M105", "M106", "M118"]
ZK_MEDICAL = ["M107", "M108", "M109"]
ZK_EDUCATION = ["M110", "M111"]
ZK_OTHER = ["M116", "M117", "M119", "M120"]


# ============================================================
# 4. 院校分数模型
# ============================================================

def get_base_score(level, category, subject):
    """根据院校层次返回分数基准范围"""
    offset = 0 if subject == "物理类" else -5
    if level == "985":
        return (640 + offset, 690 + offset) if category in ("理工", "综合") else (620 + offset, 670 + offset)
    elif level == "211":
        return (580 + offset, 640 + offset) if category in ("理工", "财经") else (560 + offset, 620 + offset)
    elif level == "双一流":
        return (550 + offset, 600 + offset)
    elif level == "普通本科":
        return (450 + offset, 550 + offset) if category in ("理工", "财经", "医药") else (430 + offset, 530 + offset)
    else:
        return (200, 420)


def get_province_difficulty(province):
    """各省竞争难度修正"""
    hard = {"河南": -20, "山东": -15, "河北": -15, "安徽": -10, "广东": -10, "四川": -8, "湖南": -8, "江西": -10}
    easy = {"北京": 15, "上海": 15, "天津": 10, "西藏": 20, "青海": 15, "宁夏": 10, "新疆": 8, "海南": 5}
    return hard.get(province, easy.get(province, 0))


# ============================================================
# 5. 核心生成逻辑
# ============================================================

def assign_majors(college):
    """为院校分配专业"""
    _, name, prov, city, level, category, is_985, is_211, is_syl, edu_level = college
    if edu_level == "专科":
        all_zk = ZK_TECH + ZK_BUSINESS + ZK_MEDICAL + ZK_EDUCATION + ZK_OTHER
        return random.sample(all_zk, random.randint(6, 10))
    else:
        majors = []
        if category in ("理工",):
            majors = random.sample(HOT_SCIENCE + GOOD_SCIENCE + NORMAL_SCIENCE, random.randint(8, 15))
            majors += random.sample(ECON_MGMT, random.randint(1, 3))
        elif category in ("综合",):
            majors = random.sample(HOT_SCIENCE + GOOD_SCIENCE, random.randint(4, 8))
            majors += random.sample(ECON_MGMT, random.randint(2, 4))
            majors += random.sample(LIBERAL_ARTS, random.randint(2, 4))
            majors += random.sample(NORMAL_SCIENCE, random.randint(1, 3))
        elif category == "财经":
            majors = ECON_MGMT[:] + random.sample(HOT_SCIENCE[:3], 2)
        elif category == "师范":
            majors = random.sample(LIBERAL_ARTS, random.randint(4, 7))
            majors += random.sample(HOT_SCIENCE[:3] + GOOD_SCIENCE[:3], random.randint(2, 4))
        elif category == "医药":
            majors = MEDICAL[:] + random.sample(NORMAL_SCIENCE[4:], 2)
        elif category == "农林":
            majors = ["M051", "M052", "M053"] + random.sample(NORMAL_SCIENCE, random.randint(2, 4))
        elif category == "政法":
            majors = ["M040", "M041", "M042"] + random.sample(ECON_MGMT[:4], 2)
        elif category == "语言":
            majors = ["M044", "M043", "M045"] + random.sample(ECON_MGMT[:3], 2)
        elif category == "艺术":
            majors = ["M054", "M055"] + random.sample(LIBERAL_ARTS[5:], 2)
        else:
            majors = random.sample(HOT_SCIENCE[:4] + ECON_MGMT[:4] + LIBERAL_ARTS[:4], random.randint(6, 10))
        return list(set(majors))[:15]


def assign_provinces(college):
    """为院校分配招生省份"""
    _, name, home_prov, city, level, *_ = college
    if level == "985":
        n = random.randint(25, 31)
    elif level == "211":
        n = random.randint(15, 25)
    elif level == "双一流":
        n = random.randint(10, 18)
    elif level == "普通本科":
        n = random.randint(5, 12)
    else:  # 专科
        # 本省 + 邻省
        neighbors = NEIGHBOR_PROVINCES.get(home_prov, [])
        n_extra = random.randint(1, min(3, len(neighbors)))
        return [home_prov] + random.sample(neighbors, n_extra)

    provinces = [home_prov]
    others = [p for p in ALL_PROVINCES if p != home_prov]
    random.shuffle(others)
    provinces.extend(others[:n-1])
    return provinces


def generate_admission_score(base_min, base_max, year, province, major_id):
    """生成录取分数"""
    year_offset = (year - 2023) * random.randint(-3, 5)
    prov_offset = get_province_difficulty(province)
    hot_offset = 0
    if major_id in HOT_SCIENCE:
        hot_offset = random.randint(5, 20)
    elif major_id in MEDICAL[:3]:
        hot_offset = random.randint(3, 15)
    elif major_id in LIBERAL_ARTS:
        hot_offset = random.randint(-5, 5)

    base = random.randint(base_min, base_max) + year_offset + prov_offset + hot_offset
    min_score = max(150, base + random.randint(-5, 0))
    avg_score = min_score + random.randint(2, 8)
    max_score = avg_score + random.randint(3, 15)
    return min_score, avg_score, max_score


def score_to_rank(score, province, subject):
    """分数转位次"""
    cfg = PROVINCES_CONFIG[province]
    pool = cfg[3] * 10000 * (0.55 if subject == "物理类" else 0.45)
    return max(1, int(pool * (750 - score) / 600))


# ============================================================
# 6. 一分一段表
# ============================================================

def generate_score_rank_table(province, subject, year):
    """生成一分一段表（每3分一档）"""
    cfg = PROVINCES_CONFIG[province]
    pool = int(cfg[3] * 10000 * (0.55 if subject == "物理类" else 0.45))
    base_line = cfg[0] if subject == "物理类" else cfg[1]
    mean_score = base_line + 80 + random.randint(-10, 10)
    std_dev = 55 + random.randint(-5, 5)

    rows = []
    cumulative = 0
    for score in range(750, 149, -1):
        z = (score - mean_score) / std_dev
        density = math.exp(-0.5 * z * z)
        same_count = max(1, int(density * pool / (std_dev * 2.5)))
        if score > 700:
            same_count = max(1, same_count // 10)
        elif score > 680:
            same_count = max(1, same_count // 5)
        elif score < 200:
            same_count = max(1, same_count // 3)
        cumulative += same_count
        if cumulative > pool:
            same_count = max(1, same_count - (cumulative - pool))
            cumulative = pool
        # 每3分记录一条
        if score % 3 == 0 and 150 <= score <= 750 and cumulative <= pool:
            rows.append((year, province, subject, score, cumulative, same_count))
        if cumulative >= pool:
            break
    return rows


# ============================================================
# 7. 主执行逻辑
# ============================================================

def main():
    start = time.time()

    print("=" * 60)
    print("  高考志愿填报系统 - 全国完整数据生成 v2")
    print("  目标: 本科~1308 + 专科~1560 = ~2868所")
    print("  覆盖: 31省 × 2022-2025年 × 76个专业")
    print("=" * 60)

    # 初始化
    init_database()
    import sqlite3
    db_path = str(Path(__file__).parent.parent / "data" / "gaokao.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    cursor = conn.cursor()

    # 清空
    for table in ["colleges", "majors", "college_majors", "admission_scores",
                  "province_lines", "score_rank_table", "enrollment_plans"]:
        cursor.execute(f"DELETE FROM {table}")
    conn.commit()
    print("\n[1/7] 已清空旧数据")

    # 专业
    for m in MAJORS_DATA:
        cursor.execute("INSERT OR REPLACE INTO majors (major_id,name,category,level,duration,description) VALUES (?,?,?,?,?,?)", m)
    conn.commit()
    print(f"[2/7] 已写入 {len(MAJORS_DATA)} 个专业")

    # 院校
    colleges = generate_colleges()
    for c in colleges:
        cid, name, prov, city, level, cat, is985, is211, is_syl, edu_lvl = c
        cursor.execute("""INSERT OR REPLACE INTO colleges
            (college_id,name,province,city,level,category,is_985,is_211,
             is_double_first_class,official_site,phone,address,intro,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
            (cid, name, prov, city, level, cat, is985, is211, is_syl,
             f"https://www.college{cid}.edu.cn", f"0{random.randint(10,99)}-{random.randint(10000000,99999999)}",
             f"{prov}{city}", f"{name}是{prov}一所{level}{cat}类院校"))
    conn.commit()
    n_bk = sum(1 for c in colleges if c[9] == "本科")
    n_zk = sum(1 for c in colleges if c[9] == "专科")
    print(f"[3/7] 已写入 {len(colleges)} 所院校 (本科{n_bk} + 专科{n_zk})")

    # 省控线
    all_lines = []
    for prov, (bp, bh, bs, _) in PROVINCES_CONFIG.items():
        all_lines.extend(get_province_lines(prov, bp, bh, bs))
    for line in all_lines:
        cursor.execute("INSERT OR REPLACE INTO province_lines (year,province,subject_category,batch,score) VALUES (?,?,?,?,?)", line)
    conn.commit()
    print(f"[4/7] 已写入 {len(all_lines)} 条省控线")

    # 录取分数 + 招生计划 + 院校专业关联
    admission_count = 0
    plan_count = 0
    cm_count = 0
    batch_ad = []
    batch_pl = []
    batch_cm = []

    for idx, college in enumerate(colleges):
        cid, name, home_prov, city, level, cat, *_, edu_lvl = college
        assigned_majors = assign_majors(college)
        assigned_provs = assign_provinces(college)

        # 院校-专业关联
        for mid in assigned_majors:
            is_key = 1 if mid in HOT_SCIENCE[:3] else 0
            batch_cm.append((cid, mid, is_key))
            cm_count += 1

        batch_name = "本科批" if edu_lvl == "本科" else "专科批"

        for subject in ("物理类", "历史类"):
            base_min, base_max = get_base_score(level, cat, subject)

            for prov in assigned_provs:
                for year in (2022, 2023, 2024, 2025):
                    # 控制数据量：每省每年只录2个专业
                    n_here = 2
                    majors_here = random.sample(assigned_majors, min(n_here, len(assigned_majors)))

                    for mid in majors_here:
                        min_s, avg_s, max_s = generate_admission_score(base_min, base_max, year, prov, mid)
                        min_rank = score_to_rank(min_s, prov, subject)
                        major_name = MAJOR_NAME_MAP[mid]
                        plan_n = random.randint(2, 25)

                        batch_ad.append((year, cid, name, major_name, prov, subject,
                                        batch_name, min_s, avg_s, max_s, min_rank,
                                        plan_n, plan_n + random.randint(-1, 2)))
                        admission_count += 1

                        if year >= 2024:
                            tuition = random.choice([4500, 5000, 5500, 6000, 8000]) if edu_lvl == "本科" else random.choice([3500, 4000, 4500, 5000])
                            batch_pl.append((year, cid, name, major_name, prov, subject,
                                           plan_n, MAJOR_DURATION_MAP[mid], tuition, ""))
                            plan_count += 1

        # 每100所提交一次
        if (idx + 1) % 100 == 0 or idx == len(colleges) - 1:
            cursor.executemany("INSERT INTO college_majors (college_id,major_id,is_key_major) VALUES (?,?,?)", batch_cm)
            cursor.executemany("""INSERT INTO admission_scores
                (year,college_id,college_name,major_name,province,subject_category,
                 batch,min_score,avg_score,max_score,min_rank,plan_count,actual_count)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", batch_ad)
            cursor.executemany("""INSERT INTO enrollment_plans
                (year,college_id,college_name,major_name,province,subject_category,
                 plan_count,duration,tuition,remarks) VALUES (?,?,?,?,?,?,?,?,?,?)""", batch_pl)
            conn.commit()
            batch_cm.clear()
            batch_ad.clear()
            batch_pl.clear()
            pct = (idx + 1) / len(colleges) * 100
            print(f"  进度: {idx+1}/{len(colleges)} ({pct:.0f}%) | 录取: {admission_count:,} | 计划: {plan_count:,}")

    print(f"[5/7] 录取分数: {admission_count:,} | 招生计划: {plan_count:,} | 院校专业: {cm_count:,}")

    # 一分一段表
    print("[6/7] 生成一分一段表...")
    rank_count = 0
    batch_ranks = []
    for prov in ALL_PROVINCES:
        for subject in ("物理类", "历史类"):
            for year in (2022, 2023, 2024, 2025):
                rows = generate_score_rank_table(prov, subject, year)
                batch_ranks.extend(rows)
                rank_count += len(rows)
        cursor.executemany("INSERT OR REPLACE INTO score_rank_table (year,province,subject_category,score,rank_number,same_score_count) VALUES (?,?,?,?,?,?)", batch_ranks)
        conn.commit()
        batch_ranks.clear()
    print(f"[6/7] 一分一段表: {rank_count:,} 条")

    # VACUUM压缩
    print("[7/7] VACUUM压缩...")
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("VACUUM")
    conn.close()

    import os
    # 删除WAL/SHM
    for ext in ("-wal", "-shm"):
        p = db_path + ext
        if os.path.exists(p):
            os.remove(p)

    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"  生成完成!")
    print(f"  院校: {len(colleges)} 所 (本科{n_bk} + 专科{n_zk})")
    print(f"  录取记录: {admission_count:,}")
    print(f"  招生计划: {plan_count:,}")
    print(f"  一分一段: {rank_count:,}")
    print(f"  数据库: {size_mb:.1f} MB")
    print(f"  耗时: {elapsed:.1f} 秒")
    print(f"{'='*60}")

    # 院校层次分布
    conn2 = __import__('sqlite3').connect(db_path)
    for lv in ["985", "211", "双一流", "普通本科", "专科"]:
        cnt = conn2.execute("SELECT COUNT(*) FROM colleges WHERE level=?", (lv,)).fetchone()[0]
        print(f"  {lv}: {cnt} 所")
    conn2.close()


if __name__ == "__main__":
    main()
