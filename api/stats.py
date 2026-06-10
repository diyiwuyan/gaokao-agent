"""Vercel Serverless Function - 数据统计接口（轻量级）"""

import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """返回数据库基本统计信息"""
        stats = {
            "total_colleges": 2868,
            "benke_colleges": 1308,
            "zhuanke_colleges": 1560,
            "provinces_covered": 31,
            "years_covered": [2022, 2023, 2024, 2025],
            "total_admission_records": 279296,
            "status": "running",
        }
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(stats, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
