"""验证推荐准确性：模拟2025年考生，调用线上API测试推荐结果"""
import json
import urllib.request
import urllib.error
import sqlite3
import sys

# 配置
API_URL = "https://gaokao-agent.vercel.app/api/chat"
DB_PATH = "data/gaokao.db"

# 测试用例：不同省份、分数段的考生
TEST_CASES = [
    {"year": 2025, "province": "山东", "category": "物理类", "score": 620, "desc": "山东物理620（中高段）"},
    {"year": 2025, "province": "山东", "category": "历史类", "score": 580, "desc": "山东历史580（中段）"},
    {"year": 2025, "province": "广东", "category": "物理类", "score": 650, "desc": "广东物理650（高段）"},
    {"year": 2025, "province": "河南", "category": "物理类", "score": 550, "desc": "河南物理550（中段）"},
    {"year": 2025, "province": "北京", "category": "物理类", "score": 600, "desc": "北京物理600"},
]


def query_db_truth(case):
    """从数据库查出该分数附近的真实录取数据作为参考"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    score = case["score"]
    
    # 查冲（高10-20分）、稳（-5到+10）、保（低10-20分）
    results = {}
    ranges = {
        "冲": (score + 5, score + 25),
        "稳": (score - 10, score + 5),
        "保": (score - 25, score - 10),
    }
    
    for tier, (low, high) in ranges.items():
        c.execute("""
            SELECT DISTINCT a.college_name, c.level, a.min_score, a.min_rank, a.subject_category
            FROM admission_scores a
            JOIN colleges c ON a.college_id = c.college_id
            WHERE a.year = ? AND a.province = ? AND a.subject_category = ?
            AND a.min_score BETWEEN ? AND ?
            ORDER BY a.min_score DESC
            LIMIT 5
        """, (case["year"], case["province"], case["category"], low, high))
        results[tier] = c.fetchall()
    
    conn.close()
    return results


def call_api(case):
    """调用线上API获取推荐结果"""
    year = case["year"]
    province = case["province"]
    category = case["category"]
    score = case["score"]
    message = (
        f"[{year}年高考志愿填报咨询]\n"
        f"省份: {province}\n"
        f"科类: {category}\n"
        f"分数: {score}分\n\n"
        "请帮我生成冲稳保方案。请给出冲（录取概率20-40%）、稳（60-80%）、保（>90%）三档各3-5所院校，附上近年录取分数和位次数据。"
    )
    
    req_body = json.dumps({"message": message, "history": []}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=req_body,
        headers={"Content-Type": "application/json"},
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("reply", "")
    except urllib.error.HTTPError as e:
        return f"[HTTP ERROR {e.code}] {e.read().decode()}"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def main():
    print("=" * 70)
    print("  高考志愿推荐系统 - 准确性验证测试")
    print("=" * 70)
    
    # 先验证数据库数据
    print("\n📊 第一步：查看数据库中的真实录取数据\n")
    
    for i, case in enumerate(TEST_CASES):
        print(f"\n{'─' * 60}")
        print(f"  测试 {i+1}: {case['desc']}")
        print(f"{'─' * 60}")
        
        truth = query_db_truth(case)
        for tier, records in truth.items():
            print(f"\n  【{tier}】档 ({len(records)} 所):")
            for r in records:
                print(f"    {r[0]} [{r[1]}] | {r[4]} | 分数:{r[2]} | 位次:{r[3]}")
    
    # 如果指定了 --api 参数，则调用线上API
    if "--api" in sys.argv:
        print("\n\n" + "=" * 70)
        print("  📡 第二步：调用线上API验证推荐结果")
        print("=" * 70)
        
        # 只测第一个case（避免调用太多次）
        case = TEST_CASES[0]
        print(f"\n  测试: {case['desc']}")
        print(f"  正在调用 API...")
        
        reply = call_api(case)
        print(f"\n  AI 回复:")
        print(f"  {'─' * 50}")
        for line in reply.split('\n'):
            print(f"  {line}")
        print(f"  {'─' * 50}")
        
        # 对比
        print(f"\n  📋 对比数据库真实数据:")
        truth = query_db_truth(case)
        for tier, records in truth.items():
            schools = [r[0] for r in records]
            print(f"    {tier}档应含: {', '.join(schools)}")
    else:
        print("\n\n💡 提示：加 --api 参数可调用线上API验证（如 python scripts/test_recommend.py --api）")
    
    print("\n✅ 验证完成！")


if __name__ == "__main__":
    main()
