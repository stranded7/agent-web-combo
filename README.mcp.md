# MCP Server 接入说明

`combo_mcp.py` 把这个组合包装成了 MCP Server，AI Agent 可以通过标准 MCP 协议自动调用搜索、渲染、研究、agent-reach 检查。

## 启动方式

```bash
cd <PROJECT_DIR>
python combo_mcp.py
```

MCP 客户端通常以 stdio 方式拉起这个进程。

## 暴露的工具

| 工具名 | 作用 |
|---|---|
| `combo_search` | 搜索：Tavily / Exa / AnySearch |
| `combo_render` | Kitesurf + Playwright 渲染/截图 |
| `combo_research` | 完整流程：搜索 + 提取 + 渲染 |
| `combo_agent_reach_doctor` | 检查 agent-reach 平台渠道状态 |

## Claude Code 配置

在 `~/.claude.json` 或项目 `.mcp.json` 中加入：

```json
{
  "mcpServers": {
    "agent-web-combo": {
      "type": "stdio",
      "command": "python",
      "args": ["<PROJECT_DIR>/combo_mcp.py"],
      "env": {}
    }
  }
}
```

## Cursor 配置

在 Cursor 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "agent-web-combo": {
      "command": "python",
      "args": ["<PROJECT_DIR>/combo_mcp.py"]
    }
  }
}
```

## OpenCode 配置

在 `opencode.json` 中加入：

```json
{
  "mcp": {
    "agent-web-combo": {
      "type": "local",
      "command": ["python", "<PROJECT_DIR>/combo_mcp.py"],
      "enabled": true
    }
  }
}
```

> 如果 `python` 不在 PATH，请替换成完整路径，例如 `Z:\Python\python.exe`。

## DSH Desktop 配置

将下面的配置追加到你的 DSH Desktop profile patch 文件，例如：

```
<DSH_PROFILE_PATCH_FILE>
```

对应配置：

```yaml
- id: mcp-agent-web-combo
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: agent_web_combo
    transport: stdio
    command: '<PYTHON_PATH>'
    args:
      - '<PROJECT_DIR>/combo_mcp.py'
    cwd: '<PROJECT_DIR>'
    toolCallTimeoutMs: 120000
```

配置后会注册以下工具：

```text
mcp__agent_web_combo__combo_search
mcp__agent_web_combo__combo_render
mcp__agent_web_combo__combo_research
mcp__agent_web_combo__combo_agent_reach_doctor
```

> DSH 支持热生效：改配置后会自动断开重连，通常不需要重启 DSH Desktop。
> 如果工具没出现，重启一次 DSH Desktop 再试。
