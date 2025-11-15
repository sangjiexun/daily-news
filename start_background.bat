@echo off
chcp 65001 >nul
echo 正在后台启动自动化Git提交和新闻收集程序...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import requests, git, schedule" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

REM 检查配置文件
if not exist "config.json" (
    echo 错误: 未找到config.json配置文件
    pause
    exit /b 1
)

REM 后台启动程序（无窗口）
start /B pythonw auto_commit.py
echo 程序已在后台启动
echo 日志文件: auto_commit.log
echo 按任意键退出...
pause >nul

