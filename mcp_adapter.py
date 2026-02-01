#!/usr/bin/env python3
"""
MCP Adapter for SubMatcher
适配器模式包装 submatcher.py，暴露 MCP 友好的接口
"""

import sys
import logging
from typing import Dict, List, Optional
from dataclasses import asdict
from pathlib import Path

BASE_DIR = Path(__file__).parent
CORE_DIR = BASE_DIR / "core"
sys.path.insert(0, str(BASE_DIR))

from core.submatcher import SubMatcher, Config, FileInfo, MatchResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def file_info_to_dict(file_info: FileInfo) -> Dict:
    """将 FileInfo 对象转换为字典"""
    return {
        'path': str(file_info.path),
        'file_type': file_info.file_type.value,
        'name': file_info.name,
        'stem': file_info.stem,
        'extension': file_info.extension,
        'tokens': file_info.tokens,
        'season': file_info.season,
        'episode': file_info.episode
    }


def match_result_to_dict(match_result: MatchResult) -> Dict:
    """将 MatchResult 对象转换为字典"""
    return {
        'video': file_info_to_dict(match_result.video),
        'subtitle': file_info_to_dict(match_result.subtitle),
        'score': match_result.score,
        'language_weight': match_result.language_weight,
        'format_weight': match_result.format_weight,
        'lineage_bonus': match_result.lineage_bonus
    }


class SubMatcherAdapter:
    """SubMatcher 的 MCP 适配器"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(BASE_DIR / "core" / "config.yaml")
        self.config_path = config_path
        self.matcher = SubMatcher(config_path)
        logger.info(f"SubMatcherAdapter initialized with config: {config_path}")

    def scan_directory(self, directory: str) -> Dict:
        """扫描视频/字幕文件"""
        logger.info(f"Scanning directory: {directory}")
        
        try:
            video_files, subtitle_files = self.matcher.file_scanner.scan_directory(directory)
            
            result = {
                'success': True,
                'directory': directory,
                'video_files': [file_info_to_dict(f) for f in video_files],
                'subtitle_files': [file_info_to_dict(f) for f in subtitle_files],
                'video_count': len(video_files),
                'subtitle_count': len(subtitle_files)
            }
            
            logger.info(f"Found {len(video_files)} video files and {len(subtitle_files)} subtitle files")
            return result
            
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            return {
                'success': False,
                'error': str(e),
                'directory': directory
            }

    def analyze_matches(self, directory: str) -> List[Dict]:
        """分析匹配（演习模式）"""
        logger.info(f"Analyzing matches for directory: {directory}")
        
        try:
            video_files, subtitle_files = self.matcher.file_scanner.scan_directory(directory)
            
            if not video_files or not subtitle_files:
                logger.warning("No video or subtitle files found")
                return []
            
            all_files = video_files + subtitle_files
            global_tokens, token_counter = self.matcher.cluster_analyzer.analyze(all_files)
            
            matches = []
            for video in video_files:
                match_result = self.matcher.matcher.find_best_match(video, subtitle_files, global_tokens)
                if match_result:
                    matches.append(match_result_to_dict(match_result))
                    subtitle_files.remove(match_result.subtitle)
            
            logger.info(f"Found {len(matches)} matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error analyzing matches: {e}")
            return []

    def execute_rename(self, directory: str, dry_run: bool = True) -> Dict:
        """执行重命名"""
        logger.info(f"Executing rename for directory: {directory}, dry_run={dry_run}")
        
        try:
            video_files, subtitle_files = self.matcher.file_scanner.scan_directory(directory)
            
            if not video_files or not subtitle_files:
                return {
                    'success': False,
                    'error': 'No video or subtitle files found',
                    'directory': directory
                }
            
            all_files = video_files + subtitle_files
            global_tokens, token_counter = self.matcher.cluster_analyzer.analyze(all_files)
            
            renamed_files = []
            failed_files = []
            skipped_files = []
            
            for video in video_files:
                match_result = self.matcher.matcher.find_best_match(video, subtitle_files, global_tokens)
                if match_result:
                    success = self.matcher.renamer.rename(match_result, dry_run=dry_run)
                    if success:
                        renamed_files.append({
                            'old_name': match_result.subtitle.name,
                            'new_name': f"{match_result.video.stem}{match_result.subtitle.extension}",
                            'video_name': match_result.video.name,
                            'score': match_result.score
                        })
                        subtitle_files.remove(match_result.subtitle)
                    else:
                        failed_files.append(match_result.subtitle.name)
                else:
                    skipped_files.append(video.name)
            
            result = {
                'success': True,
                'directory': directory,
                'dry_run': dry_run,
                'renamed_count': len(renamed_files),
                'failed_count': len(failed_files),
                'skipped_count': len(skipped_files),
                'renamed_files': renamed_files,
                'failed_files': failed_files,
                'skipped_files': skipped_files
            }
            
            logger.info(f"Rename completed: {len(renamed_files)} renamed, {len(failed_files)} failed, {len(skipped_files)} skipped")
            return result
            
        except Exception as e:
            logger.error(f"Error executing rename: {e}")
            return {
                'success': False,
                'error': str(e),
                'directory': directory
            }
