"""掌上高考 (gaokao.cn) 数据采集器

数据源说明：
- gaokao.cn 是中国高等教育学生信息网（学信网）旗下的高考信息服务平台
- 提供院校信息、录取分数线、招生计划等公开数据
- 本爬虫仅采集公开可访问的数据，用于学习和研究
"""

import time
import json
import httpx
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.config import GAOKAO_CN_BASE_URL, GAOKAO_CN_HEADERS
from app.data.database import get_connection

console = Console()

# 省份编码映射
PROVINCE_CODES = {
    "北京": "11", "天津": "12", "河北": "13", "山西": "14", "内蒙古": "15",
    "辽宁": "21", "吉林": "22", "黑龙江": "23", "上海": "31", "江苏": "32",
    "浙江": "33", "安徽": "34", "福建": "35", "江西": "36", "山东": "37",
    "河南": "41", "湖北": "42", "湖南": "43", "广东": "44", "广西": "45",
    "海南": "46", "重庆": "50", "四川": "51", "贵州": "52", "云南": "53",
    "西藏": "54", "陕西": "61", "甘肃": "62", "青海": "63", "宁夏": "64",
    "新疆": "65",
}


class GaokaoCrawler:
    """掌上高考数据采集器"""

    def __init__(self):
        self.client = httpx.Client(
            headers=GAOKAO_CN_HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )
        self.request_interval = 1.0  # 请求间隔（秒），避免过快

    def _request(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """发送请求并返回JSON"""
        try:
            time.sleep(self.request_interval)
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == "0000" or data.get("code") == 0:
                return data.get("data", data)
            console.print(f"[yellow]API返回异常: {data.get('msg', 'unknown')}[/yellow]")
            return None
        except httpx.HTTPError as e:
            console.print(f"[red]请求失败: {e}[/red]")
            return None
        except json.JSONDecodeError:
            console.print("[red]JSON解析失败[/red]")
            return None

    def fetch_college_list(self, page: int = 1, size: int = 20,
                           province_id: Optional[str] = None) -> list[dict]:
        """获取院校列表
        
        API: https://api.gaokao.cn/api/college/list
        参数: page, size, province_id, level(层次), type(类型)
        """
        url = f"{GAOKAO_CN_BASE_URL}/api/college/list"
        params = {"page": page, "size": size}
        if province_id:
            params["province_id"] = province_id

        data = self._request(url, params)
        if data and isinstance(data, dict):
            return data.get("list", data.get("items", []))
        return []

    def fetch_college_detail(self, college_id: str) -> Optional[dict]:
        """获取院校详情"""
        url = f"{GAOKAO_CN_BASE_URL}/api/college/detail"
        params = {"id": college_id}
        return self._request(url, params)

    def fetch_admission_scores(self, college_id: str, province_id: str,
                                year: int, subject_type: str = "1") -> list[dict]:
        """获取某院校在某省的录取分数线
        
        参数:
            college_id: 院校ID
            province_id: 省份编码
            year: 年份
            subject_type: 科类 (1=理科/物理, 2=文科/历史)
        """
        url = f"{GAOKAO_CN_BASE_URL}/api/college/provinceline"
        params = {
            "id": college_id,
            "province_id": province_id,
            "year": year,
            "type": subject_type,
        }
        data = self._request(url, params)
        if data and isinstance(data, list):
            return data
        if data and isinstance(data, dict):
            return data.get("list", [])
        return []

    def fetch_major_scores(self, college_id: str, province_id: str,
                           year: int, subject_type: str = "1") -> list[dict]:
        """获取某院校各专业在某省的录取分数
        
        API: https://api.gaokao.cn/api/college/majorline
        """
        url = f"{GAOKAO_CN_BASE_URL}/api/college/majorline"
        params = {
            "id": college_id,
            "province_id": province_id,
            "year": year,
            "type": subject_type,
        }
        data = self._request(url, params)
        if data and isinstance(data, list):
            return data
        if data and isinstance(data, dict):
            return data.get("list", [])
        return []

    def fetch_province_line(self, province_id: str, year: int) -> list[dict]:
        """获取省控线/批次线"""
        url = f"{GAOKAO_CN_BASE_URL}/api/province/line"
        params = {"province_id": province_id, "year": year}
        data = self._request(url, params)
        if data and isinstance(data, list):
            return data
        return []

    def fetch_score_rank(self, province_id: str, year: int,
                         subject_type: str = "1") -> list[dict]:
        """获取一分一段表"""
        url = f"{GAOKAO_CN_BASE_URL}/api/province/scorerank"
        params = {
            "province_id": province_id,
            "year": year,
            "type": subject_type,
        }
        data = self._request(url, params)
        if data and isinstance(data, list):
            return data
        return []

    def crawl_and_save_colleges(self, max_pages: int = 100):
        """批量采集院校信息并存入数据库"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task("采集院校信息...", total=max_pages)

            total_saved = 0
            for page in range(1, max_pages + 1):
                colleges = self.fetch_college_list(page=page, size=30)
                if not colleges:
                    break

                with get_connection() as conn:
                    for c in colleges:
                        conn.execute("""
                            INSERT OR REPLACE INTO colleges 
                            (college_id, name, province, city, level, category, 
                             is_985, is_211, is_double_first_class)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(c.get("id", c.get("school_id", ""))),
                            c.get("name", ""),
                            c.get("province_name", ""),
                            c.get("city_name", ""),
                            c.get("level_name", ""),
                            c.get("type_name", ""),
                            1 if c.get("f985", 0) else 0,
                            1 if c.get("f211", 0) else 0,
                            1 if c.get("dual_class", 0) else 0,
                        ))
                    total_saved += len(colleges)

                progress.update(task, advance=1)

            console.print(f"[green]✅ 共采集 {total_saved} 所院校信息[/green]")

    def crawl_admission_data(self, province: str, years: list[int],
                              subject_type: str = "1", top_n: int = 200):
        """批量采集某省的录取数据
        
        Args:
            province: 省份名
            years: 年份列表
            subject_type: 科类
            top_n: 采集前N所院校的数据
        """
        province_id = PROVINCE_CODES.get(province)
        if not province_id:
            console.print(f"[red]未知省份: {province}[/red]")
            return

        # 先获取院校列表
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT college_id, name FROM colleges LIMIT ?", (top_n,)
            ).fetchall()

        if not rows:
            console.print("[yellow]请先采集院校数据 (crawl_and_save_colleges)[/yellow]")
            return

        console.print(f"开始采集 {province} {years} 录取数据，共 {len(rows)} 所院校...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(f"采集{province}录取数据...", total=len(rows) * len(years))

            for row in rows:
                college_id = row["college_id"]
                college_name = row["name"]

                for year in years:
                    scores = self.fetch_major_scores(
                        college_id, province_id, year, subject_type
                    )

                    if scores:
                        with get_connection() as conn:
                            for s in scores:
                                conn.execute("""
                                    INSERT OR IGNORE INTO admission_scores
                                    (year, college_id, college_name, major_name,
                                     province, subject_category, batch,
                                     min_score, avg_score, max_score, min_rank,
                                     plan_count, actual_count)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    year,
                                    college_id,
                                    college_name,
                                    s.get("spname", s.get("major_name", "")),
                                    province,
                                    "物理类" if subject_type == "1" else "历史类",
                                    s.get("batch", s.get("local_batch_name", "本科批")),
                                    s.get("min", s.get("min_score")),
                                    s.get("average", s.get("avg_score")),
                                    s.get("max", s.get("max_score")),
                                    s.get("min_section", s.get("min_rank")),
                                    s.get("num", s.get("plan_count")),
                                    s.get("luqu_num", s.get("actual_count")),
                                ))

                    progress.update(task, advance=1)

        console.print(f"[green]✅ {province} 录取数据采集完成[/green]")

    def close(self):
        self.client.close()


# 便捷函数
def run_full_crawl(province: str = "河北", years: list[int] = None):
    """一键执行完整数据采集流程"""
    if years is None:
        years = [2022, 2023, 2024]

    crawler = GaokaoCrawler()
    try:
        console.print("[bold]🚀 开始全量数据采集[/bold]")
        console.print(f"   目标省份: {province}")
        console.print(f"   参考年份: {years}")

        # Step 1: 采集院校列表
        console.print("\n[bold]Step 1/3: 采集院校信息[/bold]")
        crawler.crawl_and_save_colleges(max_pages=50)

        # Step 2: 采集录取数据
        console.print(f"\n[bold]Step 2/3: 采集{province}录取数据[/bold]")
        crawler.crawl_admission_data(province, years, subject_type="1")
        crawler.crawl_admission_data(province, years, subject_type="2")

        # Step 3: 采集省控线
        console.print(f"\n[bold]Step 3/3: 采集省控线[/bold]")
        province_id = PROVINCE_CODES.get(province, "13")
        for year in years:
            lines = crawler.fetch_province_line(province_id, year)
            if lines:
                with get_connection() as conn:
                    for line in lines:
                        conn.execute("""
                            INSERT OR REPLACE INTO province_lines
                            (year, province, subject_category, batch, score)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            year, province,
                            line.get("type_name", ""),
                            line.get("batch", ""),
                            line.get("score", 0),
                        ))

        console.print("\n[bold green]🎉 全量数据采集完成！[/bold green]")
    finally:
        crawler.close()


if __name__ == "__main__":
    from app.data.database import init_database
    init_database()
    run_full_crawl("河北", [2022, 2023, 2024])
