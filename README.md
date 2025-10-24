## 屏幕自动截图工具（客户端/服务器）

该项目包含两个组件：
- 客户端：按指定时间间隔截取主显示器屏幕，并通过 HTTP POST 上传到服务器。
- 服务器：接收并保存上传的截图，按日期自动归档。

### 特色功能

- **图形界面支持**：提供友好的GUI界面，无需命令行操作
- **实时监控**：实时查看运行状态和日志信息
- **智能存储**：自动管理本地存储和文件清理
- **网络容错**：支持离线存储，网络恢复后自动上传
- **灵活配置**：可视化配置各项参数，支持实时调整
- **工程化结构**：标准的Python项目结构，支持pip安装和命令行工具

### 安装依赖

本项目使用 Python 3.12+。

#### 开发模式

- 使用 uv（推荐）：

```bash
uv sync
```

- 或使用 pip：

```bash
pip install -e .
```

#### 安装模式

```bash
pip install .
```

安装后可以使用命令行工具：
```bash
screenshot-client    # 启动客户端GUI
screenshot-server    # 启动服务端GUI
screenshot-cli --mode client  # 命令行客户端
screenshot-cli --mode server  # 命令行服务端
```

#### 直接运行模式

如果不安装包，可以直接运行：

```bash
# 启动客户端GUI
python run_client_gui.py

# 启动服务端GUI
python run_server_gui.py

# 运行命令行版本
python run_cli.py --mode client
python run_cli.py --mode server
```

或者使用模块方式（需要设置PYTHONPATH）：

```bash
# 启动客户端GUI
PYTHONPATH=src python -m screenshot_tool.gui.client_gui

# 启动服务端GUI
PYTHONPATH=src python -m screenshot_tool.gui.server_gui

# 运行命令行版本
PYTHONPATH=src python -m screenshot_tool.cli --mode client
PYTHONPATH=src python -m screenshot_tool.cli --mode server
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

#### 命令行模式

1) 在接收端机器启动服务器：

```bash
python run_cli.py --mode server
```

2) 在发送端机器启动客户端：

```bash
python run_cli.py --mode client
```

#### GUI界面模式（推荐）

项目提供了友好的图形界面，让配置和使用更加简单：

**启动服务端GUI：**
```bash
python run_server_gui.py
```

**启动客户端GUI：**
```bash
python run_client_gui.py
```

##### 服务端GUI功能：
- **配置管理**：可视化配置主机地址、端口号和存储目录
- **服务控制**：一键启动/停止服务端
- **实时状态**：显示服务运行状态和连接信息
- **日志查看**：实时查看服务端运行日志
- **目录选择**：通过文件浏览器选择存储目录

##### 客户端GUI功能：
- **配置管理**：
  - 服务器地址设置
  - 截图间隔配置（秒）
  - 图片质量设置（1-100）
  - 本地副本保存选项
  - 本地输出目录选择
  - 本地存储目录配置
  - 最大本地文件数限制
  - 文件保留时间设置
- **运行控制**：一键启动/停止客户端
- **实时日志**：查看客户端运行状态和截图进度
- **配置保存**：保存当前配置到文件
- **本地存储管理**：自动管理本地图片存储和清理

##### GUI使用步骤：

1. **启动服务端**：
   - 运行 `python run_server_gui.py`
   - 配置主机地址（通常为 `0.0.0.0`）和端口号（如 `8000`）
   - 选择存储目录（截图保存位置）
   - 点击"启动服务端"按钮

2. **启动客户端**：
   - 运行 `python run_client_gui.py`
   - 配置服务器地址（如 `http://192.168.1.100:8000/upload`）
   - 设置截图间隔（建议 10-60 秒）
   - 调整图片质量（建议 80-95）
   - 选择是否保存本地副本
   - 配置本地存储目录和相关参数
   - 点击"启动客户端"按钮开始截图

3. **监控运行状态**：
   - 通过GUI界面的日志区域实时查看运行状态
   - 服务端会显示接收到的截图信息
   - 客户端会显示截图进度和上传状态

##### GUI优势：
- **用户友好**：无需记忆命令行参数
- **实时反馈**：直观显示运行状态和日志
- **配置简单**：可视化配置各项参数
- **错误提示**：友好的错误提示和验证
- **一键操作**：简单的启动/停止控制

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
- GUI界面需要图形桌面环境支持，在服务器环境或无桌面环境中请使用命令行模式。
- 首次使用建议通过GUI界面进行配置，配置会自动保存到 `config.json` 文件中。
- GUI界面的日志信息会实时更新，可以通过"清空日志"按钮清理历史日志。
- 客户端支持离线模式，当网络不可用时会在本地保存截图，网络恢复后自动上传。
- 服务端默认使用Waitress WSGI服务器，避免了Flask开发服务器的警告信息。
- 如需显示警告信息，可以设置环境变量 `SUPPRESS_FLASK_WARNINGS=false`。

