#!/usr/bin/env python3
"""
命令行启动脚本

演示如何直接使用新的模块结构。
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from screenshot_tool.cli import main

if __name__ == "__main__":
    main()
