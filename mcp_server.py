# /// script
# dependencies = [
#   "mcp>=1.0.0",
#   "PyYAML>=6.0",
# ]
# requires-python = ">=3.10"
# ///

#!/usr/bin/env python3
"""
MCP Server for SubMatcher
提供字幕匹配和配置管理的 MCP 服务
"""

import sys
import logging
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_adapter import SubMatcherAdapter
from config_nlp import ConfigMCPWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("submatcher-server")

adapter = SubMatcherAdapter()
config_wrapper = ConfigMCPWrapper()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 MCP 工具"""
    return [
        Tool(
            name="scan_media_files",
            description="扫描指定目录中的视频和字幕文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要扫描的目录路径"
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="preview_matching",
            description="预览字幕匹配结果（演习模式，不会实际修改文件）",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要分析的目录路径"
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="rename_subtitles",
            description="执行字幕重命名操作",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要处理的目录路径"
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "是否确认执行实际重命名（默认为 false，仅演习模式）",
                        "default": False
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="get_config_value",
            description="获取配置文件中指定路径的值",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "配置路径，支持点号路径和数组索引，例如：'language_weights[0].weight'、'safety.dry_run'"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="set_config_value",
            description="设置配置文件中指定路径的值",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "配置路径，支持点号路径和数组索引，例如：'language_weights[0].weight'、'safety.dry_run'"
                    },
                    "value": {
                        "description": "要设置的值，可以是字符串、数字、布尔值等"
                    }
                },
                "required": ["path", "value"]
            }
        ),
        Tool(
            name="get_config_summary",
            description="获取当前配置摘要",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """调用 MCP 工具"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "scan_media_files":
            result = adapter.scan_directory(arguments["directory"])
            return [TextContent(type="text", text=str(result))]
        
        elif name == "preview_matching":
            result = adapter.analyze_matches(arguments["directory"])
            return [TextContent(type="text", text=str(result))]
        
        elif name == "rename_subtitles":
            confirm = arguments.get("confirm", False)
            result = adapter.execute_rename(arguments["directory"], dry_run=not confirm)
            return [TextContent(type="text", text=str(result))]
        
        elif name == "get_config_value":
            result = config_wrapper.get_config_value(arguments["path"])
            return [TextContent(type="text", text=str(result))]
        
        elif name == "set_config_value":
            result = config_wrapper.set_config_value(arguments["path"], arguments["value"])
            return [TextContent(type="text", text=str(result))]
        
        elif name == "get_config_summary":
            result = config_wrapper.get_config_summary()
            return [TextContent(type="text", text=str(result))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """启动 MCP 服务器"""
    logger.info("Starting SubMatcher MCP Server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cli_main():
    """CLI 入口点（同步函数）"""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
