# 智能字幕对齐重命名工具

一个基于统计分词匹配算法的命令行工具，能够自动将本地美剧字幕文件重命名为与对应视频同名，解决压制组、分辨率等干扰信息导致的无法自动加载字幕的问题。

## 特性

- ✅ **智能匹配**：基于统计分词和集数锚点的双重验证机制
- ✅ **多格式支持**：支持 `.mp4`, `.mkv`, `.avi` 等视频格式和 `.ass`, `.srt` 等字幕格式
- ✅ **优先级评分**：自动选择最优字幕（语言 > 格式 > 血统匹配）
- ✅ **安全执行**：默认演习模式，防止误操作
- ✅ **可配置化**：所有权重和参数均可通过配置文件自定义
- ✅ **冲突检测**：自动跳过评分相同的冲突匹配
- ✅ **沙盒化**：所有依赖在本地虚拟环境中，无系统残留

## 安装

### 环境要求

- Python 3.8 或更高版本

### 快速开始（推荐使用 UV）

#### 方法 1：使用 UV（推荐）

UV 是一个极速的 Python 包管理器，比传统的 `pip + venv` 快 10-100 倍。

```bash
# 1. 安装 UV（如果还没安装）
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 或
brew install uv  # macOS

# 2. 同步项目依赖
uv sync

# 3. 运行程序
uv run mcp-submatcher --help
```

#### 方法 2：使用传统方式

1. 克隆或下载项目到本地

```bash
cd submatcher
```

2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

注意：本项目仅使用Python标准库+PyYAML，依赖非常轻量。

## 配置

程序使用 `config.yaml` 配置文件，所有参数均可自定义。

### 主要配置项

#### 1. 语言权重配置

控制字幕语言的优先级，权重越高越优先。

```yaml
language_weights:
  - name: "简英双语"
    weight: 100
    keywords:
      - "chs&eng"
      - "cht&eng"
      - "简体&英文"
      - "双语"
```

**说明**：
- `weight`: 语言权重值，越高越优先
- `keywords`: 识别该语言的关键词列表（不区分大小写）
- 可以添加或删除语言类型，调整权重值

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

**说明**：
- `.ass` 格式权重更高，因为支持特效字幕
- 可以添加其他格式（如 `.sub`, `.ssa`）

#### 3. 血统匹配加分

如果字幕文件名包含与视频相同的压制组标识，给予额外加分。

```yaml
lineage_bonus:
  enabled: true
  weight: 20
  description: "如果字幕文件名包含与视频相同的压制组标识，给予额外加分"
  common_release_groups:
    - "eztv"
    - "rarbg"
    - "vxt"
    - "yify"
```

**说明**：
- `enabled`: 是否启用血统匹配
- `weight`: 加分权重
- `common_release_groups`: 常见压制组标识列表

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

**说明**：
- 可以根据需要添加或删除支持的格式

#### 5. 分词配置

控制文件名分词的行为。

```yaml
tokenization:
  separators:
    - "."
    - "_"
    - "-"
    - "["
    - "]"
    - "("
    - ")"
    - " "
  min_token_length: 2
  ignore_tokens:
    - "the"
    - "a"
    - "an"
```

**说明**：
- `separators`: 分隔符列表
- `min_token_length`: 最小token长度，过滤过短的词
- `ignore_tokens`: 忽略的常见无意义词

#### 6. 集数提取配置

定义识别季号和集号的正则表达式模式。

```yaml
episode_patterns:
  - pattern: "S(\\d{1,2})E(\\d{1,2})"
    season_group: 1
    episode_group: 2

  - pattern: "(\\d{1,2})x(\\d{1,2})"
    season_group: 1
    episode_group: 2
```

**说明**：
- 支持多种格式：`S01E01`, `1x01`, `101` 等
- 可以添加自定义模式

#### 7. 安全配置

控制程序的安全行为。

```yaml
safety:
  dry_run: true
  require_confirm: true
  backup_enabled: false
  backup_dir: ".backup"
```

**说明**：
- `dry_run`: 默认演习模式（仅显示，不执行）
- `require_confirm`: 是否需要确认参数才执行
- `backup_enabled`: 是否启用备份（暂未实现）

## 使用方法

