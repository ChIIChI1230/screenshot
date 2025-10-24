"""
命令行入口点

提供命令行接口来运行截图工具。
"""

import argparse
import sys

from .core.client import run_client
from .core.server import run_server


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="Screenshot tool - client/server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode client     # 运行客户端
  %(prog)s --mode server     # 运行服务端
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["client", "server"], 
        required=True, 
        help="Run as client or server"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "server":
            run_server()
        else:
            run_client()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
