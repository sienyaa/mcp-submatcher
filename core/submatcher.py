#!/usr/bin/env python3
"""
智能字幕对齐重命名工具
利用统计分词匹配算法自动将本地美剧字幕文件重命名为与对应视频同名
"""

import os
import re
import sys
import yaml
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class FileType(Enum):
    VIDEO = "video"
    SUBTITLE = "subtitle"


@dataclass
class FileInfo:
    path: Path
    file_type: FileType
    name: str
    stem: str
    extension: str
    tokens: List[str]
    season: Optional[int] = None
    episode: Optional[int] = None


@dataclass
class MatchResult:
    video: FileInfo
    subtitle: FileInfo
    score: float
    language_weight: float
    format_weight: float
    lineage_bonus: float


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"警告：配置文件 {self.config_path} 未找到，使用默认配置")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"警告：配置文件解析错误：{e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        return {
            'language_weights': [
                {'name': '简英双语', 'weight': 100, 'keywords': ['chs&eng', 'cht&eng', '双语']},
                {'name': '简体中文', 'weight': 80, 'keywords': ['chs', 'sc', '简体']},
                {'name': '纯英文', 'weight': 60, 'keywords': ['eng', 'en', 'english']}
            ],
            'format_weights': [
                {'name': 'ass', 'weight': 100},
                {'name': 'srt', 'weight': 80}
            ],
            'lineage_bonus': {
                'enabled': True,
                'weight': 20,
                'common_release_groups': ['eztv', 'rarbg', 'vxt', 'yify']
            },
            'file_extensions': {
                'video': ['.mp4', '.mkv', '.avi'],
                'subtitle': ['.ass', '.srt']
            },
            'tokenization': {
                'separators': ['.', '_', '-', '[', ']', '(', ')', ' '],
                'min_token_length': 2,
                'ignore_tokens': ['the', 'a', 'an', 'of', 'in', 'on', 'at']
            },
            'episode_patterns': [
                {'pattern': r'S(\d{1,2})E(\d{1,2})', 'season_group': 1, 'episode_group': 2},
                {'pattern': r'(\d{1,2})x(\d{1,2})', 'season_group': 1, 'episode_group': 2},
                {'pattern': r'(\d{1,2})(\d{2})', 'season_group': 1, 'episode_group': 2}
            ],
            'matching': {
                'min_common_tokens': 1,
                'min_score_threshold': 50,
                'skip_on_conflict': True,
                'log_unmatched': True
            },
            'safety': {
                'dry_run': True,
                'require_confirm': True,
                'backup_enabled': False,
                'backup_dir': '.backup'
            },
            'logging': {
                'level': 'INFO',
                'show_progress': True,
                'log_file': 'submatcher.log'
            }
        }

    def get_language_weights(self) -> List[dict]:
        return self.config.get('language_weights', [])

    def get_format_weights(self) -> List[dict]:
        return self.config.get('format_weights', [])

    def get_lineage_bonus_config(self) -> dict:
        return self.config.get('lineage_bonus', {})

    def get_video_extensions(self) -> List[str]:
        return self.config.get('file_extensions', {}).get('video', [])

    def get_subtitle_extensions(self) -> List[str]:
        return self.config.get('file_extensions', {}).get('subtitle', [])

    def get_tokenization_config(self) -> dict:
        return self.config.get('tokenization', {})

    def get_episode_patterns(self) -> List[dict]:
        return self.config.get('episode_patterns', [])

    def get_matching_config(self) -> dict:
        return self.config.get('matching', {})

    def get_safety_config(self) -> dict:
        return self.config.get('safety', {})

    def get_logging_config(self) -> dict:
        return self.config.get('logging', {})


class Tokenizer:
    def __init__(self, config: Config):
        self.config = config
        self.separators = config.get_tokenization_config().get('separators', [])
        self.min_token_length = config.get_tokenization_config().get('min_token_length', 2)
        self.ignore_tokens = set(config.get_tokenization_config().get('ignore_tokens', []))

    def tokenize(self, filename: str) -> List[str]:
        tokens = [filename]
        for sep in self.separators:
            new_tokens = []
            for token in tokens:
                new_tokens.extend(token.split(sep))
            tokens = new_tokens

        cleaned_tokens = []
        for token in tokens:
            token = token.strip().lower()
            if (len(token) >= self.min_token_length and
                token not in self.ignore_tokens and
                not token.isdigit()):
                cleaned_tokens.append(token)

        return cleaned_tokens


class EpisodeExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.patterns = config.get_episode_patterns()

    def extract(self, filename: str) -> Tuple[Optional[int], Optional[int]]:
        for pattern_config in self.patterns:
            pattern = pattern_config['pattern']
            season_group = pattern_config['season_group']
            episode_group = pattern_config['episode_group']

            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                season = int(match.group(season_group))
                episode = int(match.group(episode_group))

                condition = pattern_config.get('condition')
                if condition and 'episode_group' in condition:
                    if not eval(condition.replace('episode_group', str(episode))):
                        continue

                return season, episode

        return None, None