### 基本语法

```bash
# 使用 UV（推荐）
uv run mcp-submatcher <目录路径> [选项]

# 使用传统方式
mcp-submatcher <目录路径> [选项]
```

### 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `directory` | - | 要扫描的目录路径（必选） |
| `--config` | `-c` | 配置文件路径（默认：config.yaml） |
| `--confirm` | `-y` | 确认执行实际重命名（默认为演习模式） |
| `--verbose` | `-v` | 显示详细输出 |
| `--help` | `-h` | 显示帮助信息 |

### 使用示例

#### 1. 演习模式（推荐首次使用）

默认模式，仅显示拟重命名结果，不会实际修改文件。

```bash
# 使用 UV（推荐）
mcp-submatcher /path/to/videos

# 使用传统方式
mcp-submatcher /path/to/videos
```

**输出示例**：
```
扫描目录：/path/to/videos
找到 4 个视频文件
找到 5 个字幕文件

=== 演习模式（Dry Run）===
仅显示拟重命名结果，不会实际修改文件
使用 --confirm 或 -y 参数执行实际重命名

[DRY RUN] Breaking.Bad.S01E01.chs&eng.ass -> Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.ass
[DRY RUN] Breaking.Bad.S01E02.cht&eng.srt -> Breaking.Bad.S01E02.720p.WEB-DL.DDP5.1.H.264-NTb.srt

=== 总结 ===
匹配成功：2 个
跳过：0 个
剩余未匹配字幕：3 个
```

#### 2. 详细输出模式

显示匹配详情，包括评分分解。

```bash
# 使用 UV（推荐）
mcp-submatcher /path/to/videos -v

# 使用传统方式
mcp-submatcher /path/to/videos -v
```

**输出示例**：
```
扫描目录：/path/to/videos
找到 4 个视频文件
找到 5 个字幕文件

全局Token（前20个）：
  breaking: 6
  bad: 6
  s01e01: 2
  s01e02: 2

=== 演习模式（Dry Run）===

匹配：Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.mkv
  字幕：Breaking.Bad.S01E01.chs&eng.ass
  评分：280.0
    - 基础分：80.0
    - 语言权重：100.0
    - 格式权重：100.0
    - 血统加分：0.0
[DRY RUN] Breaking.Bad.S01E01.chs&eng.ass -> Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.ass
```

#### 3. 执行实际重命名

确认演习结果无误后，使用 `--confirm` 参数执行实际重命名。

```bash
# 使用 UV（推荐）
mcp-submatcher /path/to/videos --confirm

# 使用传统方式
mcp-submatcher /path/to/videos --confirm
```

**输出示例**：
```
扫描目录：/path/to/videos
找到 4 个视频文件
找到 5 个字幕文件

=== 执行模式 ===
将实际重命名字幕文件

[RENAME] Breaking.Bad.S01E01.chs&eng.ass -> Breaking.Bad.S01E01.1080p.BluRay.x264-SPARKS.ass
[RENAME] Breaking.Bad.S01E02.cht&eng.srt -> Breaking.Bad.S01E02.720p.WEB-DL.DDP5.1.H.264-NTb.srt

=== 总结 ===
匹配成功：2 个
跳过：0 个
剩余未匹配字幕：3 个
```

#### 4. 使用自定义配置文件

```bash
mcp-submatcher /path/to/videos -c /path/to/custom_config.yaml
```

#### 5. 组合使用多个参数

```bash
mcp-submatcher /path/to/videos --confirm --verbose
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
   - 简英双语：100分
   - 繁英双语：90分
   - 简体中文：80分
   - 繁体中文：70分
   - 纯英文：60分

2. **格式权重**：
   - `.ass`：100分（支持特效）
   - `.srt`：80分（通用格式）

3. **血统加分**：
   - 如果字幕和视频有相同的压制组标识：+20分

### 7. 冲突处理

- 如果多个候选字幕的评分相同，跳过该匹配（避免误操作）
- 未找到匹配的字幕会记录在日志中

## 常见问题

### Q1: 为什么有些字幕没有匹配成功？

**可能原因**：
1. 字幕文件名中缺少集号信息（如 `S01E01`）
2. 字幕和视频的集号不匹配
3. 存在多个相同评分的候选字幕（冲突）
4. 字幕文件名与视频文件名没有共同的全局Token

**解决方法**：
- 使用 `-v` 参数查看详细输出，了解匹配失败原因
- 检查字幕文件名是否包含正确的集号
- 手动调整字幕文件名，添加集号信息

### Q2: 如何添加新的语言类型？

编辑 `config.yaml` 文件，在 `language_weights` 部分添加：

```yaml
- name: "新语言"
  weight: 75
  keywords:
    - "关键词1"
    - "关键词2"
