---
name: "submatcher-mcp"
description: "字幕匹配重命名工具 MCP 服务器。当用户需要自动匹配和重命名字幕文件时调用此技能。"
---

# SubMatcher MCP Server

提供智能字幕对齐重命名功能，基于统计分词匹配算法自动将本地字幕文件重命名为与对应视频同名。

## 功能特性

- **扫描媒体文件**：自动识别目录中的视频和字幕文件
- **预览匹配结果**：演习模式查看匹配结果，不实际修改文件
- **执行重命名**：确认后批量重命名字幕文件
- **配置管理**：动态调整语言权重、格式权重等匹配参数

## 使用场景

当用户说以下类似需求时触发：
- "帮我整理xxx文件夹里的字幕"
- "自动匹配并重命名字幕文件"
- "字幕和视频文件名对不上"
- "批量重命名字幕"

## MCP 工具

### scan_media_files
扫描指定目录中的视频和字幕文件

### preview_matching
预览字幕匹配结果（演习模式）

### rename_subtitles
执行字幕重命名操作（支持 confirm 参数控制是否实际修改）

### get_config_value
获取配置文件中指定路径的值

### set_config_value
设置配置文件中指定路径的值

### get_config_summary
获取当前配置摘要

## 安装与运行

使用 uvx 一键运行：
```bash
uvx mcp-submatcher
```

或在 Claude Desktop 配置文件中添加：
```json
{
  "mcpServers": {
    "submatcher": {
      "command": "uvx",
      "args": ["mcp-submatcher"]
    }
  }
}
```

## 配置说明

配置文件位于 `core/config.yaml`，包含：
- `language_weights`：语言权重配置
- `format_weights`：格式权重配置
- `lineage_bonus`：系列匹配加成
- `safety`：安全设置（如 dry_run 模式）
- `matching`：匹配算法参数

所有配置修改会自动备份到 `.config_backups/` 目录，并记录到 `SYSTEM_MOD_LOG.md` 审计日志。
