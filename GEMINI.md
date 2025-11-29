# TrendRadar 项目指南

TrendRadar 是一个全网热点新闻聚合与趋势分析工具，旨在从 11+ 个主流平台（如微博、知乎、抖音等）抓取热点内容，通过智能算法重新排序，并通过多种渠道（微信、飞书、Telegram 等）进行推送。该项目近期集成了一个基于 **Model Context Protocol (MCP)** 的服务，允许 AI 助手对本地新闻数据进行自然语言分析。

## 项目概述

*   **核心功能**: 实时爬取、关键词过滤、热度重排序、多渠道通知。
*   **AI 能力**: 内置 MCP 服务器，允许 AI 助手（如 Claude, Cursor, Cherry Studio）查询、搜索和分析已收集的新闻数据。
*   **开发语言**: Python 3.10+
*   **架构**: 混合架构，包含单体爬虫脚本 (`main.py`) 和模块化的 MCP 服务器 (`mcp_server/`)。

## 目录结构

```text
TrendRadar/
├── main.py                 # 核心爬虫与通知引擎（单体脚本，约 4800+ 行）
├── mcp_server/             # MCP 服务器实现（模块化包）
│   ├── server.py           # FastMCP 入口点
│   ├── tools/              # 工具定义 (数据查询, 分析, 搜索)
│   └── services/           # AI 工具的业务逻辑
├── config/                 # 配置文件
│   ├── config.yaml         # 主配置 (API 密钥, 权重, 运行模式)
│   └── frequency_words.txt # 关键词过滤规则
├── output/                 # 本地数据存储 (YYYY年MM月DD日/txt/) - MCP 功能的核心数据源
├── docker/                 # Docker 部署相关文件
├── setup-mac.sh            # 使用 'uv' 包管理器的安装脚本
└── start-http.sh           # 以 HTTP 模式启动 MCP 服务器的脚本
```

## 构建与运行

### 1. 环境设置
项目推荐使用 `uv` 进行快速依赖管理，同时也支持标准的 `pip`。

**使用 `uv` (推荐):**
```bash
# 安装 uv (如果未安装) 并同步依赖
./setup-mac.sh
```

**使用 `pip`:**
```bash
pip install -r requirements.txt
```

### 2. 运行爬虫 (核心功能)
执行主逻辑：抓取新闻、处理规则并发送通知。
```bash
python main.py
```

### 3. 运行 MCP 服务器 (AI 分析)
MCP 服务器将本地数据暴露给 AI 工具使用。

**STDIO 模式 (适用于 Claude Desktop/Cherry Studio):**
```bash
uv run python -m mcp_server.server
```

**HTTP 模式 (适用于 Cursor/远程访问):**
```bash
./start-http.sh
# 服务器将监听 http://0.0.0.0:3333/mcp
```

### 4. Docker 部署
包含爬虫和可选服务的全栈部署。
```bash
cd docker
docker-compose up -d
```

## 配置说明

- **`config/config.yaml`**: 控制平台选择、推送渠道（飞书、钉钉、Telegram）和调度。
    - *注意:* 环境变量（如 `FEISHU_WEBHOOK_URL`）会覆盖这些设置。
- **`config/frequency_words.txt`**: 定义要追踪的新闻。
    - `关键词`: 简单匹配。
    - `+关键词`: 必须包含。
    - `!关键词`: 排除。
    - `@数量`: 限制结果数量。

## 开发规范

- **数据持久化**: `output/` 目录是 MCP 服务器的事实来源。如果你打算使用 AI 分析功能，请勿删除历史数据。
- **模块化**: 新功能应理想地放置在 `mcp_server` 包结构中，而不是继续扩展已经很大的 `main.py`。
- **MCP 工具**: 工具在 `mcp_server/server.py` 中使用 `@mcp.tool` 装饰器注册，并在 `mcp_server/tools/` 中实现。
- **版本控制**: 项目版本在 `main.py` (`VERSION`) 和 `pyproject.toml` 中跟踪。
