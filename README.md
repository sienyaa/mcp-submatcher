# MCP SubMatcher

一个基于统计分词匹配算法的 MCP 服务器，能够自动将本地字幕文件重命名为与对应视频同名，解决压制组、分辨率等干扰信息导致的无法自动加载字幕的问题。

## 特性

- ✅ **智能匹配**：基于统计分词和集数锚点的双重验证机制
- ✅ **MCP 协议**：通过 MCP 协议与 Claude Desktop 等 AI 客户端集成
- ✅ **多格式支持**：支持 `.mp4`, `.mkv`, `.avi` 等视频格式和 `.ass`, `.srt` 等字幕格式
- ✅ **优先级评分**：自动选择最优字幕（语言 > 格式 > 血统匹配）
- ✅ **安全执行**：默认演习模式，防止误操作
- ✅ **可配置化**：所有权重和参数均可通过 MCP 工具动态配置
- ✅ **冲突检测**：自动跳过评分相同的冲突匹配

## 安装

### 环境要求

- Python 3.10 或更高版本
- [uv](https://github.com/astral-sh/uv) - 快速 Python 包管理器
- [Claude Desktop](https://claude.ai/download) 或其他 MCP 客户端

### 快速安装

#### 1. 安装 UV（如果还未安装）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 或
brew install uv  # macOS
```

#### 2. 配置 Claude Desktop（推荐方式）

直接在 Claude Desktop 配置文件中使用 `uvx` 从 GitHub 安装，无需克隆项目。

## 配置 MCP 客户端

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加 MCP 服务器：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "submatcher": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/sienyaa/mcp-submatcher",
        "mcp-submatcher"
      ]
    }
  }
}
```

**说明**：
- `uvx` 会自动从 GitHub 下载并运行最新版本的 MCP SubMatcher
- 无需手动克隆项目或安装依赖
- 每次启动时会自动检查并使用最新版本

### 高级配置（可选）

如果需要使用特定版本或本地开发版本，可以使用以下配置：

```json
{
  "mcpServers": {
    "submatcher": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-submatcher",
        "run",
        "mcp-submatcher"
      ]
    }
  }
}
```

**说明**：
- 适用于本地开发或需要使用特定版本的情况
- 需要先克隆项目并运行 `uv sync`

### 重启 Claude Desktop

配置完成后，重启 Claude Desktop 以加载 MCP 服务器。

## 快速开始

配置完成后，你可以直接在 Claude Desktop 中与对话：

```
你：请扫描 /Users/username/Videos/TVShows 目录中的视频和字幕文件

Claude：[自动调用 scan_media_files 工具]
扫描完成，找到 5 个视频文件和 6 个字幕文件。

你：请预览这个目录中的字幕匹配结果

Claude：[自动调用 preview_matching 工具]
匹配结果预览：
1. Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.mkv
   - 匹配字幕: Breaking.Bad.S01E01.chs&eng.ass (评分: 280.0)
2. Breaking.Bad.S01E02.720p.WEB-DL.DDP5.1.H.264-NTb.mkv
   - 匹配字幕: Breaking.Bad.S01E02.cht&eng.srt (评分: 270.0)

你：看起来不错，请执行实际重命名

Claude：[自动调用 rename_subtitles 工具]
重命名完成：
- Breaking.Bad.S01E01.chs&eng.ass → Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.ass
- Breaking.Bad.S01E02.cht&eng.srt → Breaking.Bad.S01E02.720p.WEB-DL.DDP5.1.H.264-NTb.srt
```

就这么简单！无需手动运行任何命令，只需与 Claude 对话即可。

## 使用方法

### 可用工具

MCP SubMatcher 提供以下工具：

#### 1. scan_media_files

扫描指定目录中的视频和字幕文件。

**参数**：
- `directory` (string, 必需): 要扫描的目录路径

**示例**：
```
请扫描 /Users/username/Videos/TVShows 目录中的视频和字幕文件
```

#### 2. preview_matching

预览字幕匹配结果（演习模式，不会实际修改文件）。

**参数**：
- `directory` (string, 必需): 要分析的目录路径

**示例**：
```
请预览 /Users/username/Videos/TVShows 目录中的字幕匹配结果
```

#### 3. rename_subtitles

执行字幕重命名操作。

**参数**：
- `directory` (string, 必需): 要处理的目录路径
- `confirm` (boolean, 可选): 是否确认执行实际重命名（默认为 false，仅演习模式）

**示例**：
```
请重命名 /Users/username/Videos/TVShows 目录中的字幕文件
```

确认后执行：
```
请重命名 /Users/username/Videos/TVShows 目录中的字幕文件，确认执行实际重命名
```

#### 4. get_config_value

获取配置文件中指定路径的值。

**参数**：
- `path` (string, 必需): 配置路径，支持点号路径和数组索引

**示例**：
```
请获取配置中语言权重的第一个值
```

```
请获取配置中安全设置的 dry_run 值
```

#### 5. set_config_value

设置配置文件中指定路径的值。

**参数**：
- `path` (string, 必需): 配置路径
- `value` (any, 必需): 要设置的值

**示例**：
```
请将配置中安全设置的 dry_run 设置为 false
```

```
请将语言权重中简英双语的权重设置为 150
```

#### 6. get_config_summary

获取当前配置摘要。

**参数**：无

**示例**：
```
请获取当前配置摘要
```

## 配置说明

### 配置文件位置

配置文件位于 `core/config.yaml`。

### 主要配置项

#### 1. 语言权重配置

控制字幕语言的优先级，权重越高越优先。

```yaml
language_weights:
  - name: "简英双语"
    weight: 120
    keywords:
      - "chs&eng"
      - "cht&eng"
      - "双语"
```

**说明**：
- `weight`: 语言权重值，越高越优先
- `keywords`: 识别该语言的关键词列表（不区分大小写）

#### 2. 格式权重配置

控制字幕格式的优先级。

```yaml
format_weights:
  - name: "ass"
    weight: 100
    description: "特效字幕格式，支持样式和特效"
  - name: "srt"
    weight: 80
    description: "通用字幕格式"
```

#### 3. 血统匹配加分

如果字幕文件名包含与视频相同的压制组标识，给予额外加分。

```yaml
lineage_bonus:
  enabled: true
  weight: 20
  common_release_groups:
    - "eztv"
    - "rarbg"
    - "sparks"
```

#### 4. 文件扩展名配置

定义支持的视频和字幕格式。

```yaml
file_extensions:
  video:
    - ".mp4"
    - ".mkv"
    - ".avi"
  subtitle:
    - ".ass"
    - ".srt"
```

#### 5. 安全配置

控制程序的安全行为。

```yaml
safety:
  dry_run: false
  require_confirm: true
  backup_enabled: false
```

**说明**：
- `dry_run`: 默认演习模式（仅显示，不执行）
- `require_confirm`: 是否需要确认参数才执行

### 动态配置

通过 MCP 工具可以动态修改配置：

```
用户：请将配置中安全设置的 dry_run 设置为 true

Claude：[调用 set_config_value 工具]
配置已更新：safety.dry_run = true
```

## 工作原理

### 1. 文件扫描

程序递归扫描指定目录，识别所有视频文件和字幕文件。

### 2. 分词处理

使用配置的分隔符将文件名切碎为单词元（Tokens）。

**示例**：
```
Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.mkv
↓ 分词后
['breaking', 'bad', 's01e01', '1080p', 'bluray', 'x264', 'sparks']
```

### 3. 聚类分析

统计所有文件中每个Token出现的频率，识别"全局Token"（高频词）。

**目的**：区分文件夹内混杂的多部不同美剧。

### 4. 集数提取

从文件名中提取季号和集号，支持多种格式：

- `S01E01` → Season 1, Episode 1
- `1x01` → Season 1, Episode 1
- `101` → Season 1, Episode 01

### 5. 匹配算法

基于"全局Token"和"集数锚点"双重验证建立对应关系。

**匹配条件**：
- 存在共同的全局Token
- 季号和集号匹配（或至少集号匹配）

### 6. 评分系统

当一个视频对应多个候选字幕时，按以下权重自动筛选最优解：

**评分公式**：
```
总分 = 基础分 + 语言权重 + 格式权重 + 血统加分
```

**权重说明**：
1. **语言权重**（最高优先级）：
   - 简英双语：120分
   - 繁英双语：90分
   - 简体中文：80分
   - 繁体中文：70分
   - 纯英文：60分

2. **格式权重**：
   - `.ass`：100分（支持特效）
   - `.srt`：80分（通用格式）

3. **血统加分**：
   - 如果字幕和视频有相同的压制组标识：+20分

## 常见问题

### Q1: 如何在 Claude Desktop 中使用 MCP SubMatcher？

1. 确保已安装 [uv](https://github.com/astral-sh/uv)
2. 在 Claude Desktop 配置文件中添加 MCP 服务器配置（见上方"配置 MCP 客户端"章节）
3. 重启 Claude Desktop
4. 直接与 Claude 对话，例如："请扫描 /path/to/videos 目录中的视频和字幕文件"

### Q2: 使用 uvx 安装有什么优势？

使用 `uvx --from git+https://github.com/sienyaa/mcp-submatcher` 的优势：

- **无需克隆项目**：直接从 GitHub 下载运行
- **自动更新**：每次启动时自动使用最新版本
- **零依赖管理**：uvx 会自动处理所有依赖
- **沙盒化**：每个运行实例都是独立的，不会污染系统环境
- **快速启动**：uvx 使用缓存机制，第二次启动更快

### Q3: 为什么有些字幕没有匹配成功？

**可能原因**：
1. 字幕文件名中缺少集号信息（如 `S01E01`）
2. 字幕和视频的集号不匹配
3. 存在多个相同评分的候选字幕（冲突）
4. 字幕文件名与视频文件名没有共同的全局Token

**解决方法**：
- 使用 preview_matching 工具查看详细匹配结果
- 检查字幕文件名是否包含正确的集号
- 手动调整字幕文件名，添加集号信息

### Q4: 如何调整语言优先级？

通过 MCP 工具动态修改配置：

```
用户：请获取当前配置摘要
Claude：[调用 get_config_summary 工具]

用户：请将语言权重中简英双语的权重设置为 150
Claude：[调用 set_config_value 工具]
```

### Q5: 程序会修改视频文件吗？

**不会**。程序只会重命名字幕文件，不会修改或删除视频文件。

### Q6: 如何撤销重命名操作？

目前程序不支持自动撤销。建议：
1. 首次使用时先使用 preview_matching 工具预览结果
2. 确认结果无误后再使用 rename_subtitles 工具执行重命名
3. 可以手动备份字幕文件

### Q7: 支持哪些视频和字幕格式？

默认支持：
- **视频**：`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`
- **字幕**：`.ass`, `.srt`, `.sub`, `.ssa`

可以通过 MCP 工具动态添加更多格式。

### Q8: 程序能处理多个剧集混合的目录吗？

**可以**。程序通过聚类分析自动识别不同的剧集，即使多个剧集混合在同一目录也能正确匹配。

### Q9: 如何使用特定版本或本地开发版本？

如果需要使用特定版本或本地开发版本，可以在 Claude Desktop 配置文件中使用 `uv --directory` 方式：

```json
{
  "mcpServers": {
    "submatcher": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-submatcher",
        "run",
        "mcp-submatcher"
      ]
    }
  }
}
```

**适用场景**：
- 本地开发和测试
- 需要使用特定版本
- 需要修改代码并立即测试

**注意**：使用此方式前需要先克隆项目并运行 `uv sync`。

## 技术架构

### 核心模块

- **mcp_server.py**: MCP 服务器入口，定义工具和调用逻辑
- **mcp_adapter.py**: SubMatcher 的 MCP 适配器，提供 MCP 友好的接口
- **config_nlp.py**: 配置文件的 MCP 包装器，支持动态配置
- **core/submatcher.py**: 核心匹配算法实现
- **core/config.yaml**: 默认配置文件

### 技术栈

- **语言**: Python 3.10+
- **MCP 协议**: Model Context Protocol
- **核心库**: pathlib, re, collections.Counter
- **配置管理**: PyYAML
- **包管理**: uv

## 性能特点

- **轻量级**: 仅使用标准库和少量依赖
- **高效**: 基于统计和正则表达式，处理速度快
- **安全**: 默认演习模式，防止误操作
- **灵活**: 完全可配置，适应不同需求

## 开发

### 本地开发

如果需要本地开发或修改代码，可以克隆项目：

```bash
git clone https://github.com/sienyaa/mcp-submatcher.git
cd mcp-submatcher
uv sync
```

然后在 Claude Desktop 配置文件中使用本地版本：

```json
{
  "mcpServers": {
    "submatcher": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-submatcher",
        "run",
        "mcp-submatcher"
      ]
    }
  }
}
```

### 运行测试

```bash
uv run pytest
```

### 代码格式化

```bash
uv run black .
```

### 类型检查

```bash
uv run mypy .
```

## 贡献

欢迎提交问题报告和改进建议！

## 许可证

MIT License

## 更新日志

### v1.0.0 (2026-02-01)

- ✨ 初始版本发布
- ✅ 实现所有核心功能
- ✅ 支持 MCP 协议
- ✅ 完善的安全机制
- ✅ 详细的文档

## 相关链接

- [MCP 协议文档](https://modelcontextprotocol.io/)
- [Claude Desktop](https://claude.ai/download)
- [uv 文档](https://github.com/astral-sh/uv)

---

**享受 AI 辅助的自动化字幕管理体验！** 🎬🤖📝