```

### Q3: 如何调整语言优先级？

修改 `config.yaml` 中对应语言的 `weight` 值，权重越高优先级越高。

### Q4: 程序会修改视频文件吗？

**不会**。程序只会重命名字幕文件，不会修改或删除视频文件。

### Q5: 如何撤销重命名操作？

目前程序不支持自动撤销。建议：
1. 首次使用时先运行演习模式（默认）
2. 确认结果无误后再使用 `--confirm` 参数
3. 可以手动备份字幕文件

### Q6: 支持哪些视频和字幕格式？

默认支持：
- **视频**：`.mp4`, `.mkv`, `.avi`
- **字幕**：`.ass`, `.srt`

可以在 `config.yaml` 的 `file_extensions` 部分添加更多格式。

### Q7: 程序能处理多个剧集混合的目录吗？

**可以**。程序通过聚类分析自动识别不同的剧集，即使多个剧集混合在同一目录也能正确匹配。

### Q8: 如何提高匹配准确率？

1. 确保字幕文件名包含正确的集号（如 `S01E01`）
2. 使用详细输出模式（`-v`）查看匹配过程
3. 根据实际情况调整配置文件中的权重值
4. 添加常见的压制组标识到 `common_release_groups`

## 最佳实践

### 1. 首次使用流程

```bash
# 1. 演习模式，查看拟重命名结果
# 使用 UV（推荐）
mcp-submatcher /path/to/videos -v

# 使用传统方式
mcp-submatcher /path/to/videos -v

# 2. 检查输出，确认匹配结果正确

# 3. 执行实际重命名
# 使用 UV（推荐）
mcp-submatcher /path/to/videos --confirm

# 使用传统方式
mcp-submatcher /path/to/videos --confirm
```

### 2. 批量处理多个目录

```bash
# 使用脚本批量处理
for dir in /path/to/series/*/; do
    echo "Processing: $dir"
    mcp-submatcher "$dir" --confirm
done
```

### 3. 自定义配置

根据个人偏好创建自定义配置文件：

```bash
# 创建自定义配置
cp config.yaml my_config.yaml

# 编辑配置文件
vim my_config.yaml

# 使用自定义配置
mcp-submatcher /path/to/videos -c my_config.yaml
```

### 4. 定期维护

- 定期更新 `common_release_groups` 列表，添加新的压制组
- 根据实际使用情况调整语言和格式权重
- 检查未匹配的字幕文件，优化匹配规则

## 技术架构

### 核心模块

- **Config**: 配置加载和管理
- **Tokenizer**: 文件名分词处理
- **EpisodeExtractor**: 集数提取
- **FileScanner**: 文件扫描
- **ClusterAnalyzer**: 聚类分析
- **Matcher**: 匹配算法
- **Renamer**: 重命名执行
- **SubMatcher**: 主控制器

### 技术栈

- **语言**: Python 3.6+
- **核心库**: pathlib, re, collections.Counter, argparse
- **配置管理**: PyYAML
- **设计模式**: 函数式编程，模块化设计

## 性能特点

- **轻量级**: 仅使用标准库，无复杂依赖
- **高效**: 基于统计和正则表达式，处理速度快
- **安全**: 默认演习模式，防止误操作
- **灵活**: 完全可配置，适应不同需求

## 贡献

欢迎提交问题报告和改进建议！

## 许可证

本项目仅供个人学习和使用。

## 更新日志

### v1.0.0 (2026-01-28)

- ✨ 初始版本发布
- ✅ 实现所有核心功能
- ✅ 支持可配置化
- ✅ 完善的安全机制
- ✅ 详细的文档

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件

---

**享受自动化的字幕管理体验！** 🎬📝
