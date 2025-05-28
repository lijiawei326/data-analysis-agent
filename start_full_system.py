#!/usr/bin/env python3
"""
智能数据分析系统完整启动脚本
用于启动整个系统：相关性分析服务器 + 后端 + 前端
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path
import requests

class SystemLauncher:
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        
    def check_port(self, port, timeout=5):
        """检查端口是否可用"""
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def start_correlation_server(self):
        """启动相关性分析服务器"""
        print("🔧 启动相关性分析服务器...")
        
        server_dir = self.base_dir / "server"
        server_file = server_dir / "corr_server.py"
        
        if not server_file.exists():
            print(f"❌ 错误: 找不到相关性分析服务器文件: {server_file}")
            return False
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(server_file)],
                cwd=str(server_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(("correlation_server", process))
            
            # 等待服务器启动
            print("⏳ 等待相关性分析服务器启动...")
            for i in range(30):  # 最多等待30秒
                if self.check_port(8000):
                    print("✅ 相关性分析服务器启动成功 (端口: 8000)")
                    return True
                time.sleep(1)
            
            print("⚠️  相关性分析服务器启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动相关性分析服务器失败: {e}")
            return False
    
    def start_backend(self):
        """启动后端服务"""
        print("🚀 启动智能分析后端...")
        
        frontend_dir = self.base_dir / "frontend"
        backend_file = frontend_dir / "backend.py"
        
        if not backend_file.exists():
            print(f"❌ 错误: 找不到后端文件: {backend_file}")
            return False
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(backend_file)],
                cwd=str(frontend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(("backend", process))
            
            # 等待后端启动
            print("⏳ 等待后端服务启动...")
            for i in range(30):  # 最多等待30秒
                if self.check_port(8001):
                    print("✅ 后端服务启动成功 (端口: 8001)")
                    return True
                time.sleep(1)
            
            print("⚠️  后端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动后端服务失败: {e}")
            return False
    
    def start_frontend(self):
        """启动前端应用"""
        print("📊 启动前端应用...")
        
        frontend_dir = self.base_dir / "frontend"
        app_file = frontend_dir / "app.py"
        
        if not app_file.exists():
            print(f"❌ 错误: 找不到前端文件: {app_file}")
            return False
        
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                str(app_file),
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--browser.gatherUsageStats=false"
            ], cwd=str(frontend_dir))
            
            self.processes.append(("frontend", process))
            
            # 等待前端启动
            print("⏳ 等待前端应用启动...")
            time.sleep(5)  # Streamlit需要更多时间启动
            
            print("✅ 前端应用启动成功 (端口: 8501)")
            return True
            
        except Exception as e:
            print(f"❌ 启动前端应用失败: {e}")
            return False
    
    def stop_all_processes(self):
        """停止所有进程"""
        print("\n🛑 正在停止所有服务...")
        
        for name, process in self.processes:
            try:
                print(f"   停止 {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   强制停止 {name}...")
                process.kill()
            except Exception as e:
                print(f"   停止 {name} 时出错: {e}")
        
        print("✅ 所有服务已停止")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}，正在关闭系统...")
        self.stop_all_processes()
        sys.exit(0)
    
    def start_system(self):
        """启动完整系统"""
        print("="*60)
        print("🎯 智能数据分析系统 - 完整启动器")
        print("📊 版本: 2.0.0")
        print("🔗 启动顺序: 相关性服务器 → 后端 → 前端")
        print("="*60)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # 1. 启动相关性分析服务器
            if not self.start_correlation_server():
                print("❌ 相关性分析服务器启动失败，退出")
                return False
            
            # 2. 启动后端服务
            if not self.start_backend():
                print("❌ 后端服务启动失败，退出")
                self.stop_all_processes()
                return False
            
            # 3. 启动前端应用
            if not self.start_frontend():
                print("❌ 前端应用启动失败，退出")
                self.stop_all_processes()
                return False
            
            # 显示系统信息
            print("\n" + "="*60)
            print("🎉 智能数据分析系统启动完成！")
            print("="*60)
            print("📡 服务地址:")
            print("   - 相关性分析服务器: http://localhost:8000")
            print("   - 后端API: http://localhost:8001")
            print("   - 前端界面: http://localhost:8501")
            print("\n📖 使用说明:")
            print("   1. 打开浏览器访问: http://localhost:8501")
            print("   2. 在界面中输入分析需求")
            print("   3. 选择分析类型或使用自动选择")
            print("   4. 查看分析结果和详情")
            print("\n⚠️  注意事项:")
            print("   - 请保持此终端窗口打开")
            print("   - 按 Ctrl+C 可以停止所有服务")
            print("   - 如需单独管理服务，请使用对应的启动脚本")
            print("="*60)
            
            # 保持运行状态
            try:
                while True:
                    time.sleep(1)
                    # 检查进程状态
                    for name, process in self.processes:
                        if process.poll() is not None:
                            print(f"⚠️  {name} 进程意外退出")
                            
            except KeyboardInterrupt:
                pass
            
        except Exception as e:
            print(f"❌ 系统启动失败: {e}")
            self.stop_all_processes()
            return False
        
        finally:
            self.stop_all_processes()
        
        return True

def main():
    """主函数"""
    launcher = SystemLauncher()
    success = launcher.start_system()
    
    if success:
        print("👋 系统已正常关闭")
    else:
        print("❌ 系统启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 