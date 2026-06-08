"""Gradio 前端界面

提供对话式交互界面，支持：
- 多轮对话
- 历史记录
- 快捷操作按钮
"""

import uuid
import gradio as gr

from app.agent.graph import chat
from app.data.database import get_connection, init_database


def create_ui():
    """创建 Gradio 界面"""

    # 每个用户一个会话ID
    def get_thread_id():
        return str(uuid.uuid4())

    def respond(message: str, history: list, thread_id: str):
        """处理用户消息并返回回复"""
        if not thread_id:
            thread_id = get_thread_id()

        try:
            reply = chat(message, thread_id=thread_id)
        except Exception as e:
            reply = f"⚠️ 出错了: {str(e)}\n\n请检查：\n1. LLM API Key 是否配置正确\n2. 网络是否通畅"

        history.append((message, reply))
        return "", history, thread_id

    def get_data_status():
        """获取数据库状态"""
        try:
            with get_connection() as conn:
                colleges = conn.execute("SELECT COUNT(*) FROM colleges").fetchone()[0]
                records = conn.execute("SELECT COUNT(*) FROM admission_scores").fetchone()[0]
                provinces = conn.execute(
                    "SELECT DISTINCT province FROM admission_scores"
                ).fetchall()
                province_list = [r[0] for r in provinces if r[0]]

            return (
                f"📊 数据状态\n"
                f"- 院校数: {colleges}\n"
                f"- 录取记录数: {records}\n"
                f"- 覆盖省份: {', '.join(province_list) if province_list else '暂无'}"
            )
        except Exception:
            return "⚠️ 数据库未初始化，请先运行数据采集脚本"

    # ============ 构建界面 ============

    with gr.Blocks(
        title="高考志愿填报 AI 助手",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container { max-width: 900px !important; }
        .chatbot { min-height: 500px; }
        """
    ) as demo:
        gr.Markdown("""
        # 🎓 高考志愿填报 AI 助手
        
        基于 AI Agent 的智能志愿填报顾问，帮你科学选校选专业。
        
        **使用方法**：直接输入你的问题，比如：
        - "我河北物理类 580 分，能上什么学校？"
        - "帮我分析北京理工大学的录取概率"
        - "计算机和人工智能专业哪个好？"
        - "帮我做一个冲稳保方案"
        """)

        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    label="对话",
                    elem_classes="chatbot",
                    show_copy_button=True,
                )
                with gr.Row():
                    msg = gr.Textbox(
                        label="输入你的问题",
                        placeholder="例如：我河北物理类 580 分，帮我推荐学校",
                        scale=5,
                        show_label=False,
                    )
                    submit_btn = gr.Button("发送", variant="primary", scale=1)

            with gr.Column(scale=1):
                thread_id = gr.State(value="")

                gr.Markdown("### 快捷操作")
                with gr.Column():
                    btn_score = gr.Button("📊 分析分数", size="sm")
                    btn_college = gr.Button("🏫 搜索院校", size="sm")
                    btn_major = gr.Button("🎓 专业推荐", size="sm")
                    btn_strategy = gr.Button("📋 生成方案", size="sm")
                    btn_policy = gr.Button("📜 政策解读", size="sm")
                    btn_compare = gr.Button("⚖️ 院校对比", size="sm")

                gr.Markdown("---")
                data_status = gr.Textbox(
                    label="数据状态",
                    value=get_data_status,
                    interactive=False,
                    lines=4,
                )
                refresh_btn = gr.Button("🔄 刷新状态", size="sm")

        # ============ 事件绑定 ============

        # 发送消息
        submit_btn.click(
            respond,
            inputs=[msg, chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )
        msg.submit(
            respond,
            inputs=[msg, chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )

        # 快捷按钮
        btn_score.click(
            lambda h, t: respond("请帮我分析分数，我需要告诉你什么信息？", h, t),
            inputs=[chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )
        btn_college.click(
            lambda h, t: respond("我想搜索学校，请问我需要什么条件？", h, t),
            inputs=[chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )
        btn_major.click(
            lambda h, t: respond("请根据我的情况推荐合适的专业方向", h, t),
            inputs=[chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )
        btn_strategy.click(
            lambda h, t: respond("请帮我生成一个完整的冲稳保志愿方案", h, t),
            inputs=[chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )
        btn_policy.click(
            lambda h, t: respond("请帮我解读平行志愿投档规则和冲稳保策略", h, t),
            inputs=[chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )
        btn_compare.click(
            lambda h, t: respond("我想对比几所学校，帮我分析", h, t),
            inputs=[chatbot, thread_id],
            outputs=[msg, chatbot, thread_id],
        )

        # 刷新数据状态
        refresh_btn.click(get_data_status, outputs=[data_status])

    return demo


def run_ui():
    """启动 Gradio 界面"""
    from app.config import GRADIO_PORT

    # 确保数据库存在
    init_database()

    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=GRADIO_PORT,
        share=False,
        show_api=False,
    )


if __name__ == "__main__":
    run_ui()
