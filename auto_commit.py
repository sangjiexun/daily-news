#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化Git/Gitee提交和新闻收集程序
每日自动获取AI和Web3相关新闻，并提交到Git和Gitee
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import logging

# 导入schedule模块，如果失败则提示安装
try:
    import schedule
    # 检查schedule模块是否有every属性
    if not hasattr(schedule, 'every'):
        raise AttributeError("schedule模块缺少'every'属性，可能是版本问题")
except ImportError:
    print("错误: schedule模块未安装")
    print("请运行: pip install schedule")
    sys.exit(1)
except AttributeError as e:
    print(f"错误: {e}")
    print("请运行: pip install --upgrade schedule")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_commit.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻收集器"""
    
    def __init__(self):
        self.max_articles_per_day = 10
        self.data_dir = Path("news_data")
        self.data_dir.mkdir(exist_ok=True)
        self.today_file = self.data_dir / f"news_{datetime.now().strftime('%Y%m%d')}.json"
        
    def get_ai_news(self):
        """获取AI相关新闻（使用NewsAPI或替代方案）"""
        articles = []
        
        # 方案1: 使用NewsAPI (需要API key，这里使用免费方案)
        # 如果没有API key，可以使用其他新闻源
        try:
            # 使用Hacker News API作为替代（免费，无需API key）
            hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(hn_url, timeout=10)
            if response.status_code == 200:
                story_ids = response.json()[:30]  # 获取前30个故事ID
                
                for story_id in story_ids[:5]:  # 只检查前5个
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_resp = requests.get(story_url, timeout=5)
                        if story_resp.status_code == 200:
                            story = story_resp.json()
                            title = story.get('title', '').lower()
                            # 检查是否包含AI相关关键词
                            ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 
                                         'deep learning', 'neural network', 'chatgpt', 'openai',
                                         'llm', 'gpt', 'claude', 'gemini']
                            if any(keyword in title for keyword in ai_keywords):
                                articles.append({
                                    'title': story.get('title', ''),
                                    'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                    'source': 'Hacker News',
                                    'category': 'AI',
                                    'time': datetime.now().isoformat()
                                })
                    except Exception as e:
                        logger.warning(f"获取故事 {story_id} 失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"获取Hacker News失败: {e}")
        
        # 方案2: 使用Reddit API获取r/MachineLearning和r/artificial的新闻
        try:
            reddit_urls = [
                "https://www.reddit.com/r/MachineLearning/top.json?limit=5",
                "https://www.reddit.com/r/artificial/top.json?limit=5"
            ]
            
            for url in reddit_urls:
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        for post in data.get('data', {}).get('children', [])[:3]:
                            post_data = post.get('data', {})
                            articles.append({
                                'title': post_data.get('title', ''),
                                'url': post_data.get('url', ''),
                                'source': 'Reddit',
                                'category': 'AI',
                                'time': datetime.now().isoformat()
                            })
                except Exception as e:
                    logger.warning(f"获取Reddit新闻失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"Reddit API错误: {e}")
        
        return articles
    
    def get_web3_news(self):
        """获取Web3相关新闻"""
        articles = []
        
        # 使用Reddit API获取Web3相关新闻
        try:
            reddit_urls = [
                "https://www.reddit.com/r/ethereum/top.json?limit=5",
                "https://www.reddit.com/r/CryptoCurrency/top.json?limit=5",
                "https://www.reddit.com/r/web3/top.json?limit=5"
            ]
            
            for url in reddit_urls:
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        for post in data.get('data', {}).get('children', [])[:2]:
                            post_data = post.get('data', {})
                            title = post_data.get('title', '').lower()
                            # 过滤Web3相关
                            web3_keywords = ['web3', 'blockchain', 'crypto', 'defi', 'nft', 
                                           'ethereum', 'bitcoin', 'smart contract', 'dao']
                            if any(keyword in title for keyword in web3_keywords):
                                articles.append({
                                    'title': post_data.get('title', ''),
                                    'url': post_data.get('url', ''),
                                    'source': 'Reddit',
                                    'category': 'Web3',
                                    'time': datetime.now().isoformat()
                                })
                except Exception as e:
                    logger.warning(f"获取Reddit Web3新闻失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"获取Web3新闻错误: {e}")
        
        return articles
    
    def save_news(self, articles):
        """保存新闻到文件，确保每日不超过10条"""
        if not articles:
            logger.info("没有新文章需要保存")
            return False
        
        # 读取今日已有文章
        existing_articles = []
        if self.today_file.exists():
            try:
                with open(self.today_file, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
            except Exception as e:
                logger.warning(f"读取今日文件失败: {e}")
        
        # 去重（基于标题）
        existing_titles = {article.get('title', '') for article in existing_articles}
        new_articles = [a for a in articles if a.get('title', '') not in existing_titles]
        
        # 限制每日总数不超过10条
        remaining_slots = self.max_articles_per_day - len(existing_articles)
        if remaining_slots <= 0:
            logger.info(f"今日已达到最大文章数限制({self.max_articles_per_day}条)")
            return False
        
        # 添加新文章
        articles_to_add = new_articles[:remaining_slots]
        existing_articles.extend(articles_to_add)
        
        # 保存到文件
        try:
            with open(self.today_file, 'w', encoding='utf-8') as f:
                json.dump(existing_articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存 {len(articles_to_add)} 条新文章，今日总计 {len(existing_articles)} 条")
            return len(articles_to_add) > 0
        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            return False


class RepositoryManager:
    """仓库管理器：自动创建GitHub和Gitee仓库"""
    
    def __init__(self, github_token, gitee_token):
        self.github_token = github_token
        self.gitee_token = gitee_token
        self.repo_name = "daily-news"  # 每日资讯的英文名称
        self.github_username = None
        self.gitee_username = None
        
    def get_github_username(self):
        """获取GitHub用户名"""
        if self.github_username:
            return self.github_username
        
        try:
            # 处理不同类型的token格式
            token = self.github_token.strip()
            
            # 尝试Bearer token方式（适用于Fine-grained tokens）
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.github_username = response.json().get('login', '')
                logger.info(f"✓ 获取GitHub用户名: {self.github_username}")
                return self.github_username
            elif response.status_code == 401:
                # Bearer方式失败，尝试token前缀（适用于classic tokens）
                logger.info("Bearer token认证失败，尝试token前缀方式...")
                headers['Authorization'] = f'token {token}'
                response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
                if response.status_code == 200:
                    self.github_username = response.json().get('login', '')
                    logger.info(f"✓ 获取GitHub用户名: {self.github_username}")
                    return self.github_username
                else:
                    logger.error(f"✗ 获取GitHub用户名失败 (状态码: {response.status_code})")
                    logger.error(f"错误信息: {response.text}")
                    if response.status_code == 403:
                        logger.error("提示: Token可能没有足够的权限或已过期")
                    return None
            elif response.status_code == 403:
                logger.error("✗ GitHub API 403错误 - Token权限不足")
                logger.error("请检查Token是否有 'read:user' 权限")
                return None
            else:
                logger.error(f"✗ 获取GitHub用户名失败 (状态码: {response.status_code})")
                logger.error(f"错误信息: {response.text}")
                return None
        except Exception as e:
            logger.error(f"获取GitHub用户名异常: {e}")
            return None
    
    def get_gitee_username(self):
        """获取Gitee用户名"""
        if self.gitee_username:
            return self.gitee_username
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
            }
            params = {'access_token': self.gitee_token}
            response = requests.get('https://gitee.com/api/v5/user', headers=headers, 
                                   params=params, timeout=10)
            if response.status_code == 200:
                self.gitee_username = response.json().get('login', '')
                logger.info(f"获取Gitee用户名: {self.gitee_username}")
                return self.gitee_username
            else:
                logger.error(f"获取Gitee用户名失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取Gitee用户名异常: {e}")
            return None
    
    def create_github_repo(self):
        """创建GitHub仓库"""
        if not self.github_token:
            logger.warning("GitHub token未提供，跳过GitHub仓库创建")
            return None
            
        username = self.get_github_username()
        if not username:
            logger.error("无法获取GitHub用户名，跳过创建仓库")
            logger.error("提示: 请检查GitHub token是否正确，是否有足够的权限")
            return None
        
        repo_url = f"https://github.com/{username}/{self.repo_name}.git"
        
        # 检查仓库是否已存在
        try:
            # 尝试Bearer token方式
            headers = {
                'Authorization': f'Bearer {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            check_url = f'https://api.github.com/repos/{username}/{self.repo_name}'
            response = requests.get(check_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ GitHub仓库已存在: {repo_url}")
                return repo_url
            elif response.status_code == 404:
                # 仓库不存在，创建新仓库
                logger.info(f"正在创建GitHub仓库: {self.repo_name} (用户: {username})")
                
                # 简化创建数据（某些字段可能导致403）
                create_data = {
                    'name': self.repo_name,
                    'description': 'Daily AI and Web3 News Collection - 每日AI和Web3资讯收集',
                    'private': False,
                    'auto_init': True  # 自动初始化仓库，创建README
                }
                create_url = 'https://api.github.com/user/repos'
                
                # 尝试Bearer token
                create_response = requests.post(create_url, headers=headers, 
                                               json=create_data, timeout=10)
                
                if create_response.status_code == 201:
                    logger.info(f"✓ 成功创建GitHub仓库: {repo_url}")
                    return repo_url
                elif create_response.status_code == 401:
                    # 认证失败，尝试token前缀
                    logger.info("Bearer token认证失败，尝试token前缀方式...")
                    headers['Authorization'] = f'token {self.github_token}'
                    create_response = requests.post(create_url, headers=headers, 
                                                   json=create_data, timeout=10)
                    if create_response.status_code == 201:
                        logger.info(f"✓ 成功创建GitHub仓库: {repo_url}")
                        return repo_url
                    else:
                        error_msg = create_response.text
                        logger.error(f"✗ 创建GitHub仓库失败 (状态码: {create_response.status_code})")
                        logger.error(f"错误信息: {error_msg}")
                        if "name already exists" in error_msg.lower():
                            logger.info("仓库可能已存在，尝试获取仓库URL...")
                            return repo_url
                        if create_response.status_code == 403:
                            logger.error("提示: Token可能没有 'repo' 权限")
                        return None
                else:
                    error_msg = create_response.text
                    logger.error(f"✗ 创建GitHub仓库失败 (状态码: {create_response.status_code})")
                    logger.error(f"错误信息: {error_msg}")
                    
                    # 详细处理403错误
                    if create_response.status_code == 403:
                        logger.error("=" * 50)
                        logger.error("GitHub 403 错误 - 权限不足")
                        logger.error("=" * 50)
                        logger.error("可能的原因：")
                        logger.error("1. Token权限不足 - 需要 'repo' 权限")
                        logger.error("2. Token已过期或被撤销")
                        logger.error("3. Token格式不正确")
                        logger.error("4. 仓库数量达到限制")
                        logger.error("")
                        logger.error("解决方案：")
                        logger.error("1. 检查Token权限：")
                        logger.error("   - 登录GitHub → Settings → Developer settings")
                        logger.error("   - Personal access tokens → Tokens (classic)")
                        logger.error("   - 确保勾选了 'repo' 权限")
                        logger.error("2. 如果使用Fine-grained token，需要：")
                        logger.error("   - 确保有 'Repository access' 权限")
                        logger.error("   - 确保有 'Contents' 和 'Metadata' 权限")
                        logger.error("3. 重新生成Token并更新config.json")
                        logger.error("=" * 50)
                        
                        # 尝试检查仓库是否已存在（可能只是创建失败，但仓库已存在）
                        try:
                            check_resp = requests.get(check_url, headers=headers, timeout=10)
                            if check_resp.status_code == 200:
                                logger.info(f"✓ 仓库实际上已存在: {repo_url}")
                                return repo_url
                        except:
                            pass
                    return None
            elif response.status_code == 401:
                # 认证失败，尝试token前缀
                logger.info("Bearer token认证失败，尝试token前缀方式检查仓库...")
                headers['Authorization'] = f'token {self.github_token}'
                response = requests.get(check_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✓ GitHub仓库已存在: {repo_url}")
                    return repo_url
                else:
                    logger.error(f"检查GitHub仓库状态失败: {response.status_code} - {response.text}")
                    return None
            else:
                logger.error(f"检查GitHub仓库状态失败: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"创建GitHub仓库网络异常: {e}")
            return None
        except Exception as e:
            logger.error(f"创建GitHub仓库异常: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def create_gitee_repo(self):
        """创建Gitee仓库"""
        username = self.get_gitee_username()
        if not username:
            logger.error("无法获取Gitee用户名，跳过创建仓库")
            return None
        
        repo_url = f"https://gitee.com/{username}/{self.repo_name}.git"
        
        # 检查仓库是否已存在
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            params = {'access_token': self.gitee_token}
            check_url = f'https://gitee.com/api/v5/repos/{username}/{self.repo_name}'
            response = requests.get(check_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Gitee仓库已存在: {repo_url}")
                return repo_url
            elif response.status_code == 404:
                # 仓库不存在，创建新仓库
                logger.info(f"正在创建Gitee仓库: {self.repo_name}")
                create_data = {
                    'name': self.repo_name,
                    'description': 'Daily AI and Web3 News Collection - 每日AI和Web3资讯收集',
                    'private': False,
                    'auto_init': False
                }
                create_url = 'https://gitee.com/api/v5/user/repos'
                create_params = {**params, **create_data}
                create_response = requests.post(create_url, headers=headers, 
                                              params=create_params, timeout=10)
                
                if create_response.status_code == 201:
                    logger.info(f"成功创建Gitee仓库: {repo_url}")
                    return repo_url
                else:
                    logger.error(f"创建Gitee仓库失败: {create_response.status_code} - {create_response.text}")
                    return None
            else:
                logger.error(f"检查Gitee仓库状态失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"创建Gitee仓库异常: {e}")
            return None
    
    def _map_gitee_to_github(self, gitee_url):
        """从Gitee URL映射到GitHub URL"""
        if not gitee_url:
            return None
        
        try:
            # 从Gitee URL提取用户名和仓库名
            # 格式: https://gitee.com/username/repo.git
            if 'gitee.com' in gitee_url:
                parts = gitee_url.replace('.git', '').split('gitee.com/')
                if len(parts) > 1:
                    repo_path = parts[1]
                    # 提取仓库名（可能是 username/repo 或直接是 repo）
                    if '/' in repo_path:
                        repo_name = repo_path.split('/')[-1]
                    else:
                        repo_name = repo_path
                    
                    # 获取GitHub用户名
                    github_username = self.get_github_username()
                    if github_username:
                        # 使用相同的仓库名，但使用GitHub用户名
                        github_url = f"https://github.com/{github_username}/{repo_name}.git"
                        logger.info(f"从Gitee URL映射到GitHub: {gitee_url} -> {github_url}")
                        return github_url
        except Exception as e:
            logger.debug(f"映射Gitee到GitHub失败: {e}")
        return None
    
    def _map_github_to_gitee(self, github_url):
        """从GitHub URL映射到Gitee URL"""
        if not github_url:
            return None
        
        try:
            # 从GitHub URL提取用户名和仓库名
            # 格式: https://github.com/username/repo.git
            if 'github.com' in github_url:
                parts = github_url.replace('.git', '').split('github.com/')
                if len(parts) > 1:
                    repo_path = parts[1]
                    # 获取Gitee用户名
                    gitee_username = self.get_gitee_username()
                    if gitee_username:
                        # 使用相同的仓库名，但使用Gitee用户名
                        gitee_url = f"https://gitee.com/{gitee_username}/{self.repo_name}.git"
                        logger.info(f"从GitHub URL映射到Gitee: {github_url} -> {gitee_url}")
                        return gitee_url
        except Exception as e:
            logger.debug(f"映射GitHub到Gitee失败: {e}")
        return None
    
    def ensure_repos_exist(self):
        """确保GitHub和Gitee仓库存在，如果不存在则创建"""
        github_url = None
        gitee_url = None
        
        logger.info("=" * 50)
        logger.info("开始检查并创建远程仓库...")
        
        # 优先创建Gitee仓库（如果提供了Gitee token）
        if self.gitee_token:
            logger.info("检查Gitee仓库...")
            gitee_url = self.create_gitee_repo()
            if gitee_url:
                logger.info(f"✓ Gitee仓库准备就绪: {gitee_url}")
            else:
                logger.warning("✗ Gitee仓库创建或检查失败")
        else:
            logger.warning("Gitee token未提供，跳过Gitee仓库检查")
        
        # 创建或映射GitHub仓库
        if self.github_token:
            logger.info("检查GitHub仓库...")
            github_url = self.create_github_repo()
            if github_url:
                logger.info(f"✓ GitHub仓库准备就绪: {github_url}")
            else:
                logger.warning("✗ GitHub仓库创建或检查失败")
                # 如果GitHub创建失败，尝试从Gitee映射
                if gitee_url:
                    logger.info("尝试从Gitee URL映射到GitHub...")
                    mapped_github_url = self._map_gitee_to_github(gitee_url)
                    if mapped_github_url:
                        github_url = mapped_github_url
                        logger.info(f"✓ 已映射GitHub仓库: {github_url}")
        else:
            logger.warning("GitHub token未提供，跳过GitHub仓库检查")
            # 如果没有GitHub token但有Gitee URL，尝试映射
            if gitee_url:
                logger.info("尝试从Gitee URL映射到GitHub...")
                mapped_github_url = self._map_gitee_to_github(gitee_url)
                if mapped_github_url:
                    github_url = mapped_github_url
                    logger.info(f"✓ 已映射GitHub仓库: {github_url}")
        
        # 如果GitHub存在但Gitee不存在，尝试映射
        if github_url and not gitee_url and self.gitee_token:
            logger.info("尝试从GitHub URL映射到Gitee...")
            mapped_gitee_url = self._map_github_to_gitee(github_url)
            if mapped_gitee_url:
                # 检查映射的Gitee仓库是否存在
                gitee_url = self.create_gitee_repo()
                if not gitee_url:
                    gitee_url = mapped_gitee_url
                    logger.info(f"✓ 已映射Gitee仓库: {gitee_url}")
        
        logger.info("=" * 50)
        return github_url, gitee_url


class GitManager:
    """Git和Gitee管理器（使用git命令）"""
    
    def __init__(self, github_token, gitee_token, config=None):
        self.github_token = github_token
        self.gitee_token = gitee_token
        self.repo_path = Path(".").absolute()
        
        # 配置选项（使用默认值）
        self.config = config or {}
        self.force_push = self.config.get('force_push', True)
        self.retry_count = self.config.get('retry_count', 3)
        self.timeout_seconds = self.config.get('timeout_seconds', 30)
        self.enable_gitee = self.config.get('enable_gitee', True)
        self.enable_github = self.config.get('enable_github', True)
        
        # 初始化仓库管理器
        self.repo_manager = RepositoryManager(github_token, gitee_token)
        
        # 确保远程仓库存在
        logger.info("正在检查并创建远程仓库...")
        github_url, gitee_url = self.repo_manager.ensure_repos_exist()
        
        # 初始化或获取本地Git仓库
        self._init_git_repo()
        
        # 配置远程仓库
        self._setup_remotes(github_url, gitee_url)
        
        logger.info(f"GitManager已初始化: {self.repo_path}")
        logger.info(f"配置: force_push={self.force_push}, retry_count={self.retry_count}, enable_github={self.enable_github}, enable_gitee={self.enable_gitee}")
    
    def _run_git(self, *args, check=True):
        """执行git命令"""
        cmd = ['git'] + list(args)
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=check,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # 对于某些错误（如远程已存在），不记录为错误
            error_msg = e.stderr.strip() if e.stderr else ""
            if "already exists" in error_msg.lower():
                # 远程已存在，这是正常情况，不记录为错误
                logger.debug(f"Git命令提示: {' '.join(cmd)} - {error_msg}")
            else:
                logger.error(f"Git命令失败: {' '.join(cmd)}")
                logger.error(f"错误: {error_msg}")
            if check:
                raise
            return None
    
    def _init_git_repo(self):
        """初始化Git仓库"""
        # 检查是否已经是Git仓库
        if not (self.repo_path / '.git').exists():
            logger.info("本地Git仓库不存在，正在初始化...")
            self._run_git('init', '-b', 'main')
            logger.info("成功初始化本地Git仓库（使用main分支）")
        else:
            logger.info(f"Git仓库已存在: {self.repo_path}")
            # 确保使用main分支
            self._ensure_main_branch()
    
    def _ensure_main_branch(self):
        """确保使用main分支"""
        try:
            # 获取当前分支
            current_branch = self._run_git('branch', '--show-current', check=False)
            if not current_branch:
                # 如果没有分支，创建初始提交
                logger.info("创建初始提交...")
                self._run_git('commit', '--allow-empty', '-m', 'Initial commit', check=False)
                current_branch = self._run_git('branch', '--show-current', check=False)
            
            if current_branch and current_branch != 'main':
                logger.info(f"当前分支是 {current_branch}，切换到main分支...")
                # 检查main分支是否存在
                branches = self._run_git('branch', '--list', 'main', check=False) or ""
                if 'main' in branches:
                    # 切换到main分支
                    self._run_git('checkout', 'main')
                    logger.info("已切换到main分支")
                else:
                    # main分支不存在，创建它
                    logger.info("创建main分支...")
                    self._run_git('checkout', '-b', 'main')
                    logger.info("已创建并切换到main分支")
            elif not current_branch or current_branch == 'main':
                logger.info("当前在main分支")
        except Exception as e:
            logger.debug(f"确保main分支: {e}")
    
    def _setup_remotes(self, github_url, gitee_url):
        """配置远程仓库"""
        # 配置GitHub远程仓库
        if github_url:
            try:
                # 检查origin远程是否存在
                remotes = self._run_git('remote', 'list', check=False) or ""
                if 'origin' in remotes:
                    # 检查URL是否相同
                    try:
                        current_url = self._run_git('remote', 'get-url', 'origin', check=False)
                        if current_url and current_url != github_url:
                            self._run_git('remote', 'set-url', 'origin', github_url)
                            logger.info(f"更新origin远程仓库URL: {github_url}")
                        else:
                            logger.info(f"origin远程仓库已配置: {github_url}")
                    except:
                        # 如果获取URL失败，尝试更新
                        self._run_git('remote', 'set-url', 'origin', github_url)
                        logger.info(f"更新origin远程仓库URL: {github_url}")
                else:
                    # 如果不存在，创建它
                    self._run_git('remote', 'add', 'origin', github_url)
                    logger.info(f"创建origin远程仓库: {github_url}")
            except Exception as e:
                logger.warning(f"配置GitHub远程仓库失败: {e}")
                # 如果添加失败，可能是已存在，尝试更新
                try:
                    self._run_git('remote', 'set-url', 'origin', github_url, check=False)
                    logger.info(f"已更新origin远程仓库URL: {github_url}")
                except:
                    logger.warning("将在推送时尝试重新创建")
        else:
            logger.warning("GitHub仓库URL为空，跳过origin远程仓库配置")
        
        # 配置Gitee远程仓库
        if gitee_url:
            try:
                # 准备带token的Gitee URL（避免每次推送时输入密码）
                gitee_url_with_token = self._prepare_push_url(gitee_url, self.gitee_token) if self.gitee_token else gitee_url
                
                # 检查gitee远程是否存在
                remotes = self._run_git('remote', 'list', check=False) or ""
                if 'gitee' in remotes:
                    # 检查URL是否相同
                    try:
                        current_url = self._run_git('remote', 'get-url', 'gitee', check=False)
                        if current_url and current_url != gitee_url_with_token:
                            self._run_git('remote', 'set-url', 'gitee', gitee_url_with_token)
                            logger.info(f"更新gitee远程仓库URL（已包含token）")
                        else:
                            logger.info(f"gitee远程仓库已配置（已包含token）")
                    except:
                        # 如果获取URL失败，尝试更新
                        self._run_git('remote', 'set-url', 'gitee', gitee_url_with_token, check=False)
                        logger.info(f"更新gitee远程仓库URL（已包含token）")
                else:
                    # 如果不存在，创建它（使用带token的URL）
                    try:
                        self._run_git('remote', 'add', 'gitee', gitee_url_with_token)
                        logger.info(f"创建gitee远程仓库（已包含token）")
                    except Exception as add_error:
                        # 如果添加失败（可能已存在但检查时没发现），尝试更新
                        error_str = str(add_error) if add_error else ""
                        if "already exists" in error_str.lower() or "exit status 3" in error_str:
                            logger.info("gitee远程仓库已存在，更新URL...")
                            self._run_git('remote', 'set-url', 'gitee', gitee_url_with_token, check=False)
                            logger.info(f"已更新gitee远程仓库URL（已包含token）")
                        else:
                            raise
            except Exception as e:
                logger.warning(f"配置Gitee远程仓库失败: {e}")
                # 如果添加失败，可能是已存在，尝试更新
                error_str = str(e) if e else ""
                if "already exists" in error_str.lower() or "exit status 3" in str(e):
                    try:
                        self._run_git('remote', 'set-url', 'gitee', gitee_url_with_token, check=False)
                        logger.info(f"已更新gitee远程仓库URL（已包含token）")
                    except:
                        logger.warning("Gitee远程仓库配置失败，将在推送时处理")
                else:
                    logger.warning("Gitee远程仓库配置失败，将在推送时处理")
    
    def _prepare_push_url(self, url, token):
        """准备带token的推送URL"""
        if not token:
            return url
        
        # 如果URL中已经有token，直接返回
        if '@' in url:
            return url
        
        # 处理HTTPS URL
        if url.startswith('https://'):
            # 提取域名和路径
            url_parts = url.replace('https://', '').split('/', 1)
            if len(url_parts) == 2:
                return f'https://{token}@{url_parts[0]}/{url_parts[1]}'
            else:
                return f'https://{token}@{url_parts[0]}'
        
        # 处理SSH URL (git@github.com:user/repo.git)
        if url.startswith('git@'):
            # SSH URL不需要token，直接返回
            return url
        
        return url
    
    def commit_and_push(self):
        """提交并推送到Git和Gitee（使用git命令）"""
        try:
            # 确保在main分支
            self._ensure_main_branch()
            
            # 检查是否有更改
            status_output = self._run_git('status', '--porcelain', check=False)
            has_changes = bool(status_output.strip())
            
            # 检查news_data目录是否有文件
            news_data_dir = Path("news_data")
            if news_data_dir.exists():
                news_files = list(news_data_dir.glob("*.json"))
                if news_files:
                    logger.info(f"发现 {len(news_files)} 个新闻数据文件")
            
            # 如果是空仓库，创建README文件作为初始提交
            try:
                # 检查是否有提交历史
                self._run_git('log', '--oneline', '-1', check=False)
                has_commits = True
            except:
                has_commits = False
            
            if not has_commits:
                # 空仓库，创建初始README
                logger.info("检测到空仓库，创建初始README文件...")
                readme_content = """# Daily News Collection

