# 项目结构说明

## 📁 新的工程化项目结构

本项目已重构为标准的Python工程化项目结构，遵循现代Python开发最佳实践。

### 🏗️ 目录结构

```
screenshot/
├── src/                          # 源代码目录
│   └── screenshot_tool/          # 主包目录
│       ├── __init__.py           # 包初始化文件
│       ├── cli.py                # 命令行接口
│       ├── core/                 # 核心功能模块
│       │   ├── __init__.py
│       │   ├── client.py         # 客户端核心逻辑
│       │   ├── server.py         # 服务端核心逻辑
│       │   └── config.py         # 配置管理
│       ├── gui/                  # GUI界面模块
│       │   ├── __init__.py
│       │   ├── client_gui.py     # 客户端GUI
│       │   ├── server_gui.py     # 服务端GUI
│       │   └── gui_utils.py      # GUI工具类
│       └── utils/                # 工具模块
│           ├── __init__.py
│           ├── logger.py         # 日志管理
│           ├── file_utils.py     # 文件工具
│           └── network_utils.py  # 网络工具
├── release/                      # 发布包目录
├── pyproject.toml               # 项目配置文件
├── README.md                    # 项目说明文档
├── run_client_gui.py           # 客户端GUI启动脚本
├── run_server_gui.py           # 服务端GUI启动脚本
└── run_cli.py                  # 命令行启动脚本
```

### 🔧 模块说明

#### 核心模块 (`core/`)
- **`client.py`**: 截图客户端核心逻辑
  - `ScreenshotClient`: 客户端主类
  - `LocalImageStorage`: 本地图片存储管理
  - 截图、上传、本地存储等功能

- **`server.py`**: 截图服务端核心逻辑
  - `ScreenshotServer`: 服务端主类
  - HTTP服务器、文件接收、存储管理

- **`config.py`**: 配置管理
  - `ConfigManager`: 配置管理器
  - `ClientConfig`: 客户端配置类
  - `ServerConfig`: 服务端配置类

#### GUI模块 (`gui/`)
- **`client_gui.py`**: 客户端图形界面
- **`server_gui.py`**: 服务端图形界面
- **`gui_utils.py`**: GUI通用工具类

#### 工具模块 (`utils/`)
- **`logger.py`**: 日志管理工具
- **`file_utils.py`**: 文件操作工具
- **`network_utils.py`**: 网络工具

### 🚀 使用方式

#### 1. 开发模式
```bash
# 安装依赖
uv sync

# 运行客户端GUI
python run_client_gui.py

# 运行服务端GUI
python run_server_gui.py

# 运行命令行版本
python run_cli.py --mode client
python run_cli.py --mode server
```

#### 2. 安装模式
```bash
# 安装包
pip install -e .

# 使用命令行工具
screenshot-client    # 启动客户端GUI
screenshot-server    # 启动服务端GUI
screenshot-cli --mode client  # 命令行客户端
screenshot-cli --mode server  # 命令行服务端
```

### 📦 项目配置

#### `pyproject.toml`
- 项目元数据配置
- 依赖管理
- 入口点定义
- 构建系统配置

#### 入口点
- `screenshot-client`: 客户端GUI
- `screenshot-server`: 服务端GUI
- `screenshot-cli`: 命令行工具

### 🎯 直接使用新结构

项目采用标准的Python包结构，所有功能都通过启动脚本访问：
- 使用 `python run_cli.py` 运行命令行版本
- 使用 `python run_client_gui.py` 运行客户端GUI
- 使用 `python run_server_gui.py` 运行服务端GUI

### 🧪 测试

运行结构测试脚本验证项目结构：
```bash
python test_structure.py
```

### 📋 优势

1. **模块化设计**: 清晰的模块分离，便于维护和扩展
2. **标准化结构**: 符合Python项目最佳实践
3. **可安装性**: 支持pip安装和命令行工具
4. **向后兼容**: 保持原有使用方式不变
5. **易于扩展**: 模块化设计便于添加新功能
6. **类型提示**: 完整的类型注解支持
7. **文档完善**: 详细的模块和函数文档

### 🔧 开发指南

1. **添加新功能**: 在相应的模块中添加功能
2. **修改配置**: 在`core/config.py`中修改配置类
3. **添加工具**: 在`utils/`目录中添加工具函数
4. **GUI扩展**: 在`gui/`目录中扩展界面功能
5. **测试**: 运行`test_structure.py`验证修改

这个新的项目结构为项目的长期维护和扩展提供了坚实的基础。
