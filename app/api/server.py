"""FastAPI 服务端"""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.graph import chat, chat_stream
from app.data.database import get_connection


app = FastAPI(
    title="高考志愿填报 AI Agent",
    description="基于 LangGraph ReAct 架构的智能志愿填报助手 API",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 请求/响应模型 ============

class ChatRequest(BaseModel):
    message: str
    thread_id: str = ""


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


class DataStatsResponse(BaseModel):
    total_colleges: int
    total_admission_records: int
    provinces_covered: list[str]
    years_covered: list[int]


# ============ API 端点 ============

@app.get("/")
async def root():
    return {"service": "高考志愿填报 AI Agent", "status": "running", "version": "0.1.0"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """与 AI 顾问对话"""
    thread_id = req.thread_id or str(uuid.uuid4())

    try:
        reply = chat(req.message, thread_id=thread_id)
        return ChatResponse(reply=reply, thread_id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行出错: {str(e)}")


@app.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """流式对话"""
    thread_id = req.thread_id or str(uuid.uuid4())

    async def generate():
        async for chunk in chat_stream(req.message, thread_id=thread_id):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/data/stats", response_model=DataStatsResponse)
async def data_stats():
    """查看数据库统计信息"""
    with get_connection() as conn:
        college_count = conn.execute("SELECT COUNT(*) FROM colleges").fetchone()[0]
        record_count = conn.execute("SELECT COUNT(*) FROM admission_scores").fetchone()[0]

        provinces = [
            row[0] for row in
            conn.execute("SELECT DISTINCT province FROM admission_scores WHERE province IS NOT NULL").fetchall()
        ]

        years = [
            row[0] for row in
            conn.execute("SELECT DISTINCT year FROM admission_scores ORDER BY year").fetchall()
        ]

    return DataStatsResponse(
        total_colleges=college_count,
        total_admission_records=record_count,
        provinces_covered=provinces,
        years_covered=years,
    )


@app.get("/data/search_college")
async def search_college(name: str, limit: int = 10):
    """搜索院校"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM colleges WHERE name LIKE ? LIMIT ?",
            (f"%{name}%", limit)
        ).fetchall()
    return [dict(r) for r in rows]


def run_server():
    """启动 FastAPI 服务"""
    import uvicorn
    from app.config import API_PORT
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)


if __name__ == "__main__":
    run_server()
