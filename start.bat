@echo off
chcp 65001 >nul
echo 正在启动自动化Git提交和新闻收集程序...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

python -c "import git" >nul 2>&1
if errorlevel 1 (
    echo 正在安装GitPython...
    pip install GitPython
)

REM 检查并卸载可能冲突的django-scheduler
python -c "import schedule; assert hasattr(schedule, 'every')" >nul 2>&1
if errorlevel 1 (
    echo 检测到schedule模块问题，正在修复...
    pip uninstall django-scheduler -y >nul 2>&1
    pip uninstall schedule -y >nul 2>&1
    pip install schedule
    if errorlevel 1 (
        echo 错误: schedule模块安装失败
        pause
        exit /b 1
    )
    REM 再次验证
    python -c "import schedule; assert hasattr(schedule, 'every')" >nul 2>&1
    if errorlevel 1 (
        echo 错误: schedule模块验证失败，请手动运行 fix_schedule.py
        pause
        exit /b 1
    )
)

REM 检查配置文件
if not exist "config.json" (
    echo 错误: 未找到config.json配置文件
    echo 请先创建config.json文件并填入Git令牌
    pause
    exit /b 1
)

REM 启动程序
echo 程序启动中...
python auto_commit.py

pause

