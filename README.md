# 🎓 高考志愿填报 AI Agent

基于 **LangGraph ReAct 架构**的智能高考志愿填报助手。Agent 能自主推理、调用工具、多轮对话，为考生提供个性化的志愿填报方案。

🌐 **在线体验**: [https://diyiwuyan.github.io/gaokao-agent](https://diyiwuyan.github.io/gaokao-agent)

## ✨ 核心特性

- **AI Agent 自主决策** — 基于 LangGraph ReAct 循环，Agent 自主判断何时调用哪个工具
- **位次法精准预测** — 基于历年一分一段表，用位次而非分数计算录取概率
- **冲稳保方案生成** — 自动生成"冲刺-稳妥-保底"三档志愿方案
- **8 大专业工具** — 覆盖分数分析、院校搜索、录取查询、概率计算、专业推荐、院校对比、政策解读、策略建议
- **多轮对话记忆** — 支持连续追问，Agent 记住上下文
- **掌上高考数据源** — 对接 gaokao.cn API 获取真实录取数据

## 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│              用户界面层                        │
│   Gradio Web UI / CLI / REST API            │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            LangGraph ReAct Agent             │
│                                             │
│  ┌─────────┐    ┌──────────┐    ┌────────┐  │
│  │ Reason  │───▶│   Act    │───▶│Observe │  │
│  │ (思考)   │◀───│ (执行工具) │◀───│(观察)   │  │
│  └─────────┘    └──────────┘    └────────┘  │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              工具层 (8 Tools)                  │
│                                             │
│  📊 分数分析  🏫 院校搜索  📋 录取查询         │
│  🎯 概率计算  🎓 专业推荐  ⚖️ 院校对比         │
│  📜 政策解读  📝 策略建议                      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              数据层                           │
│   SQLite + 掌上高考 API + 内置知识库          │
└─────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 一个兼容 OpenAI 的 LLM API（DeepSeek、智谱、Moonshot 等）

### 安装

```bash
git clone https://github.com/diyiwuyan/gaokao-agent.git
cd gaokao-agent

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

# 安装依赖
pip install -e .
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

`.env` 关键配置：
```
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### 初始化数据

```bash
# 初始化数据库
python main.py init-db

# 灌入演示数据（可选，用于快速体验）
python scripts/seed_demo_data.py

# 或从掌上高考爬取真实数据
python main.py crawl --province 河北 --year 2024
```

### 启动

```bash
# 命令行对话
python main.py chat

# Web 界面（推荐）
python main.py ui

# API 服务
python main.py api
```

## 💬 使用示例

```
你：我是河北物理类考生，考了650分，想学计算机，帮我推荐一下

志愿哥：好的！让我帮你分析一下...
   📊 650分在河北物理类对应位次约1800名
   🏫 以下是适合你的计算机类院校推荐：
   
   🔴 冲刺: 浙江大学、南京大学、北航
   🟡 稳妥: 哈工大、武大、华科、电子科大
   🟢 保底: 北邮、西南交大、河北工业大学
   ...
```

## 📁 项目结构

```
gaokao-agent/
├── main.py                 # 入口（CLI 命令）
├── pyproject.toml          # 项目配置
├── .env.example            # 环境变量模板
├── app/
│   ├── config.py           # 全局配置
│   ├── ui.py               # Gradio 界面
│   ├── agent/
│   │   ├── graph.py        # LangGraph ReAct 核心
│   │   └── prompts.py      # System Prompt
│   ├── api/
│   │   └── server.py       # FastAPI REST API
│   ├── crawler/
│   │   └── gaokao_cn.py    # 掌上高考爬虫
│   ├── data/
│   │   └── database.py     # SQLite 数据库
│   ├── models/
│   │   └── schemas.py      # Pydantic 模型
│   └── tools/              # 8 个 Agent 工具
│       ├── score_analysis.py
│       ├── college_search.py
│       ├── admission_query.py
│       ├── probability_calc.py
│       ├── major_recommend.py
│       ├── college_compare.py
│       ├── policy_interpret.py
│       └── strategy_suggest.py
├── scripts/
│   ├── seed_demo_data.py   # 演示数据
│   └── quick_start.ps1     # Windows 快速启动
└── docs/                   # GitHub Pages 网站
```

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph + LangChain |
| LLM | OpenAI 兼容接口（DeepSeek/智谱/Moonshot） |
| 后端 | FastAPI + Uvicorn |
| 前端 | Gradio |
| 数据库 | SQLite |
| 数据源 | 掌上高考 (gaokao.cn) API |

## 📊 支持省份

- **新高考 3+1+2**: 河北、辽宁、江苏、福建、湖北、湖南、广东、重庆
- **新高考 3+3**: 浙江、上海、北京、天津、山东、海南
- **传统高考**: 河南、四川、安徽、陕西、山西、广西 等

## 📄 License

MIT License - 详见 [LICENSE](./LICENSE)

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent 编排框架
- [掌上高考](https://www.gaokao.cn) - 数据来源
- [Gradio](https://gradio.app) - 快速 Web UI
