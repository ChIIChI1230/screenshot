import argparse

from server import run_server
from client import run_client

def main():
    """命令行入口：

    使用 `--mode` 选择运行模式：
    - client：运行截图客户端
    - server：运行接收服务器
    """

    parser = argparse.ArgumentParser(description="Screenshot tool - client/server")
    parser.add_argument("--mode", choices=["client", "server"], required=True, help="Run as client or server")
    args = parser.parse_args()

    if args.mode == "server":
        run_server()
    else:
        run_client()


if __name__ == "__main__":
    main()
