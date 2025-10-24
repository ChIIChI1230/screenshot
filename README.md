## 屏幕自动截图工具（客户端/服务器）

该项目包含两个组件：
- 客户端：按指定时间间隔截取主显示器屏幕，并通过 HTTP POST 上传到服务器。
- 服务器：接收并保存上传的截图，按日期自动归档。

### 安装依赖

本项目使用 Python 3.12+。

- 使用 uv（推荐）：

```bash
uv sync
```

- 或使用 pip（需要自行安装依赖）：

```bash
pip install pillow requests flask schedule waitress
```

### 配置

编辑根目录下的 `config.json`：

- `client.server_url`：上传接口地址，例如 `http://服务器IP:8000/upload`
- `client.interval_seconds`：截图间隔（秒）
- `client.image_format`：图片格式，支持 `JPEG`、`PNG`（推荐 JPEG）
- `client.jpeg_quality`：JPEG 质量 (1-95，越大越清晰体积越大)
- `client.save_local_copy`：是否在客户端本地保存副本
- `client.local_output_dir`：客户端本地保存目录
- `server.host` / `server.port`：服务器监听地址与端口
- `server.storage_dir`：服务器端保存目录

### 运行

1) 在接收端机器启动服务器：

```bash
uv run python -m waitress --host=0.0.0.0 --port=8000 server:app
```

1) 在发送端机器启动客户端：

```bash
python main.py --mode client
```
或者使用 uv：
```bash
uv run main.py --mode client
```

### 接口说明

服务器上传接口：`POST /upload`（multipart/form-data）

表单字段：
- `file`：图片二进制内容（建议 JPEG）
- `timestamp`：时间戳字符串（可选）
- `source`：来源主机名/客户端标识（可选）

返回：

```json
{ "status": "ok", "path": "保存路径" }
```

### 注意事项

- Windows 环境下，`PIL.ImageGrab` 需要在有桌面会话的环境中运行（非无头）。
- 当前默认仅截取主显示器，如需多显示器或区域截图，可在 `client.py` 中扩展。
- 生产环境建议在服务器前放置反向代理（如 Nginx）并增加认证/鉴权与传输加密（HTTPS）。

