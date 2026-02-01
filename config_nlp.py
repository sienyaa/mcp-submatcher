#!/usr/bin/env python3
"""
Configuration Manager for SubMatcher
提供配置文件读写、备份和审计日志功能
"""

import sys
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

BASE_DIR = Path(__file__).parent
CORE_DIR = BASE_DIR / "core"
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """配置变更记录"""
    success: bool
    path: str
    config_path: str
    backup_path: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = ""


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(BASE_DIR / "core" / "config.yaml")
        self.config_path = config_path
        self.backup_dir = BASE_DIR / ".config_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.log_file = BASE_DIR / "SYSTEM_MOD_LOG.md"
        self._init_log_file()
        logger.info(f"ConfigManager initialized with config: {config_path}")

    def _init_log_file(self):
        """初始化审计日志文件"""
        if not self.log_file.exists():
            self.log_file.write_text("# 系统修改日志\n\n")

    def _write_log(self, path: str, old_value: Any, new_value: Any, environment: str):
        """写入审计日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = f"## {timestamp}\n- **配置路径**: {path}\n- **旧值**: {old_value}\n- **新值**: {new_value}\n- **环境**: {environment}\n\n"
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        logger.info(f"Log entry written: {path}")

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise

    def _save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def _backup_config(self) -> str:
        """备份配置文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"config_backup_{timestamp}.yaml"
        backup_path = self.backup_dir / backup_filename
        shutil.copy2(self.config_path, backup_path)
        logger.info(f"Config backed up to: {backup_path}")
        return str(backup_path)

    def get_config_value(self, path: str) -> Any:
        """读取配置值（支持点号路径和数组索引）"""
        config = self._load_config()
        value = config
        
        keys = path.split('.')
        for key in keys:
            if '[' in key and key.endswith(']'):
                base_key = key[:key.index('[')]
                index = int(key[key.index('[')+1:key.index(']')])
                if isinstance(value, dict) and base_key in value:
                    value = value[base_key]
                    if isinstance(value, list) and 0 <= index < len(value):
                        value = value[index]
                    else:
                        return None
                else:
                    return None
            elif isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def set_config_value(self, path: str, value: Any) -> ConfigChange:
        """设置配置值（支持点号路径和数组索引）"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        try:
            old_value = self.get_config_value(path)
            
            config = self._load_config()
            current = config
            
            keys = path.split('.')
            for i, key in enumerate(keys[:-1]):
                if '[' in key and key.endswith(']'):
                    base_key = key[:key.index('[')]
                    index = int(key[key.index('[')+1:key.index(']')])
                    if base_key not in current:
                        current[base_key] = []
                    if isinstance(current[base_key], list) and 0 <= index < len(current[base_key]):
                        current = current[base_key][index]
                    else:
                        return ConfigChange(
                            success=False,
                            path=path,
                            config_path=self.config_path,
                            error=f"Invalid index for {base_key}",
                            timestamp=timestamp
                        )
                else:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
            
            last_key = keys[-1]
            if '[' in last_key and last_key.endswith(']'):
                base_key = last_key[:last_key.index('[')]
                index = int(last_key[last_key.index('[')+1:last_key.index(']')])
                if base_key not in current:
                    current[base_key] = []
                if isinstance(current[base_key], list) and 0 <= index < len(current[base_key]):
                    current[base_key][index] = value
                else:
                    return ConfigChange(
                        success=False,
                        path=path,
                        config_path=self.config_path,
                        error=f"Invalid index for {base_key}",
                        timestamp=timestamp
                    )
            else:
                current[last_key] = value
            
            backup_path = self._backup_config()
            self._save_config(config)
            
            import sys
            environment = f"Python {sys.version.split()[0]}"
            self._write_log(path, old_value, value, environment)
            
            return ConfigChange(
                success=True,
                path=path,
                config_path=self.config_path,
                backup_path=backup_path,
                old_value=old_value,
                new_value=value,
                timestamp=timestamp
            )
            
        except Exception as e:
            return ConfigChange(
                success=False,
                path=path,
                config_path=self.config_path,
                error=str(e),
                timestamp=timestamp
            )

    def get_config_summary(self) -> Dict:
        """获取配置摘要"""
        config = self._load_config()
        
        summary = {
            'language_weights': config.get('language_weights', []),
            'format_weights': config.get('format_weights', []),
            'lineage_bonus': config.get('lineage_bonus', {}),
            'safety': config.get('safety', {}),
            'matching': config.get('matching', {})
        }
        
        return summary


class ConfigMCPWrapper:
    """配置管理器的 MCP 包装类"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(BASE_DIR / "core" / "config.yaml")
        self.manager = ConfigManager(config_path)
        logger.info(f"ConfigMCPWrapper initialized with config: {config_path}")

    def get_config_value(self, path: str) -> Any:
        """获取配置值"""
        logger.info(f"Getting config value at path: {path}")
        return self.manager.get_config_value(path)

    def set_config_value(self, path: str, value: Any) -> Dict:
        """设置配置值"""
        logger.info(f"Setting config value at path: {path} to: {value}")
        change = self.manager.set_config_value(path, value)
        
        result = {
            'success': change.success,
            'path': change.path,
            'config_path': change.config_path,
            'backup_path': change.backup_path,
            'old_value': change.old_value,
            'new_value': change.new_value,
            'error': change.error,
            'timestamp': change.timestamp
        }
        
        return result

    def get_config_summary(self) -> Dict:
        """获取配置摘要"""
        logger.info("Getting config summary")
        return self.manager.get_config_summary()
