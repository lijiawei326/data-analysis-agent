"""
通用日志配置模块
使用loguru实现简洁高效的日志记录，适用于任何Python项目
"""
import os
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger
from datetime import datetime


class UniversalLogger:
    """通用日志器类，适用于任何场景"""
    
    def __init__(
        self, 
        log_dir: Optional[str] = None,
        app_name: str = "app",
        log_level: str = "INFO",
        rotation: str = "00:00",
        retention: str = "30 days",
        console_output: bool = True,
        file_output: bool = True,
        custom_format: Optional[str] = None
    ):
        """
        初始化通用日志器
        
        Args:
            log_dir: 日志目录路径，默认为当前目录下的logs文件夹
            app_name: 应用名称，用于日志文件命名
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            rotation: 日志轮转策略 (如: "00:00", "100 MB", "1 week")
            retention: 日志保留策略 (如: "30 days", "10 files")
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            custom_format: 自定义日志格式
        """
        self.app_name = app_name
        self.log_level = log_level
        self.rotation = rotation
        self.retention = retention
        self.console_output = console_output
        self.file_output = file_output
        
        # 设置日志目录
        if log_dir is None:
            self.log_dir = Path.cwd() / "logs"
        else:
            self.log_dir = Path(log_dir)
        
        # 设置日志格式
        self.console_format = (
            custom_format or 
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        
        self.file_format = (
            custom_format or 
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 移除默认的控制台输出
        logger.remove()
        
        # 添加控制台输出
        if self.console_output:
            logger.add(
                sys.stderr,
                format=self.console_format,
                level=self.log_level,
                colorize=True
            )
        
        # 添加文件输出
        if self.file_output:
            log_file = self.log_dir / f"{self.app_name}_{{time:YYYY-MM-DD}}.log"
            logger.add(
                str(log_file),
                rotation=self.rotation,
                retention=self.retention,
                level=self.log_level,
                format=self.file_format,
                encoding="utf-8"
            )
        
        logger.info(f"日志系统已初始化 [{self.app_name}] - 日志目录: {self.log_dir}")
    
    def get_logger(self):
        """获取日志器实例"""
        return logger
    
    def log_with_tag(self, level: str, message: str, tag: str = ""):
        """带标签的日志记录"""
        tag_prefix = f"[{tag}] " if tag else ""
        getattr(logger, level.lower())(f"{tag_prefix}{message}")
    
    def log_user_action(self, action: str, details: str = "", user_id: str = ""):
        """记录用户行为"""
        user_prefix = f"[USER:{user_id}] " if user_id else "[USER] "
        logger.info(f"{user_prefix}{action}: {details}")
    
    def log_api_request(self, method: str, endpoint: str, status_code: int = None, 
                       duration: float = None, user_id: str = ""):
        """记录API请求"""
        msg = f"[API] {method} {endpoint}"
        if status_code:
            msg += f" - {status_code}"
        if duration:
            msg += f" - {duration:.3f}s"
        if user_id:
            msg += f" - User:{user_id}"
        logger.info(msg)
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """记录性能指标"""
        logger.info(f"[PERF] {operation}: {duration:.3f}s {details}")
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any] = None):
        """记录带上下文的错误"""
        error_msg = f"[ERROR] {type(error).__name__}: {str(error)}"
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            error_msg += f" | Context: {context_str}"
        logger.error(error_msg)
    
    def log_business_event(self, event: str, data: Dict[str, Any] = None):
        """记录业务事件"""
        msg = f"[EVENT] {event}"
        if data:
            data_str = " | ".join([f"{k}={v}" for k, v in data.items()])
            msg += f" | Data: {data_str}"
        logger.info(msg)
    
    def log_security_event(self, event: str, severity: str = "INFO", details: str = ""):
        """记录安全事件"""
        level = severity.lower()
        getattr(logger, level)(f"[SECURITY] {event}: {details}")
    
    def get_log_files_info(self) -> Dict[str, Any]:
        """获取日志文件信息"""
        try:
            if not self.log_dir.exists():
                return {"files": [], "message": "日志目录不存在"}
            
            log_files = []
            for file_path in self.log_dir.glob("*.log"):
                file_size = file_path.stat().st_size
                file_mtime = file_path.stat().st_mtime
                log_files.append({
                    "name": file_path.name,
                    "size": file_size,
                    "size_mb": round(file_size / (1024*1024), 2),
                    "modified": datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "path": str(file_path)
                })
            
            # 按修改时间排序，最新的在前面
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            return {
                "files": log_files,
                "total_files": len(log_files),
                "log_dir": str(self.log_dir)
            }
            
        except Exception as e:
            logger.error(f"获取日志文件列表失败: {str(e)}")
            return {"files": [], "error": str(e)}
    
    def read_log_file(self, log_file: str, lines: int = 100, 
                     search_pattern: str = None) -> Dict[str, Any]:
        """读取指定日志文件"""
        try:
            file_path = self.log_dir / log_file
            
            # 安全检查
            if not file_path.is_relative_to(self.log_dir):
                raise ValueError("无效的文件路径")
            
            if not file_path.exists():
                raise FileNotFoundError("日志文件不存在")
            
            if not file_path.suffix == '.log':
                raise ValueError("只能查看日志文件")
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # 搜索过滤
            if search_pattern:
                filtered_lines = [line for line in all_lines if search_pattern in line]
                display_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
            else:
                display_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            return {
                "file": log_file,
                "total_lines": len(all_lines),
                "showing_lines": len(display_lines),
                "content": ''.join(display_lines),
                "search_pattern": search_pattern,
                "filtered_lines": len(filtered_lines) if search_pattern else None
            }
            
        except Exception as e:
            logger.error(f"读取日志文件失败: {str(e)}")
            raise
    
    def set_log_level(self, level: str):
        """动态修改日志级别"""
        self.log_level = level
        # 重新配置日志器
        self._setup_logging()
        logger.info(f"日志级别已修改为: {level}")
    
    def add_file_handler(self, file_path: str, level: str = "INFO", 
                        format_str: str = None, **kwargs):
        """添加额外的文件处理器"""
        logger.add(
            file_path,
            level=level,
            format=format_str or self.file_format,
            encoding="utf-8",
            **kwargs
        )
        logger.info(f"已添加文件处理器: {file_path}")
    
    def create_child_logger(self, name: str):
        """创建子日志器"""
        return logger.bind(module=name)


