#!/usr/bin/env python3
"""
智能数据分析系统启动脚本
用于启动Streamlit前端应用
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_backend_status(url="http://localhost:8001", timeout=5):
    """检查后端服务状态"""
    try:
        response = requests.get(f"{url}/", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_frontend():
    """启动前端应用"""
    print("🚀 启动智能数据分析系统前端...")
    
    # 检查后端状态
    print("🔍 检查后端服务状态...")
    if check_backend_status():
        print("✅ 后端服务运行正常")
    else:
        print("⚠️  警告: 后端服务未运行或无法连接")
        print("   请确保后端服务已启动: python backend.py")
        print("   继续启动前端...")
    
    # 获取当前脚本目录
    current_dir = Path(__file__).parent
    app_file = current_dir / "app.py"
    
    if not app_file.exists():
        print("❌ 错误: 找不到 app.py 文件")
        sys.exit(1)
    
    # 启动Streamlit应用
    try:
        print(f"📊 启动前端应用: {app_file}")
        print("🌐 前端地址: http://localhost:8502")
        print("📖 使用说明:")
        print("   - 在浏览器中打开 http://localhost:8502")
        print("   - 使用自然语言描述分析需求")
        print("   - 选择合适的分析类型")
        print("   - 查看分析结果和详情")
        print("\n" + "="*50)
        
        # 启动streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--server.port=8502",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 前端应用已停止")
    except Exception as e:
        print(f"❌ 启动前端应用失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("="*60)
    print("🎯 智能数据分析系统 - 前端启动器")
    print("📊 版本: 2.0.0")
    print("🔗 支持多种数据分析功能")
    print("="*60)
    
    start_frontend()

if __name__ == "__main__":
    main() 