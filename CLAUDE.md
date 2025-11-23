# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

TrendRadar 是一个全网热点新闻聚合工具，支持从11+主流平台抓取热点内容，通过智能算法重新排序，并支持多种推送方式。项目基于 Python 3.10+ 开发，集成了基于 MCP (Model Context Protocol) 的 AI 分析功能。

## 核心架构

### 主要模块结构
- **main.py**: 主程序入口（约17.4万行代码），包含完整的爬虫、数据处理、推送逻辑
- **config/**: 配置文件目录
  - `config.yaml`: 主配置文件，控制所有运行参数
  - `frequency_words.txt`: 关键词过滤配置
- **mcp_server/**: MCP AI分析服务器
  - `server.py`: MCP服务器主文件，提供13种智能分析工具
  - `services/`: 业务逻辑层（分析、查询、搜索、系统管理）
  - `tools/`: 工具模块（缓存、数据、解析服务）
- **output/**: 新闻数据输出目录，按日期组织存储
- **docker/**: Docker部署相关文件

### 技术栈
- **核心语言**: Python 3.10+
- **配置管理**: YAML格式配置文件
- **MCP协议**: FastMCP 2.0实现AI分析功能
- **依赖库**: requests, pytz, PyYAML, fastmcp, websockets
- **部署方式**: GitHub Actions, Docker, 本地运行

## 常用开发命令

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 运行主程序
python main.py

# 启动MCP HTTP服务器（用于AI分析功能）
./start-http.sh

# 启动MCP STDIO模式
uv run python -m mcp_server.server
```

### Docker部署
```bash
# 快速启动
docker run -d --name trend-radar \
  -v ./config:/app/config:ro \
  -v ./output:/app/output \
  -e FEISHU_WEBHOOK_URL="your-webhook" \
  wantcat/trendradar:latest

# 使用docker-compose
cd docker
docker-compose up -d

# 查看容器状态
docker logs -f trend-radar
```

### 测试和调试
```bash
# 测试MCP服务器连接
npx @modelcontextprotocol/inspector

# 验证配置文件
python -c "import yaml; print(yaml.safe_load(open('config/config.yaml')))"

# 手动触发GitHub Actions
# 在仓库页面: Actions -> Hot News Crawler -> Run workflow
```

## 核心配置说明

### 推送模式选择（config/config.yaml）
- **daily**: 当日汇总模式 - 按时推送当日所有匹配新闻
- **incremental**: 增量监控模式 - 仅推送新增内容，零重复
- **current**: 当前榜单模式 - 按时推送当前榜单匹配新闻

### 关键词配置（config/frequency_words.txt）
支持三种语法：
- 普通词: `华为` (包含任意一个即可)
- 必须词: `+手机` (必须同时包含)
- 过滤词: `!广告` (包含则排除)

用空行分隔不同词组，每个词组独立统计。

### 权重算法配置
```yaml
weight:
  rank_weight: 0.6      # 排名权重（看重排名高的新闻）
  frequency_weight: 0.3  # 频次权重（关注持续出现的话题）
  hotness_weight: 0.1    # 热度权重（考虑排名质量）
```

## 重要提醒

### 安全注意事项
- **绝不要在config.yaml中填写webhooks**，特别是当部署在GitHub上时
- **所有敏感配置应通过GitHub Secrets或环境变量管理**
- webhook URL暴露会导致垃圾信息推送甚至安全风险

### 开发最佳实践
- 修改配置后建议先本地测试验证
- 使用Docker部署时注意数据持久化路径映射
- MCP功能需要本地新闻数据支持，确保output目录有数据
- 关键词配置建议从宽泛到精确逐步调整

### 故障排查
1. **推送失败**: 检查webhook配置和GitHub Secrets设置
2. **爬虫异常**: 验证newsnow API服务状态
3. **MCP连接问题**: 确认端口3333未被占用，依赖已安装
4. **配置不生效**: Docker环境下检查环境变量覆盖机制

## MCP AI分析功能

项目集成了13种AI分析工具，支持：
- **基础查询**: 获取最新新闻、按日期查询、热点话题
- **智能检索**: 搜索新闻、历史关联搜索
- **高级分析**: 话题趋势分析、数据洞察、情感分析
- **系统管理**: 配置查看、系统状态、手动触发爬虫

### MCP客户端配置示例
```json
{
  "mcpServers": {
    "trendradar": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/TrendRadar",
        "run",
        "python",
        "-m",
        "mcp_server.server"
      ]
    }
  }
}
```

## 部署方式对比

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| GitHub Actions | 零配置、自动化 | 执行时间不固定 | 快速体验、个人使用 |
| Docker本地部署 | 时间可控、数据私密 | 需要维护服务器 | 长期使用、企业部署 |
| 本地运行 | 调试方便、完全控制 | 需要Python环境 | 开发测试、定制需求 |

## 版本更新机制

- 项目通过版本检查URL自动检测更新
- 大版本升级建议重新Fork项目
- 小版本更新可替换main.py文件
- 配置文件格式可能随版本变化，升级时注意兼容性

## 相关链接

- 官方仓库: https://github.com/sansan0/TrendRadar
- 新闻数据源: https://github.com/ourongxing/newsnow
- MCP协议: https://modelcontextprotocol.io/
- Docker镜像: wantcat/trendradar:latest