每日AI和Web3资讯自动收集仓库

## 说明

本仓库通过自动化程序每日收集AI和Web3相关的最新资讯，并自动更新。

## 新闻来源

- **AI新闻**: Hacker News, Reddit (r/MachineLearning, r/artificial)
- **Web3新闻**: Reddit (r/ethereum, r/CryptoCurrency, r/web3)

## 数据格式

新闻数据保存在 `news_data/` 目录下，按日期分类存储为JSON格式。

## 更新频率

每日自动更新，最多10条新闻。
"""
                readme_path = Path("README.md")
                if not readme_path.exists():
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(readme_content)
                    self._run_git('add', 'README.md')
                    self._run_git('commit', '-m', 'Initial commit: 初始化仓库')
                    logger.info("创建初始提交")
                    has_changes = True
            
            if has_changes or not has_commits:
                # 确保在main分支
                self._ensure_main_branch()
                
                # 添加所有更改（包括所有代码文件）
                self._run_git('add', '-A')
                logger.info("已添加所有更改到暂存区")
                
                # 检查暂存的文件
                staged_files = self._run_git('diff', '--cached', '--name-only', check=False)
                if staged_files:
                    files_list = staged_files.split('\n')
                    news_files = [f for f in files_list if 'news_data' in f]
                    code_files = [f for f in files_list if f.endswith(('.py', '.bat', '.md', '.txt', '.json')) and 'config.json' not in f]
                    logger.info(f"准备提交 {len(files_list)} 个文件")
                    if news_files:
                        logger.info(f"  - 新闻文件: {len(news_files)} 个")
                    if code_files:
                        logger.info(f"  - 代码文件: {len(code_files)} 个")
                
                # 创建提交
                commit_message = f"自动更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self._run_git('commit', '-m', commit_message)
                logger.info(f"✓ 创建提交: {commit_message}")
                
                # 推送到GitHub (origin)
                if self.enable_github:
                    self._push_to_github()
                else:
                    logger.info("GitHub推送已禁用")
                
                # 推送到Gitee
                if self.enable_gitee:
                    self._push_to_gitee()
                else:
                    logger.info("Gitee推送已禁用")
            else:
                logger.info("没有更改需要提交")
        except Exception as e:
            logger.error(f"Git操作失败: {e}")
    
    def _push_to_github(self):
        """推送到GitHub - 增强版本"""
        try:
            # 检查origin远程仓库是否存在
            remotes = self._run_git('remote', 'list', check=False) or ""
            if 'origin' not in remotes:
                logger.warning("origin远程仓库不存在，跳过GitHub推送")
                return
            
            original_url = self._run_git('remote', 'get-url', 'origin', check=False)
            if not original_url or 'github.com' not in original_url.lower():
                logger.warning(f"origin不是GitHub仓库，跳过: {original_url}")
                return
            
            logger.info(f"正在推送到GitHub: {original_url}")
            
            # 准备带token的URL（临时使用）
            push_url = original_url
            if self.github_token:
                push_url = self._prepare_push_url(original_url, self.github_token)
                if push_url != original_url:
                    self._run_git('remote', 'set-url', 'origin', push_url)
            
            # 尝试推送，支持重试
            for attempt in range(self.retry_count):
                try:
                    # 尝试推送到main分支
                    if self.force_push:
                        self._run_git('push', '-f', 'origin', 'main')
                        logger.info("✓ 成功强制推送到GitHub main分支")
                    else:
                        self._run_git('push', 'origin', 'main')
                        logger.info("✓ 成功推送到GitHub main分支")
                    break  # 成功，跳出重试循环
                    
                except subprocess.CalledProcessError as push_error:
                    if attempt < self.retry_count - 1:
                        logger.warning(f"GitHub推送失败，尝试重试 {attempt + 2}/{self.retry_count}...")
                        import time
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    
                    # 最后一次尝试，尝试master分支
                    try:
                        if self.force_push:
                            self._run_git('push', '-f', 'origin', 'master')
                            logger.info("✓ 成功强制推送到GitHub master分支")
                        else:
                            self._run_git('push', 'origin', 'master')
                            logger.info("✓ 成功推送到GitHub master分支")
                    except subprocess.CalledProcessError as master_error:
                        logger.error(f"GitHub推送失败（尝试{self.retry_count}次后）: {master_error}")
                        logger.error("提示: 可能需要手动处理分支冲突或检查Token权限")
                        raise
            
            # 恢复原始URL（避免在配置中保存token）
            if push_url != original_url:
                self._run_git('remote', 'set-url', 'origin', original_url)
                
        except Exception as e:
            logger.error(f"推送到GitHub失败: {e}")
    
    def _push_to_gitee(self):
        """推送到Gitee - 增强版本"""
        try:
            # 检查gitee远程仓库是否存在
            remotes = self._run_git('remote', 'list', check=False) or ""
            if 'gitee' not in remotes:
                logger.warning("gitee远程仓库不存在，跳过Gitee推送")
                return
            
            gitee_url = self._run_git('remote', 'get-url', 'gitee', check=False)
            if not gitee_url:
                logger.warning("无法获取gitee远程仓库URL")
                return
            
            logger.info("正在推送到Gitee...")
            
            # 确保URL中包含token
            if self.gitee_token and '@' not in gitee_url:
                push_url = self._prepare_push_url(gitee_url, self.gitee_token)
                if push_url != gitee_url:
                    self._run_git('remote', 'set-url', 'gitee', push_url)
                    gitee_url = push_url
            
            # 尝试推送，支持重试
            for attempt in range(self.retry_count):
                try:
                    # 尝试推送到main分支
                    if self.force_push:
                        self._run_git('push', '-f', 'gitee', 'main')
                        logger.info("✓ 成功强制推送到Gitee main分支")
                    else:
                        self._run_git('push', 'gitee', 'main')
                        logger.info("✓ 成功推送到Gitee main分支")
                    break  # 成功，跳出重试循环
                    
                except subprocess.CalledProcessError as push_error:
                    if attempt < self.retry_count - 1:
                        logger.warning(f"Gitee推送失败，尝试重试 {attempt + 2}/{self.retry_count}...")
                        import time
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    
                    # 最后一次尝试，尝试master分支
                    try:
                        if self.force_push:
                            self._run_git('push', '-f', 'gitee', 'master')
                            logger.info("✓ 成功强制推送到Gitee master分支")
                        else:
                            self._run_git('push', 'gitee', 'master')
                            logger.info("✓ 成功推送到Gitee master分支")
                    except subprocess.CalledProcessError as master_error:
                        logger.error(f"Gitee推送失败（尝试{self.retry_count}次后）: {master_error}")
                        raise
                    
        except Exception as e:
            logger.error(f"推送到Gitee失败: {e}")


def daily_task():
    """每日任务：收集新闻并提交"""
    logger.info("=" * 50)
    logger.info("开始执行每日任务")
    
    try:
        # 初始化新闻收集器
        collector = NewsCollector()
        
        # 获取新闻
        logger.info("正在获取AI新闻...")
        ai_articles = collector.get_ai_news()
        logger.info(f"获取到 {len(ai_articles)} 条AI新闻")
        
        logger.info("正在获取Web3新闻...")
        web3_articles = collector.get_web3_news()
        logger.info(f"获取到 {len(web3_articles)} 条Web3新闻")
        
        # 合并并保存
        all_articles = ai_articles + web3_articles
        has_new = collector.save_news(all_articles)
        
        # 读取配置
        config_file = Path("config.json")
        if not config_file.exists():
            logger.error("配置文件不存在，请先创建config.json")
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            github_token = config.get('github_token', '')
            gitee_token = config.get('gitee_token', '')
        
        # 初始化Git管理器（会自动创建仓库）
        try:
            logger.info("正在初始化Git管理器...")
            git_manager = GitManager(github_token, gitee_token, config)
            logger.info("Git管理器初始化成功")
        except Exception as e:
            logger.error(f"Git管理器初始化失败: {e}")
            logger.error("提示: 请检查Git令牌是否正确")
            return
        
        # 每次运行都提交和推送（确保内容同步）
        try:
            if has_new:
                logger.info("检测到新文章，正在提交到Git...")
            else:
                logger.info("未检测到新文章，但将检查并提交已有内容...")
            
            git_manager.commit_and_push()
            logger.info("✓ Git提交和推送完成")
        except Exception as e:
            logger.error(f"Git操作失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("每日任务完成")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"执行每日任务失败: {e}", exc_info=True)


def main():
    """主函数"""
    logger.info("程序启动")
    
    # 检查配置文件
    config_file = Path("config.json")
    if not config_file.exists():
        logger.error("配置文件不存在，请创建config.json文件")
        return
    
    # 设置定时任务：每天执行一次（默认早上9点）
    schedule.every().day.at("09:00").do(daily_task)
    
    # 也可以立即执行一次（用于测试）
    logger.info("立即执行一次任务（测试）...")
    daily_task()
    
    logger.info("程序运行中，等待定时任务...")
    logger.info("下次执行时间: 每天 09:00")
    
    # 保持程序运行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    main()

