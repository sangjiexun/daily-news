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
            # GitHub API支持token和Bearer两种方式
            headers = {
                'Authorization': f'Bearer {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            if response.status_code == 200:
                self.github_username = response.json().get('login', '')
                logger.info(f"获取GitHub用户名: {self.github_username}")
                return self.github_username
            else:
                # 尝试使用token前缀
                headers['Authorization'] = f'token {self.github_token}'
                response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
                if response.status_code == 200:
                    self.github_username = response.json().get('login', '')
                    logger.info(f"获取GitHub用户名: {self.github_username}")
                    return self.github_username
                else:
                    logger.error(f"获取GitHub用户名失败: {response.status_code} - {response.text}")
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
                create_data = {
                    'name': self.repo_name,
                    'description': 'Daily AI and Web3 News Collection - 每日AI和Web3资讯收集',
                    'private': False,
                    'auto_init': True,  # 自动初始化仓库，创建README
                    'has_issues': True,
                    'has_projects': False,
                    'has_wiki': False,
                    'default_branch': 'master'  # 使用master作为默认分支
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
                        return None
                else:
                    error_msg = create_response.text
                    logger.error(f"✗ 创建GitHub仓库失败 (状态码: {create_response.status_code})")
                    logger.error(f"错误信息: {error_msg}")
                    # 如果是403，可能是权限问题
                    if create_response.status_code == 403:
                        logger.error("提示: GitHub token可能没有创建仓库的权限，请检查token权限设置")
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
    
    def ensure_repos_exist(self):
        """确保GitHub和Gitee仓库存在，如果不存在则创建"""
        github_url = None
        gitee_url = None
        
        logger.info("=" * 50)
        logger.info("开始检查并创建远程仓库...")
        
        if self.github_token:
            logger.info("检查GitHub仓库...")
            github_url = self.create_github_repo()
            if github_url:
                logger.info(f"✓ GitHub仓库准备就绪: {github_url}")
            else:
                logger.warning("✗ GitHub仓库创建或检查失败")
        else:
            logger.warning("GitHub token未提供，跳过GitHub仓库检查")
        
        if self.gitee_token:
            logger.info("检查Gitee仓库...")
            gitee_url = self.create_gitee_repo()
            if gitee_url:
                logger.info(f"✓ Gitee仓库准备就绪: {gitee_url}")
            else:
                logger.warning("✗ Gitee仓库创建或检查失败")
        else:
            logger.warning("Gitee token未提供，跳过Gitee仓库检查")
        
        logger.info("=" * 50)
        return github_url, gitee_url


class GitManager:
    """Git和Gitee管理器（使用git命令）"""
    
    def __init__(self, github_token, gitee_token):
        self.github_token = github_token
        self.gitee_token = gitee_token
        self.repo_path = Path(".").absolute()
        
        # 初始化仓库管理器
        self.repo_manager = RepositoryManager(github_token, gitee_token)
        
        # 确保远程仓库存在
        logger.info("正在检查并创建远程仓库...")
        github_url, gitee_url = self.repo_manager.ensure_repos_exist()
        
        # 初始化或获取本地Git仓库
        self._init_git_repo()
        
        # 配置远程仓库
        self._setup_remotes(github_url, gitee_url)
    
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
            logger.error(f"Git命令失败: {' '.join(cmd)}")
            logger.error(f"错误: {e.stderr}")
            if check:
                raise
            return None
    
    def _init_git_repo(self):
        """初始化Git仓库"""
        # 检查是否已经是Git仓库
        if not (self.repo_path / '.git').exists():
            logger.info("本地Git仓库不存在，正在初始化...")
            self._run_git('init', '-b', 'master')
            logger.info("成功初始化本地Git仓库（使用master分支）")
        else:
            logger.info(f"Git仓库已存在: {self.repo_path}")
            # 确保使用master分支
            self._ensure_master_branch()
    
    def _ensure_master_branch(self):
        """确保使用master分支"""
        try:
            # 获取当前分支
            current_branch = self._run_git('branch', '--show-current', check=False)
            if not current_branch:
                # 如果没有分支，创建初始提交
                logger.info("创建初始提交...")
                self._run_git('commit', '--allow-empty', '-m', 'Initial commit', check=False)
                current_branch = self._run_git('branch', '--show-current', check=False)
            
            if current_branch and current_branch != 'master':
                logger.info(f"当前分支是 {current_branch}，切换到master分支...")
                # 检查master分支是否存在
                branches = self._run_git('branch', '--list', 'master', check=False)
                if 'master' in branches:
                    # 切换到master分支
                    self._run_git('checkout', 'master')
                    logger.info("已切换到master分支")
                else:
                    # master分支不存在，创建它
                    logger.info("创建master分支...")
                    self._run_git('checkout', '-b', 'master')
                    logger.info("已创建并切换到master分支")
            elif not current_branch or current_branch == 'master':
                logger.info("当前在master分支")
        except Exception as e:
            logger.debug(f"确保master分支: {e}")
    
    def _setup_remotes(self, github_url, gitee_url):
        """配置远程仓库"""
        # 配置GitHub远程仓库
        if github_url:
            try:
                # 检查origin远程是否存在
                remotes = self._run_git('remote', 'list', check=False)
                if 'origin' in remotes:
                    # 检查URL是否相同
                    current_url = self._run_git('remote', 'get-url', 'origin', check=False)
                    if current_url != github_url:
                        self._run_git('remote', 'set-url', 'origin', github_url)
                        logger.info(f"更新origin远程仓库URL: {github_url}")
                    else:
                        logger.info(f"origin远程仓库已配置: {github_url}")
                else:
                    # 如果不存在，创建它
                    self._run_git('remote', 'add', 'origin', github_url)
                    logger.info(f"创建origin远程仓库: {github_url}")
            except Exception as e:
                logger.warning(f"配置GitHub远程仓库失败: {e}")
                logger.warning("将在推送时尝试重新创建")
        else:
            logger.warning("GitHub仓库URL为空，跳过origin远程仓库配置")
        
        # 配置Gitee远程仓库
        if gitee_url:
            try:
                # 准备带token的Gitee URL（避免每次推送时输入密码）
                gitee_url_with_token = self._prepare_push_url(gitee_url, self.gitee_token) if self.gitee_token else gitee_url
                
                # 检查gitee远程是否存在
                remotes = self._run_git('remote', 'list', check=False)
                if 'gitee' in remotes:
                    # 检查URL是否相同
                    current_url = self._run_git('remote', 'get-url', 'gitee', check=False)
                    if current_url != gitee_url_with_token:
                        self._run_git('remote', 'set-url', 'gitee', gitee_url_with_token)
                        logger.info(f"更新gitee远程仓库URL（已包含token）")
                    else:
                        logger.info(f"gitee远程仓库已配置（已包含token）")
                else:
                    # 如果不存在，创建它（使用带token的URL）
                    self._run_git('remote', 'add', 'gitee', gitee_url_with_token)
                    logger.info(f"创建gitee远程仓库（已包含token）")
            except Exception as e:
                logger.warning(f"配置Gitee远程仓库失败: {e}")
    
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
            # 确保在master分支
            self._ensure_master_branch()
            
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
                try:
                    # 检查origin远程仓库是否存在
                    remotes = self._run_git('remote', 'list', check=False)
                    if 'origin' not in remotes:
                        # origin不存在，尝试重新创建
                        logger.warning("origin远程仓库不存在，尝试重新创建...")
                        github_url, _ = self.repo_manager.ensure_repos_exist()
                        if github_url:
                            self._run_git('remote', 'add', 'origin', github_url)
                            logger.info(f"创建origin远程仓库: {github_url}")
                        else:
                            logger.error("无法获取GitHub仓库URL，跳过GitHub推送")
                            raise Exception("GitHub仓库URL不可用")
                    
                    original_url = self._run_git('remote', 'get-url', 'origin', check=False)
                    logger.info(f"找到origin远程仓库: {original_url}")
                    
                    # 判断是否是GitHub仓库
                    is_github = 'github.com' in original_url.lower()
                    
                    if is_github and self.github_token:
                        # 准备带token的URL
                        push_url = self._prepare_push_url(original_url, self.github_token)
                        if push_url != original_url:
                            self._run_git('remote', 'set-url', 'origin', push_url)
                        
                        # 确保使用master分支
                        self._ensure_master_branch()
                        
                        # 首次推送前，检查远程分支并拉取合并
                        try:
                            # 获取远程分支信息
                            self._run_git('fetch', 'origin', check=False)
                            remote_branches = self._run_git('branch', '-r', check=False)
                            
                            has_main = 'origin/main' in remote_branches
                            has_master = 'origin/master' in remote_branches
                            
                            if remote_branches:
                                logger.info(f"检测到远程仓库有内容 (main: {has_main}, master: {has_master})")
                                # 如果远程是main分支，我们需要拉取并合并
                                if has_main:
                                    logger.info("远程使用main分支，正在拉取并合并到本地master分支...")
                                    try:
                                        self._run_git('fetch', 'origin', 'main', check=False)
                                        self._run_git('merge', 'origin/main', '--allow-unrelated-histories', '--no-edit', check=False)
                                        logger.info("✓ 已合并远程main分支内容到本地master分支")
                                    except Exception as merge_error:
                                        logger.warning(f"合并远程main分支失败: {merge_error}")
                                elif has_master:
                                    # 远程有master分支，正常拉取
                                    try:
                                        self._run_git('pull', 'origin', 'master', '--allow-unrelated-histories', '--no-edit', check=False)
                                        logger.info("✓ 已拉取远程master分支内容")
                                    except:
                                        logger.warning("拉取远程master分支失败，继续推送")
                        except Exception as fetch_error:
                            logger.debug(f"检查远程内容: {fetch_error}")
                        
                        # 推送到master分支
                        logger.info("正在推送到GitHub master分支...")
                        try:
                            self._run_git('push', '-u', 'origin', 'master')
                            logger.info("✓ 成功推送到GitHub (master分支)")
                        except Exception as push_error:
                            # 如果推送失败，可能是远程只有main分支
                            logger.warning(f"推送到master分支失败，尝试推送到main分支...")
                            try:
                                self._run_git('push', '-u', 'origin', 'main')
                                logger.info("✓ 成功推送到GitHub (main分支)")
                            except Exception as push_main_error:
                                # 如果main也失败，尝试强制推送到master
                                logger.warning(f"推送到main分支也失败，尝试强制推送...")
                                try:
                                    self._run_git('push', '-f', 'origin', 'master')
                                    logger.info("✓ 使用强制推送完成 (master分支)")
                                except Exception as force_error:
                                    logger.error(f"所有推送方式都失败: {force_error}")
                        
                        # 恢复原始URL（避免在配置中保存token）
                        if push_url != original_url:
                            self._run_git('remote', 'set-url', 'origin', original_url)
                    elif is_github:
                        # 没有token，尝试直接推送
                        self._run_git('push', 'origin', 'master', check=False)
                        logger.info("✓ 成功推送到GitHub（使用已保存的凭据）")
                    else:
                        logger.warning(f"origin远程仓库不是GitHub，跳过GitHub推送: {original_url}")
                except Exception as e:
                    logger.error(f"推送到GitHub失败: {e}")
                
                # 推送到Gitee
                try:
                    remotes = self._run_git('remote', 'list', check=False)
                    if 'gitee' not in remotes:
                        # 如果没有gitee远程，尝试从origin推断
                        try:
                            origin_url = self._run_git('remote', 'get-url', 'origin', check=False)
                            # 如果是GitHub URL，尝试转换为Gitee URL
                            if 'github.com' in origin_url.lower():
                                # 提取用户名和仓库名
                                parts = origin_url.replace('.git', '').split('github.com/')
                                if len(parts) > 1:
                                    repo_path = parts[1]
                                    gitee_url = f'https://gitee.com/{repo_path}.git'
                                    # 准备带token的URL
                                    gitee_url_with_token = self._prepare_push_url(gitee_url, self.gitee_token) if self.gitee_token else gitee_url
                                    self._run_git('remote', 'add', 'gitee', gitee_url_with_token)
                                    logger.info(f"自动创建gitee远程仓库（已包含token）")
                            else:
                                logger.info("未找到gitee远程仓库，且无法从origin推断，跳过Gitee推送")
                                return
                        except:
                            logger.info("无法获取origin URL，跳过Gitee推送")
                            return
                    
                    # 确保URL中包含token
                    current_url = self._run_git('remote', 'get-url', 'gitee', check=False)
                    if self.gitee_token and '@' not in current_url:
                        push_url = self._prepare_push_url(current_url, self.gitee_token)
                        self._run_git('remote', 'set-url', 'gitee', push_url)
                        logger.debug("Gitee URL已更新为包含token的版本")
                    
                    # 推送到Gitee
                    try:
                        self._run_git('push', '-u', 'gitee', 'master')
                        logger.info("✓ 成功推送到Gitee")
                    except Exception as push_error:
                        # 如果设置上游失败，尝试直接推送
                        try:
                            self._run_git('push', 'gitee', 'master', check=False)
                            logger.info("✓ 成功推送到Gitee")
                        except:
                            logger.warning("推送到Gitee失败")
                except Exception as e:
                    logger.error(f"推送到Gitee失败: {e}")
            else:
                logger.info("没有更改需要提交")
        except Exception as e:
            logger.error(f"Git操作失败: {e}")


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
            git_manager = GitManager(github_token, gitee_token)
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