class FileScanner:
    def __init__(self, config: Config, tokenizer: Tokenizer, episode_extractor: EpisodeExtractor):
        self.config = config
        self.tokenizer = tokenizer
        self.episode_extractor = episode_extractor

    def scan_directory(self, directory: str) -> Tuple[List[FileInfo], List[FileInfo]]:
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"目录不存在：{directory}")

        video_files = []
        subtitle_files = []

        video_extensions = self.config.get_video_extensions()
        subtitle_extensions = self.config.get_subtitle_extensions()

        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                extension = file_path.suffix.lower()

                if extension in video_extensions:
                    video_files.append(self._create_file_info(file_path, FileType.VIDEO))
                elif extension in subtitle_extensions:
                    subtitle_files.append(self._create_file_info(file_path, FileType.SUBTITLE))

        return video_files, subtitle_files

    def _create_file_info(self, path: Path, file_type: FileType) -> FileInfo:
        name = path.name
        stem = path.stem
        extension = path.suffix.lower()
        tokens = self.tokenizer.tokenize(stem)
        season, episode = self.episode_extractor.extract(stem)

        return FileInfo(
            path=path,
            file_type=file_type,
            name=name,
            stem=stem,
            extension=extension,
            tokens=tokens,
            season=season,
            episode=episode
        )


class ClusterAnalyzer:
    def __init__(self, config: Config):
        self.config = config

    def analyze(self, files: List[FileInfo]) -> Tuple[Set[str], Counter]:
        all_tokens = []
        for file_info in files:
            all_tokens.extend(file_info.tokens)

        token_counter = Counter(all_tokens)

        matching_config = self.config.get_matching_config()
        min_common_tokens = matching_config.get('min_common_tokens', 1)

        global_tokens = set()
        for token, count in token_counter.items():
            if count >= min_common_tokens:
                global_tokens.add(token)

        return global_tokens, token_counter


class Matcher:
    def __init__(self, config: Config):
        self.config = config

    def match(self, video: FileInfo, subtitle: FileInfo, global_tokens: Set[str]) -> float:
        score = 0.0

        video_token_set = set(video.tokens)
        subtitle_token_set = set(subtitle.tokens)

        common_tokens = video_token_set & subtitle_token_set & global_tokens
        score += len(common_tokens) * 10

        if video.season is not None and video.episode is not None:
            if subtitle.season == video.season and subtitle.episode == video.episode:
                score += 50
            elif subtitle.episode == video.episode:
                score += 30

        return score

    def find_best_match(self, video: FileInfo, subtitles: List[FileInfo],
                       global_tokens: Set[str]) -> Optional[MatchResult]:
        matches = []
        for subtitle in subtitles:
            score = self.match(video, subtitle, global_tokens)
            if score > 0:
                match_result = self._calculate_detailed_score(video, subtitle, score)
                matches.append(match_result)

        if not matches:
            return None

        matching_config = self.config.get_matching_config()
        skip_on_conflict = matching_config.get('skip_on_conflict', True)

        matches.sort(key=lambda x: x.score, reverse=True)

        if skip_on_conflict and len(matches) > 1:
            if matches[0].score == matches[1].score:
                return None

        return matches[0]

    def _calculate_detailed_score(self, video: FileInfo, subtitle: FileInfo,
                                  base_score: float) -> MatchResult:
        language_weight = self._calculate_language_weight(subtitle.stem)
        format_weight = self._calculate_format_weight(subtitle.extension)
        lineage_bonus = self._calculate_lineage_bonus(video.stem, subtitle.stem)

        total_score = base_score + language_weight + format_weight + lineage_bonus

        return MatchResult(
            video=video,
            subtitle=subtitle,
            score=total_score,
            language_weight=language_weight,
            format_weight=format_weight,
            lineage_bonus=lineage_bonus
        )

    def _calculate_language_weight(self, filename: str) -> float:
        language_weights = self.config.get_language_weights()
        filename_lower = filename.lower()

        for lang_config in language_weights:
            keywords = [kw.lower() for kw in lang_config.get('keywords', [])]
            for keyword in keywords:
                if keyword in filename_lower:
                    return lang_config.get('weight', 0)

        return 0

    def _calculate_format_weight(self, extension: str) -> float:
        format_weights = self.config.get_format_weights()
        extension = extension.lstrip('.')

        for format_config in format_weights:
            if format_config.get('name', '').lower() == extension.lower():
                return format_config.get('weight', 0)

        return 0

    def _calculate_lineage_bonus(self, video_name: str, subtitle_name: str) -> float:
        lineage_config = self.config.get_lineage_bonus_config()
        if not lineage_config.get('enabled', False):
            return 0

        video_lower = video_name.lower()
        subtitle_lower = subtitle_name.lower()

        release_groups = lineage_config.get('common_release_groups', [])
        bonus_weight = lineage_config.get('weight', 20)

        for group in release_groups:
            if group.lower() in video_lower and group.lower() in subtitle_lower:
                return bonus_weight

        return 0


