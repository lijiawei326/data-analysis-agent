#!/usr/bin/env python3
"""
交互式可视化MCP服务器启动脚本
"""

import sys
import os
from pathlib import Path
import asyncio
import argparse

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'frontend'))

def main():
    """主启动函数"""
    parser = argparse.ArgumentParser(description='启动交互式可视化MCP服务器')
    parser.add_argument('--transport', '-t', 
                       choices=['sse', 'stdio'], 
                       default='sse',
                       help='传输协议 (默认: sse)')
    parser.add_argument('--host', 
                       default='localhost',
                       help='服务器主机 (默认: localhost)')
    parser.add_argument('--port', '-p', 
                       type=int, 
                       default=8000,
                       help='服务器端口 (默认: 8000)')
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='日志级别 (默认: INFO)')
    
    args = parser.parse_args()
    
    print("🚀 启动交互式可视化MCP服务器")
    print("=" * 50)
    print(f"传输协议: {args.transport}")
    if args.transport == 'sse':
        print(f"服务地址: http://{args.host}:{args.port}")
    print(f"日志级别: {args.log_level}")
    print("=" * 50)
    
    # 设置日志级别
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # 导入并启动服务器
    try:
        from interactive_visualization_server import mcp
        
        if args.transport == 'sse':
            mcp.run(transport='sse', host=args.host, port=args.port)
        else:
            mcp.run(transport='stdio')
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保项目依赖已正确安装")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main() 