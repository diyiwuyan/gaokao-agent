"""高考志愿填报 AI Agent - 主入口

使用方式：
    # 1. 启动 Gradio 交互界面（推荐）
    python main.py ui
    
    # 2. 启动 FastAPI 服务（供前端调用）
    python main.py api
    
    # 3. 命令行对话模式
    python main.py chat
    
    # 4. 初始化数据库
    python main.py init-db
    
    # 5. 采集数据
    python main.py crawl --province 河北 --years 2022,2023,2024
"""

import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "ui":
        from app.ui import run_ui
        run_ui()

    elif command == "api":
        from app.api.server import run_server
        run_server()

    elif command == "chat":
        run_chat_mode()

    elif command == "init-db":
        from app.data.database import init_database
        init_database()

    elif command == "crawl":
        run_crawl()

    elif command in ("-h", "--help", "help"):
        print_help()

    else:
        print(f"未知命令: {command}")
        print_help()


def run_chat_mode():
    """命令行对话模式"""
    from app.data.database import init_database
    from app.agent.graph import chat

    init_database()

    print("=" * 60)
    print("🎓 高考志愿填报 AI 助手 - 命令行模式")
    print("=" * 60)
    print("输入你的问题，输入 'q' 或 'quit' 退出")
    print("-" * 60)

    thread_id = "cli-session"

    while True:
        try:
            user_input = input("\n🧑 你: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！祝你填报顺利！🎓")
            break

        if user_input.lower() in ("q", "quit", "exit", "退出"):
            print("再见！祝你填报顺利！🎓")
            break

        if not user_input:
            continue

        print("\n🤖 志愿哥: ", end="", flush=True)
        try:
            reply = chat(user_input, thread_id=thread_id)
            print(reply)
        except Exception as e:
            print(f"\n⚠️ 出错了: {e}")
            print("请检查 .env 文件中的 LLM_API_KEY 配置是否正确")


def run_crawl():
    """数据采集"""
    from datetime import date
    from app.data.database import init_database
    from app.crawler.gaokao_cn import run_full_crawl

    # 解析参数
    province = "河北"
    current_year = date.today().year
    years = [current_year - 2, current_year - 1, current_year]

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--province" and i + 1 < len(args):
            province = args[i + 1]
            i += 2
        elif args[i] == "--years" and i + 1 < len(args):
            years = [int(y) for y in args[i + 1].split(",")]
            i += 2
        else:
            i += 1

    init_database()
    run_full_crawl(province=province, years=years)


def print_help():
    print("""
🎓 高考志愿填报 AI Agent
========================

使用方式:
    python main.py <command> [options]

命令:
    ui          启动 Gradio 交互界面（推荐新手使用）
    api         启动 FastAPI 服务（供前端/小程序调用）
    chat        命令行对话模式
    init-db     初始化数据库
    crawl       采集高考数据

采集数据示例:
    python main.py crawl --province 河北 --years 2022,2023,2024

首次使用步骤:
    1. 复制 .env.example 为 .env，配置 LLM API Key
    2. python main.py init-db
    3. python main.py crawl --province 你的省份
    4. python main.py ui
""")


if __name__ == "__main__":
    main()
