#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复schedule模块安装问题
"""

import subprocess
import sys

def check_and_install_schedule():
    """检查并安装schedule模块"""
    try:
        # 首先检查是否有冲突的包
        try:
            import schedule
            # 检查是否是django-scheduler的schedule模块
            if hasattr(schedule, 'django') and not hasattr(schedule, 'every'):
                print("✗ 检测到django-scheduler冲突，正在卸载...")
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "django-scheduler"])
                # 重新导入
                import importlib
                import sys
                if 'schedule' in sys.modules:
                    del sys.modules['schedule']
                import schedule
        except ImportError:
            pass
        
        import schedule
        if hasattr(schedule, 'every'):
            print("✓ schedule模块已正确安装")
            return True
        else:
            print("✗ schedule模块缺少'every'属性")
            print("正在卸载冲突的包...")
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "django-scheduler"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("正在重新安装schedule模块...")
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "schedule"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
            # 再次检查
            import importlib
            import sys
            if 'schedule' in sys.modules:
                del sys.modules['schedule']
            import schedule
            if hasattr(schedule, 'every'):
                print("✓ schedule模块已重新安装并验证成功")
                return True
            else:
                print("✗ schedule模块仍然有问题")
                return False
    except ImportError:
        print("✗ schedule模块未安装")
        print("正在安装schedule模块...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
        # 再次检查
        import schedule
        if hasattr(schedule, 'every'):
            print("✓ schedule模块已安装并验证成功")
            return True
        else:
            print("✗ schedule模块安装后仍有问题")
            return False
    except Exception as e:
        print(f"✗ 检查schedule模块时出错: {e}")
        return False

if __name__ == "__main__":
    print("正在检查schedule模块...")
    if check_and_install_schedule():
        print("\n✓ 所有检查通过，可以运行auto_commit.py了")
        sys.exit(0)
    else:
        print("\n✗ 请手动运行: pip install schedule")
        sys.exit(1)