class Renamer:
    def __init__(self, config: Config):
        self.config = config

    def rename(self, match_result: MatchResult, dry_run: bool = True) -> bool:
        video = match_result.video
        subtitle = match_result.subtitle

        new_subtitle_name = video.stem + subtitle.extension
        new_subtitle_path = subtitle.path.parent / new_subtitle_name

        if new_subtitle_path == subtitle.path:
            return False

        if dry_run:
            print(f"[DRY RUN] {subtitle.name} -> {new_subtitle_name}")
            return True
        else:
            try:
                subtitle.path.rename(new_subtitle_path)
                print(f"[RENAME] {subtitle.name} -> {new_subtitle_name}")
                return True
            except Exception as e:
                print(f"[ERROR] 重命名失败：{subtitle.name} -> {new_subtitle_name}")
                print(f"  错误信息：{e}")
                return False


class SubMatcher:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        self.tokenizer = Tokenizer(self.config)
        self.episode_extractor = EpisodeExtractor(self.config)
        self.file_scanner = FileScanner(self.config, self.tokenizer, self.episode_extractor)
        self.cluster_analyzer = ClusterAnalyzer(self.config)
        self.matcher = Matcher(self.config)
        self.renamer = Renamer(self.config)

    def run(self, directory: str, confirm: bool = False, verbose: bool = False) -> None:
        try:
            print(f"扫描目录：{directory}")
            video_files, subtitle_files = self.file_scanner.scan_directory(directory)

            print(f"找到 {len(video_files)} 个视频文件")
            print(f"找到 {len(subtitle_files)} 个字幕文件")

            if not video_files or not subtitle_files:
                print("未找到视频或字幕文件，退出")
                return

            all_files = video_files + subtitle_files
            global_tokens, token_counter = self.cluster_analyzer.analyze(all_files)

            if verbose:
                print(f"\n全局Token（前20个）：")
                for token, count in token_counter.most_common(20):
                    print(f"  {token}: {count}")

            safety_config = self.config.get_safety_config()
            if confirm:
                dry_run = False
            else:
                dry_run = safety_config.get('dry_run', True)

            if dry_run:
                print("\n=== 演习模式（Dry Run）===")
                print("仅显示拟重命名结果，不会实际修改文件")
                print("使用 --confirm 或 -y 参数执行实际重命名\n")
            else:
                print("\n=== 执行模式 ===")
                print("将实际重命名字幕文件\n")

            matched_count = 0
            skipped_count = 0

            for video in video_files:
                match_result = self.matcher.find_best_match(video, subtitle_files, global_tokens)

                if match_result:
                    if verbose:
                        print(f"\n匹配：{video.name}")
                        print(f"  字幕：{match_result.subtitle.name}")
                        print(f"  评分：{match_result.score:.1f}")
                        print(f"    - 基础分：{match_result.score - match_result.language_weight - match_result.format_weight - match_result.lineage_bonus:.1f}")
                        print(f"    - 语言权重：{match_result.language_weight:.1f}")
                        print(f"    - 格式权重：{match_result.format_weight:.1f}")
                        print(f"    - 血统加分：{match_result.lineage_bonus:.1f}")

                    success = self.renamer.rename(match_result, dry_run=dry_run)
                    if success:
                        matched_count += 1
                        subtitle_files.remove(match_result.subtitle)
                else:
                    if verbose:
                        print(f"\n未匹配：{video.name}")
                    skipped_count += 1

            print(f"\n=== 总结 ===")
            print(f"匹配成功：{matched_count} 个")
            print(f"跳过：{skipped_count} 个")
            print(f"剩余未匹配字幕：{len(subtitle_files)} 个")

            matching_config = self.config.get_matching_config()
            if matching_config.get('log_unmatched', True) and subtitle_files:
                print(f"\n未匹配的字幕文件：")
                for subtitle in subtitle_files:
                    print(f"  {subtitle.name}")

        except Exception as e:
            print(f"错误：{e}")
            import traceback
            traceback.print_exc()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='智能字幕对齐重命名工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python submatcher.py /path/to/videos
  python submatcher.py /path/to/videos --confirm
  python submatcher.py /path/to/videos -c custom_config.yaml -v
        """
    )

    parser.add_argument('directory', help='要扫描的目录路径')
    parser.add_argument('-c', '--config', default='config.yaml',
                       help='配置文件路径（默认：config.yaml）')
    parser.add_argument('-y', '--confirm', action='store_true',
                       help='确认执行实际重命名（默认为演习模式）')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='显示详细输出')

    args = parser.parse_args()

    matcher = SubMatcher(args.config)
    matcher.run(args.directory, confirm=args.confirm, verbose=args.verbose)


if __name__ == '__main__':
    main()