def create_logger(
    app_name: str = "app",
    log_dir: Optional[str] = None,
    **kwargs
) -> UniversalLogger:
    """
    快速创建日志器的工厂函数
    
    Args:
        app_name: 应用名称
        log_dir: 日志目录
        **kwargs: 其他配置参数
    
    Returns:
        UniversalLogger实例
    """
    return UniversalLogger(app_name=app_name, log_dir=log_dir, **kwargs)


# 默认实例 - 向后兼容
default_log_config = UniversalLogger(
    app_name="app",
    log_dir=os.environ.get("LOG_DIR", "logs")
)

# 导出默认日志器
logger = default_log_config.get_logger()

# 兼容性函数
def log_chat_input(message: str):
    """聊天输入日志（兼容性函数）"""
    default_log_config.log_with_tag("info", f"用户输入: {message}", "CHAT")

def log_chat_output(message: str, processing_time: float = None):
    """聊天输出日志（兼容性函数）"""
    default_log_config.log_with_tag("info", f"AI回复: {message}", "CHAT")
    if processing_time:
        default_log_config.log_performance("Chat Response", processing_time)

def log_chat_error(user_input: str, error: str, processing_time: float = None):
    """聊天错误日志（兼容性函数）"""
    error_msg = f"对话出错 - 用户输入: {user_input[:50]}... | 错误: {error}"
    if processing_time:
        error_msg += f" | 耗时: {processing_time:.2f}秒"
    default_log_config.log_with_tag("error", error_msg, "CHAT")

# 向后兼容的全局实例
log_config = default_log_config 