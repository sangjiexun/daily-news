@echo off
chcp 65001 >nul
echo ========================================
echo Git自动提交程序初始化脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [1/4] 检查Python依赖...
python -c "import requests, git, schedule" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [完成] 依赖安装成功
) else (
    echo [完成] 依赖已安装
)

echo.
echo [2/4] 检查配置文件...
if not exist "config.json" (
    echo [警告] config.json不存在，已自动创建
    echo 请编辑config.json文件，填入你的GitHub和Gitee令牌
) else (
    echo [完成] 配置文件已存在
)

echo.
echo [3/4] 初始化Git仓库...
if not exist ".git" (
    echo 正在初始化Git仓库...
    git init
    if errorlevel 1 (
        echo [错误] Git初始化失败，请确保已安装Git
        pause
        exit /b 1
    )
    echo [完成] Git仓库初始化成功
    echo.
    echo [提示] 请配置远程仓库：
    echo   git remote add origin https://github.com/你的用户名/你的仓库名.git
    echo   git remote add gitee https://gitee.com/你的用户名/你的仓库名.git
) else (
    echo [完成] Git仓库已存在
)

echo.
echo [4/4] 检查远程仓库配置...
git remote -v >nul 2>&1
if errorlevel 1 (
    echo [警告] 未配置远程仓库
    echo 请运行以下命令配置：
    echo   git remote add origin https://github.com/你的用户名/你的仓库名.git
    echo   git remote add gitee https://gitee.com/你的用户名/你的仓库名.git
) else (
    echo [完成] 远程仓库配置：
    git remote -v
)

echo.
echo ========================================
echo 初始化完成！
echo ========================================
echo.
echo 下一步：
echo 1. 编辑 config.json，填入GitHub和Gitee令牌
echo 2. 配置Git远程仓库（如果还没有）
echo 3. 运行 start.bat 启动程序
echo.
pause

