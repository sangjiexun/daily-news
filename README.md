# 自动化Git提交和新闻收集程序

这是一个Python后台程序，可以自动收集AI和Web3相关的最新新闻，并每日自动提交到GitHub和Gitee。

## 功能特性

- 🤖 自动获取AI相关新闻（来自Hacker News和Reddit）
- 🌐 自动获取Web3相关资讯（来自Reddit）
- 📝 自动保存新闻到JSON文件
- 🔄 每日自动提交到GitHub和Gitee
- 📊 每日更新限制：最多10条新闻
- ⏰ 定时任务：每天自动执行
- 🚀 **自动创建仓库**：首次运行时自动创建名为 `daily-news` 的GitHub和Gitee仓库
- 🔧 **自动初始化**：自动初始化本地Git仓库并配置远程仓库

## 快速开始

### Windows用户（推荐）

1. **运行初始化脚本**
   ```bash
   init_setup.bat
   ```
   这个脚本会自动：
   - 检查并安装Python依赖
   - 创建配置文件模板
   - 初始化Git仓库
   - 检查远程仓库配置

2. **编辑配置文件**
   
   打开 `config.json`，填入你的GitHub和Gitee令牌（已预填）：
   ```json
   {
     "github_token": "你的GitHub令牌",
     "gitee_token": "你的Gitee令牌"
   }
   ```

3. **自动创建仓库**
   
   程序会在首次运行时自动：
   - 获取你的GitHub和Gitee用户名
   - 创建名为 `daily-news` 的仓库（如果不存在）
   - 自动配置远程仓库连接
   
   **注意**：无需手动创建仓库，程序会自动处理！

4. **启动程序**
   ```bash
   # 前台运行（可以看到输出）
   start.bat
   
   # 或后台运行（无窗口）
   start_background.bat
   ```

### 手动安装步骤

1. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置Git令牌**
   
   编辑 `config.json` 文件，填入你的GitHub和Gitee令牌

3. **自动创建和初始化**
   
   程序会在首次运行时自动：
   - 创建名为 `daily-news` 的GitHub和Gitee仓库（如果不存在）
   - 初始化本地Git仓库（如果不存在）
   - 配置远程仓库连接
   
   **无需手动操作！** 程序会自动处理所有Git相关配置。

## 使用方法

### 方式1：直接运行（前台）
```bash
python auto_commit.py
```

### 方式2：后台运行（Windows）
```bash
# 使用nohup或start命令
start /B python auto_commit.py

# 或者使用Pythonw（无窗口）
pythonw auto_commit.py
```

### 方式3：作为Windows服务（推荐）

可以使用 `nssm` 或 `pywin32` 将程序注册为Windows服务。

## 配置说明

- **执行时间**：默认每天09:00执行，可在 `auto_commit.py` 中修改
- **新闻数量限制**：每日最多10条，可在 `NewsCollector` 类中修改 `max_articles_per_day`
- **新闻来源**：
  - AI新闻：Hacker News、Reddit (r/MachineLearning, r/artificial)
  - Web3新闻：Reddit (r/ethereum, r/CryptoCurrency, r/web3)

## 文件结构

```
.
├── auto_commit.py          # 主程序文件
├── config.json             # 配置文件（包含Git令牌）
├── requirements.txt        # Python依赖
├── init_setup.bat        # 初始化脚本（Windows）
├── start.bat              # 启动脚本（前台运行）
├── start_background.bat   # 启动脚本（后台运行）
├── .gitignore            # Git忽略文件
├── news_data/            # 新闻数据目录
│   └── news_YYYYMMDD.json  # 每日新闻文件
└── auto_commit.log       # 日志文件
```

## 注意事项

1. **令牌安全**：`config.json` 包含敏感信息，建议添加到 `.gitignore`
2. **网络连接**：程序需要网络连接来获取新闻
3. **Git配置**：确保Git已正确配置用户信息
4. **权限问题**：确保有写入文件的权限

## 日志

程序运行日志保存在 `auto_commit.log` 文件中，可以查看程序运行状态和错误信息。

## 故障排除

1. **Git推送失败**：检查令牌是否正确，远程仓库URL是否正确
2. **无法获取新闻**：检查网络连接，某些API可能需要代理
3. **文件权限错误**：确保有写入权限

## 许可证

MIT License

