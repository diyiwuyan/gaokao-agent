"""全局配置"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# LLM 配置
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 数据库
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "gaokao.db"))

# 服务
API_PORT = int(os.getenv("API_PORT", "8000"))
GRADIO_PORT = int(os.getenv("GRADIO_PORT", "7860"))

# 掌上高考 API
GAOKAO_CN_BASE_URL = "https://api.gaokao.cn"
GAOKAO_CN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.gaokao.cn/",
    "Origin": "https://www.gaokao.cn",
}

# 省份配置（新高考改革分类）
PROVINCE_CONFIG = {
    # 3+1+2 模式省份
    "3+1+2": [
        "河北", "辽宁", "江苏", "福建", "湖北", "湖南", "广东", "重庆",
        "黑龙江", "吉林", "安徽", "江西", "广西", "贵州", "甘肃",
    ],
    # 3+3 模式省份
    "3+3": [
        "上海", "浙江", "北京", "天津", "山东", "海南",
    ],
    # 传统文理分科省份
    "传统": [
        "河南", "四川", "云南", "陕西", "山西", "内蒙古", "宁夏",
        "青海", "新疆", "西藏",
    ],
}
