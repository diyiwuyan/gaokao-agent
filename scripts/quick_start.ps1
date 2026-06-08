# 高考志愿填报 AI Agent - 快速启动脚本 (PowerShell)
# 用法: .\scripts\quick_start.ps1

Write-Host "🎓 高考志愿填报 AI Agent - 快速启动" -ForegroundColor Cyan
Write-Host "=" * 50

# 检查 Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ 未检测到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python: $(python --version)" -ForegroundColor Green

# 进入项目目录
$projectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectDir
Write-Host "📁 项目目录: $projectDir"

# 创建虚拟环境
if (-not (Test-Path ".venv")) {
    Write-Host "`n📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
}

# 激活虚拟环境
Write-Host "🔄 激活虚拟环境..."
& .\.venv\Scripts\Activate.ps1

# 安装依赖
Write-Host "`n📦 安装依赖（uv 方式）..." -ForegroundColor Yellow
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    uv pip install -e ".[dev]"
} else {
    Write-Host "  (未检测到 uv，使用 pip)" -ForegroundColor Gray
    pip install -e ".[dev]"
}

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "`n⚙️  创建 .env 配置文件..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "  ⚠️  请编辑 .env 填入你的 LLM API Key" -ForegroundColor Yellow
    Write-Host "  文件路径: $projectDir\.env" -ForegroundColor Gray
}

# 初始化数据库并灌入演示数据
Write-Host "`n🗄️  初始化数据库..." -ForegroundColor Yellow
python main.py init-db

Write-Host "`n🌱 灌入演示数据..." -ForegroundColor Yellow
python scripts/seed_demo_data.py

# 完成
Write-Host "`n" + "=" * 50
Write-Host "🎉 启动准备完成！" -ForegroundColor Green
Write-Host ""
Write-Host "可用命令:" -ForegroundColor Cyan
Write-Host "  python main.py chat    # 命令行对话（需要配置 LLM API Key）"
Write-Host "  python main.py ui      # Web 界面（Gradio）"
Write-Host "  python main.py api     # API 服务（FastAPI）"
Write-Host ""
Write-Host "💡 首次使用请确保 .env 中已配置:" -ForegroundColor Yellow
Write-Host "   LLM_API_KEY=你的API密钥"
Write-Host "   LLM_BASE_URL=你的API地址"
Write-Host ""
