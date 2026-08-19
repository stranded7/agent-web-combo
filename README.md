# Agent Web Combo

一个面向 AI Agent 的联网工具组合：**搜索发现 + 内容提取 + Kitesurf/Playwright 渲染 + agent-reach 平台读取**。

- 搜索：Tavily / Exa / AnySearch
- 渲染：Cloudflare Kitesurf + Playwright（CDP）
- 平台内容：agent-reach（可选）
- 接入方式：CLI 和 MCP Server

## 功能

- 多搜索源切换：`tavily` / `exa` / `anysearch`
- 搜索结果的页面内容提取
- Kitesurf 渲染页面、提取正文、截图
- 完整流水线：搜索 → 提取 → 渲染 → 截图
- MCP Server：Claude Code / Cursor / OpenCode / DSH Desktop 等可直接调用

## 架构

```text
搜索发现：Tavily / Exa / AnySearch
        ↓
内容提取：AnySearch extract / Tavily Extract / Exa Contents
        ↓
需要渲染/截图/JS：Kitesurf + Playwright (connectOverCDP)
        ↓
平台类内容/登录态：agent-reach (可选)
```

## 项目结构

```text
agent-web-combo/
├── combo/
│   ├── __main__.py       # CLI 入口
│   ├── cli.py            # 命令行
│   ├── config.py         # 环境变量配置
│   ├── search.py         # Tavily / Exa / AnySearch
│   ├── kitesurf.py       # Kitesurf + Playwright
│   ├── agent_reach.py    # agent-reach CLI
│   └── pipeline.py       # 组合流水线
├── combo_mcp.py          # MCP Server 入口
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## 安装

```bash
pip install -r requirements.txt
playwright install chromium  # 仅本地调试/备选浏览器时需要；连 Kitesurf 不需要
```

## 配置

```bash
cp .env.example .env
```

按需填写：

```bash
# Cloudflare / Kitesurf（需要 Browser Run 权限）
CF_ACCOUNT_ID=你的账号ID
CF_API_TOKEN=你的API Token

# 搜索源（至少一个；AnySearch 可不填 Key）
TAVILY_API_KEY=tvly-xxx
EXA_API_KEY=xxx
ANYSEARCH_API_KEY=as_sk_xxx
```

> `.env` 已被 `.gitignore` 忽略，请勿提交。

## CLI 使用

```bash
# 搜索
python -m combo search "Cloudflare Kitesurf" --provider anysearch --max-results 5

# 渲染单个页面 + 截图
python -m combo render "https://example.com" --screenshot output.png

# 完整流水线
python -m combo research "Kitesurf vs Tavily" \
  --provider auto \
  --max-results 5 \
  --extract \
  --render \
  --render-limit 3 \
  --screenshot-dir shots

# 检查 agent-reach
python -m combo agent-reach
```

## MCP 使用

启动 MCP Server：

```bash
python combo_mcp.py
```

暴露工具：

| 工具 | 作用 |
|---|---|
| `combo_search` | 搜索 |
| `combo_render` | Kitesurf 渲染/截图 |
| `combo_research` | 搜索 + 提取 + 渲染 |
| `combo_agent_reach_doctor` | 检查 agent-reach 状态 |

各客户端配置见 [README.mcp.md](./README.mcp.md)。

## 安全说明

- 所有 API Key 只放在本地 `.env`
- `.gitignore` 已忽略 `.env`、截图、缓存
- MCP 配置中不写明文密钥
- 公开发布前请确认没有提交 `.env` 或截图文件

## 说明

- AnySearch 走 MCP `tools/call` HTTP 接口，匿名可用
- Kitesurf 通过 Cloudflare Browser Run 的 CDP endpoint 连接
- Kitesurf 目前是 Beta，适合截图、HTML 提取、DOM 操作等 Agent 常见任务
