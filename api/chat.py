"""Vercel Serverless Function - 对话接口

将用户消息发送给 DeepSeek LLM，带上系统提示和工具结果。
Vercel 每个请求最长执行 60s（Hobby 计划）。
"""

import os
import json
from http.server import BaseHTTPRequestHandler


# DeepSeek API 配置
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """你是「志愿哥」，一位专业的高考志愿填报 AI 顾问。

你的能力：
1. 分析考生分数和位次
2. 推荐适合的院校和专业
3. 计算录取概率（基于位次法）
4. 生成冲-稳-保三档志愿方案
5. 解读高考政策（平行志愿、新高考选科等）

数据说明：
- 你拥有全国 2868 所院校的数据（本科1308所 + 专科1560所）
- 覆盖全部 31 个省份
- 包含 2022-2025 年的录取数据
- 使用位次法进行概率评估

回答要求：
- 回复简洁专业，重要数字用加粗或emoji标注
- 给出具体的分数线和位次数据
- 建议时说明依据（如"根据近3年数据"）
- 如果信息不足，主动追问考生的省份、科类、分数等
- 给出冲稳保方案时，说明每所学校的录取概率档位

注意：你是纯对话模式，如果用户问某所学校的具体分数线，根据你的训练知识给出参考数据，并提醒用户以官方数据为准。"""


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            message = data.get("message", "")
            history = data.get("history", [])  # [{role, content}, ...]

            if not message:
                self._json_response(400, {"error": "message 不能为空"})
                return

            if not LLM_API_KEY:
                self._json_response(500, {"error": "服务端未配置 LLM_API_KEY"})
                return

            # 构建消息列表
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for h in history[-20:]:  # 只保留最近20轮
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message})

            # 调用 DeepSeek API
            import urllib.request
            import urllib.error

            req_body = json.dumps({
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4096,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{LLM_BASE_URL}/chat/completions",
                data=req_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LLM_API_KEY}",
                },
            )

            with urllib.request.urlopen(req, timeout=55) as resp:
                result = json.loads(resp.read())

            reply = result["choices"][0]["message"]["content"]
            self._json_response(200, {"reply": reply})

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            self._json_response(502, {"error": f"LLM API 错误: {error_body}"})
        except Exception as e:
            self._json_response(500, {"error": f"服务端错误: {str(e)}"})

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _json_response(self, status, data):
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
