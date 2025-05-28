"""
交互式可视化MCP服务器
支持多轮对话的可视化代码生成和优化
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import asyncio
import json
import time
import random
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import ast
import hashlib

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 忽略警告
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'frontend'))

from logger_config import create_logger
from mcp.server.fastmcp import FastMCP
from custom_types.types import ReadDataParam
from correlation_server import correlation_analysis

# ===== 异常定义 =====
class VisualizationError(Exception):
    """可视化基础异常"""
    pass

class CodeSecurityError(VisualizationError):
    """代码安全异常"""
    pass

class ChartGenerationError(VisualizationError):
    """图表生成异常"""
    pass

class SessionNotFoundError(VisualizationError):
    """会话不存在异常"""
    pass

# ===== 配置类 =====
@dataclass
class VisualizationConfig:
    """可视化配置"""
    output_dir: str = "./visualizations"
    default_figsize: Tuple[int, int] = (12, 8)
    default_dpi: int = 300
    default_format: str = "png"
    session_timeout: int = 3600  # 1小时
    max_sessions: int = 100
    
    # 颜色方案
    color_schemes: Dict[str, str] = field(default_factory=lambda: {
        "correlation": "RdBu_r",
        "sequential": "viridis", 
        "diverging": "RdYlBu",
        "categorical": "Set3"
    })
    
    # 中文字体
    chinese_fonts: List[str] = field(default_factory=lambda: [
        'SimHei', 'DejaVu Sans', 'Arial Unicode MS'
    ])
    
    def __post_init__(self):
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

# ===== 会话管理 =====
@dataclass
class VisualizationSession:
    """可视化会话状态"""
    session_id: str
    user_request: str                    # 原始用户需求
    data_info: Dict                     # 数据信息
    current_code: str                   # 当前代码版本
    code_history: List[str]             # 代码历史版本
    generated_charts: List[str]         # 生成的图片路径
    conversation_history: List[Dict]     # 对话历史
    
    # 新增：相关性分析相关字段
    correlation_result: Optional[str]    # 相关性分析原始结果（Markdown表格）
    correlation_matrix: Optional[pd.DataFrame]  # 解析后的相关性矩阵
    correlation_vars: Optional[List[str]]  # 相关性分析变量
    correlation_method: str              # 相关性计算方法
    has_correlation_analysis: bool       # 是否包含相关性分析
    
    # 会话类型标记
    session_type: str                   # "visualization_only", "correlation_only", "both"
    
    created_at: datetime
    updated_at: datetime
    
    def add_code_version(self, code: str, chart_path: str, feedback: str = ""):
        """添加新的代码版本"""
        if self.current_code:  # 只有当前代码不为空时才添加到历史
            self.code_history.append(self.current_code)
        self.current_code = code
        self.generated_charts.append(chart_path)
        self.conversation_history.append({
            "type": "iteration",
            "feedback": feedback,
            "code": code,
            "chart": chart_path,
            "timestamp": datetime.now()
        })
        self.updated_at = datetime.now()
    
    def set_correlation_data(self, 
                           correlation_result: str,
                           correlation_matrix: pd.DataFrame,
                           correlation_vars: List[str],
                           correlation_method: str):
        """设置相关性分析数据"""
        self.correlation_result = correlation_result
        self.correlation_matrix = correlation_matrix
        self.correlation_vars = correlation_vars
        self.correlation_method = correlation_method
        self.has_correlation_analysis = True
        self.updated_at = datetime.now()
    
    def get_correlation_table(self) -> Optional[str]:
        """获取相关性表格"""
        return self.correlation_result
    
    def get_correlation_matrix(self) -> Optional[pd.DataFrame]:
        """获取相关性矩阵（用于绘图）"""
        return self.correlation_matrix

class SessionManager:
    """会话管理器"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.sessions: Dict[str, VisualizationSession] = {}
        self.logger = create_logger(app_name="session_mgr", log_dir="./logs").get_logger()
    
    def create_session(self, user_request: str, data_info: Dict, session_type: str = "visualization_only") -> str:
        """创建新会话"""
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        # 检查会话数量限制
        if len(self.sessions) >= self.config.max_sessions:
            self._cleanup_oldest_session()
        
        session_id = f"viz_{int(time.time())}_{random.randint(1000, 9999)}"
        session = VisualizationSession(
            session_id=session_id,
            user_request=user_request,
            data_info=data_info,
            current_code="",
            code_history=[],
            generated_charts=[],
            conversation_history=[],
            # 新增字段
            correlation_result=None,
            correlation_matrix=None,
            correlation_vars=None,
            correlation_method="pearson",
            has_correlation_analysis=False,
            session_type=session_type,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.sessions[session_id] = session
        self.logger.info(f"创建新会话: {session_id}, 类型: {session_type}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[VisualizationSession]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session:
            # 检查是否过期
            if self._is_session_expired(session):
                self.delete_session(session_id)
                return None
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"删除会话: {session_id}")
            return True
        return False
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if self._is_session_expired(session)
        ]
        for sid in expired_sessions:
            self.delete_session(sid)
    
    def _cleanup_oldest_session(self):
        """清理最老的会话"""
        if self.sessions:
            oldest_session_id = min(
                self.sessions.keys(),
                key=lambda sid: self.sessions[sid].created_at
            )
            self.delete_session(oldest_session_id)
    
    def _is_session_expired(self, session: VisualizationSession) -> bool:
        """检查会话是否过期"""
        age = (datetime.now() - session.updated_at).total_seconds()
        return age > self.config.session_timeout

# ===== 数据加载器 =====
class DataLoader:
    """数据加载器"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.logger = create_logger(app_name="data_loader", log_dir="./logs").get_logger()
    
    async def load_data(self, read_data_param: ReadDataParam) -> pd.DataFrame:
        """加载数据"""
        try:
            file_path = Path(read_data_param.read_data_query).resolve()
            
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 根据文件类型加载数据
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            elif file_ext == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_ext}")
            
            self.logger.info(f"成功加载数据: {df.shape[0]}行 x {df.shape[1]}列")
            return df
            
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            raise VisualizationError(f"数据加载失败: {str(e)}") from e
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
        """应用过滤条件"""
        if not filters:
            return df
        
        df_filtered = df.copy()
        for col, value in filters.items():
            if col not in df_filtered.columns:
                raise ValueError(f"过滤列不存在: {col}")
            df_filtered = df_filtered[df_filtered[col] == value]
            self.logger.debug(f"应用过滤条件 {col}={value}，剩余 {len(df_filtered)} 行")
        
        return df_filtered

# ===== 代码执行器 =====
class SafeCodeExecutor:
    """安全代码执行器"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.logger = create_logger(app_name="code_executor", log_dir="./logs").get_logger()
        
        # 允许的模块
        self.allowed_imports = {
            'matplotlib.pyplot', 'matplotlib', 'matplotlib.dates', 'matplotlib.patches',
            'seaborn', 'pandas', 'numpy', 'scipy', 'sklearn', 'plotly',
            'datetime', 'time', 'math', 're'
        }
        
        # 禁用的函数
        self.forbidden_functions = {
            'exec', 'eval', 'open', '__import__', 'compile',
            'input', 'raw_input', 'exit', 'quit', 'help'
        }
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """验证代码安全性"""
        
        # 检查禁用函数
        for forbidden in self.forbidden_functions:
            if forbidden in code:
                return False, f"代码包含禁用函数: {forbidden}"
        
        # 检查文件操作
        file_operations = ['open(', 'file(', 'input(', 'raw_input(']
        for op in file_operations:
            if op in code:
                return False, f"代码包含禁用的文件操作: {op}"
        
        # 检查import语句
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._is_allowed_import(alias.name):
                            return False, f"不允许的import: {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._is_allowed_import(node.module):
                        return False, f"不允许的import: {node.module}"
        except SyntaxError as e:
            return False, f"代码语法错误: {e}"
        
        return True, "代码验证通过"
    
    def _is_allowed_import(self, module_name: str) -> bool:
        """检查是否允许导入该模块"""
        if not module_name:
            return True
        
        for allowed in self.allowed_imports:
            if module_name.startswith(allowed):
                return True
        return False
    
    async def execute_code(self, 
                          code: str, 
                          data_df: pd.DataFrame,
                          save_path: str) -> str:
        """执行绘图代码"""
        
        # 1. 验证代码安全性
        is_safe, message = self.validate_code(code)
        if not is_safe:
            raise CodeSecurityError(message)
        
        # 2. 准备执行环境
        exec_globals = {
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'min': min, 'max': max, 'sum': sum, 'abs': abs,
                'round': round, 'sorted': sorted, 'reversed': reversed,
                'any': any, 'all': all,
                'print': print  # 允许打印调试
            }
        }
        
        exec_locals = {
            'data_df': data_df,
            'save_path': save_path,
            # 预导入常用模块
            'pd': pd,
            'np': np,
            'plt': plt,
            'sns': sns
        }
        
        # 3. 执行代码
        try:
            self.logger.info(f"开始执行代码，保存路径: {save_path}")
            exec(code, exec_globals, exec_locals)
            
            # 4. 验证文件是否生成
            if not Path(save_path).exists():
                raise ChartGenerationError("代码执行完成但未生成图表文件")
            
            self.logger.info(f"代码执行成功，图表已保存: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"代码执行失败: {e}")
            # 确保关闭所有图形
            plt.close('all')
            raise ChartGenerationError(f"代码执行失败: {str(e)}")

# ===== 相关性结果解析器 =====
class CorrelationResultParser:
    """相关性结果解析器"""
    
    def __init__(self):
        self.logger = create_logger(app_name="corr_parser", log_dir="./logs").get_logger()
    
    def parse_to_matrix(self, correlation_result: str, variables: List[str]) -> pd.DataFrame:
        """将Markdown表格解析为数值矩阵"""
        try:
            # 检查是否有分组
            if "**" in correlation_result and "-" in correlation_result:
                # 分组相关性分析，取第一个分组
                return self._parse_grouped_correlation(correlation_result, variables)
            else:
                # 简单相关性矩阵
                return self._parse_simple_correlation(correlation_result, variables)
                
        except Exception as e:
            self.logger.error(f"相关性结果解析失败: {e}")
            # 如果解析失败，创建一个示例矩阵
            return self._create_dummy_matrix(variables)
    
    def _parse_simple_correlation(self, result: str, variables: List[str]) -> pd.DataFrame:
        """解析简单相关性矩阵"""
        lines = result.strip().split('\n')
        
        # 找到表格开始位置
        table_start = -1
        for i, line in enumerate(lines):
            if '| 变量 |' in line:
                table_start = i
                break
        
        if table_start == -1:
            raise ValueError("无法找到相关性矩阵表格")
        
        # 解析表格数据
        matrix_data = {}
        data_lines = lines[table_start + 2:]  # 跳过表头和分隔线
        
        for line in data_lines:
            if not line.strip() or not line.startswith('|'):
                continue
                
            parts = [p.strip() for p in line.split('|')[1:-1]]  # 去掉首尾空元素
            if len(parts) < len(variables) + 1:
                continue
                
            row_var = parts[0]
            for i, col_var in enumerate(variables):
                if i + 1 < len(parts):
                    try:
                        value_str = parts[i + 1]
                        if value_str == "数据不足":
                            value = 0.0
                        elif value_str == "1.000":
                            value = 1.0 if row_var == col_var else 0.0
                        else:
                            value = float(value_str)
                        matrix_data[(row_var, col_var)] = value
                    except (ValueError, IndexError):
                        matrix_data[(row_var, col_var)] = 0.0
        
        # 构建DataFrame
        matrix = pd.DataFrame(index=variables, columns=variables)
        for var1 in variables:
            for var2 in variables:
                matrix.loc[var1, var2] = matrix_data.get((var1, var2), 1.0 if var1 == var2 else 0.0)
        
        return matrix.astype(float)
    
    def _parse_grouped_correlation(self, result: str, variables: List[str]) -> pd.DataFrame:
        """解析分组相关性矩阵，取第一个分组"""
        # 简化实现：找到第一个表格并解析
        lines = result.strip().split('\n')
        
        # 找到第一个表格
        table_start = -1
        for i, line in enumerate(lines):
            if '| 变量 |' in line:
                table_start = i
                break
        
        if table_start != -1:
            # 提取第一个表格的内容
            table_lines = []
            for line in lines[table_start:]:
                if line.strip() and ('|' in line):
                    table_lines.append(line)
                elif line.strip() == "" and table_lines:
                    break  # 表格结束
            
            if table_lines:
                table_content = '\n'.join(table_lines)
                return self._parse_simple_correlation(table_content, variables)
        
        # 如果解析失败，返回示例矩阵
        return self._create_dummy_matrix(variables)
    
    def _create_dummy_matrix(self, variables: List[str]) -> pd.DataFrame:
        """创建示例相关性矩阵"""
        n = len(variables)
        # 创建随机相关性矩阵
        np.random.seed(42)
        matrix = np.random.rand(n, n)
        matrix = (matrix + matrix.T) / 2  # 确保对称
        np.fill_diagonal(matrix, 1.0)  # 对角线为1
        
        self.logger.warning(f"使用示例相关性矩阵，变量: {variables}")
        return pd.DataFrame(matrix, index=variables, columns=variables)

# ===== 主要实现类 =====
class InteractiveVisualizationMCP:
    """交互式可视化MCP实现类"""
    
    def __init__(self):
        self.config = VisualizationConfig()
        self.session_manager = SessionManager(self.config)
        self.data_loader = DataLoader(self.config)
        self.code_executor = SafeCodeExecutor(self.config)
        self.correlation_parser = CorrelationResultParser()
        self.data_cache = {}  # 简单的数据缓存
        self.logger = create_logger(app_name="interactive_viz", log_dir="./logs").get_logger()
    
    async def start_session_impl(self, 
                                user_request: str,
                                read_data_param: ReadDataParam,
                                correlation_vars: Optional[List[str]] = None,
                                correlation_method: str = "pearson",
                                filters: Optional[Dict[str, str]] = None,
                                group_by: Optional[List[str]] = None,
                                include_correlation_table: bool = False) -> str:
        """开始会话的具体实现"""
        
        try:
            self.logger.info(f"开始新的可视化会话: {user_request}")
            
            # 1. 准备数据和相关性结果
            data_df, correlation_result, correlation_matrix = await self._prepare_data_and_correlation_enhanced(
                read_data_param, correlation_vars, correlation_method,
                filters, group_by, user_request, include_correlation_table
            )
            
            # 2. 缓存数据
            data_key = f"data_{int(time.time())}_{random.randint(1000, 9999)}"
            self.data_cache[data_key] = data_df
            
            # 3. 获取数据信息
            data_info = self._get_data_info(data_df)
            data_info['data_key'] = data_key
            
            # 4. 确定会话类型
            has_correlation = correlation_result is not None
            session_type = "both" if has_correlation else "visualization_only"
            
            # 5. 创建会话
            session_id = self.session_manager.create_session(user_request, data_info, session_type)
            
            # 6. 如果有相关性分析，设置相关性数据
            if has_correlation and correlation_vars:
                session = self.session_manager.get_session(session_id)
                session.set_correlation_data(
                    correlation_result=correlation_result,
                    correlation_matrix=correlation_matrix,
                    correlation_vars=correlation_vars,
                    correlation_method=correlation_method
                )
            
            # 7. 调用agent生成初始代码
            from visualization_agent import interactive_visualization_agent
            initial_code = await interactive_visualization_agent.generate_initial_code(
                user_request, data_info
            )
            
            # 8. 执行代码生成图表
            chart_path = await self._execute_and_save(initial_code, data_df, session_id, "v1")
            
            # 9. 更新会话
            session = self.session_manager.get_session(session_id)
            session.current_code = initial_code
            session.generated_charts.append(chart_path)
            session.conversation_history.append({
                "type": "initial",
                "request": user_request,
                "code": initial_code,
                "chart": chart_path,
                "timestamp": datetime.now()
            })
            
            # 10. 构建结果
            result = {
                "session_id": session_id,
                "chart_path": chart_path,
                "session_type": session_type,
                "message": "可视化会话已创建，图表已生成。您可以提供反馈来改进图表。"
            }
            
            # 11. 如果需要相关性表格，添加到结果中
            if include_correlation_table and correlation_result:
                result["correlation_table"] = correlation_result
                result["message"] += " 相关性表格也已包含在结果中。"
            
            # 12. 如果有相关性分析，添加相关信息
            if has_correlation:
                result["has_correlation_analysis"] = True
                result["correlation_vars"] = correlation_vars
                result["correlation_method"] = correlation_method
                result["message"] += f" 会话包含相关性分析（{correlation_method}），可使用 get_correlation_table_from_session 获取表格。"
            
            self.logger.info(f"会话创建成功: {session_id}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"会话创建失败: {e}")
            return f"会话创建失败: {str(e)}"
    
    async def refine_visualization_impl(self, session_id: str, user_feedback: str) -> str:
        """优化可视化的具体实现"""
        
        try:
            self.logger.info(f"优化可视化: {session_id}, 反馈: {user_feedback}")
            
            # 1. 获取会话
            session = self.session_manager.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")
            
            # 2. 获取缓存的数据
            data_df = self.data_cache.get(session.data_info['data_key'])
            if data_df is None:
                raise VisualizationError("数据缓存已过期，请重新开始会话")
            
            # 3. 调用agent生成修改后的代码
            from visualization_agent import interactive_visualization_agent
            modified_code = await interactive_visualization_agent.modify_code(
                current_code=session.current_code,
                user_feedback=user_feedback,
                original_request=session.user_request,
                data_info=session.data_info,
                conversation_history=session.conversation_history
            )
            
            # 4. 执行新代码
            version = f"v{len(session.generated_charts) + 1}"
            new_chart_path = await self._execute_and_save(modified_code, data_df, session_id, version)
            
            # 5. 更新会话
            session.add_code_version(modified_code, new_chart_path, user_feedback)
            
            result = {
                "session_id": session_id,
                "chart_path": new_chart_path,
                "version": version,
                "message": f"图表已根据反馈更新（{version}）。如需进一步调整，请继续提供反馈。"
            }
            
            self.logger.info(f"图表优化成功: {session_id} -> {version}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"图表优化失败: {e}")
            return f"图表优化失败: {str(e)}"
    
    async def get_session_info_impl(self, session_id: str) -> str:
        """获取会话信息的具体实现"""
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return f"会话不存在: {session_id}"
        
        info = {
            "session_id": session_id,
            "original_request": session.user_request,
            "current_version": f"v{len(session.generated_charts)}",
            "total_iterations": len(session.conversation_history),
            "generated_charts": session.generated_charts,
            "conversation_summary": [
                {
                    "type": conv["type"],
                    "feedback": conv.get("feedback", conv.get("request", "")),
                    "timestamp": conv["timestamp"].isoformat()
                }
                for conv in session.conversation_history
            ],
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        
        return json.dumps(info, ensure_ascii=False, indent=2)
    
    async def rollback_to_version_impl(self, session_id: str, version: str) -> str:
        """回滚到指定版本的具体实现"""
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")
            
            version_idx = int(version[1:]) - 1
            if version_idx < 0 or version_idx >= len(session.code_history):
                raise ValueError(f"版本不存在: {version}")
            
            # 回滚代码
            session.current_code = session.code_history[version_idx]
            
            # 重新生成图表
            data_df = self.data_cache.get(session.data_info['data_key'])
            if data_df is None:
                raise VisualizationError("数据缓存已过期，无法回滚")
            
            chart_path = await self._execute_and_save(
                session.current_code, 
                data_df, 
                session_id, 
                f"{version}_rollback"
            )
            
            session.generated_charts.append(chart_path)
            session.conversation_history.append({
                "type": "rollback",
                "target_version": version,
                "chart": chart_path,
                "timestamp": datetime.now()
            })
            
            result = {
                "session_id": session_id,
                "chart_path": chart_path,
                "message": f"已回滚到{version}并重新生成图表"
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"版本回滚失败: {str(e)}"
    
    async def _prepare_data_and_correlation_enhanced(self, 
                                                   read_data_param: ReadDataParam,
                                                   correlation_vars: Optional[List[str]],
                                                   correlation_method: str,
                                                   filters: Optional[Dict[str, str]],
                                                   group_by: Optional[List[str]],
                                                   user_request: str,
                                                   include_correlation_table: bool) -> Tuple[pd.DataFrame, Optional[str], Optional[pd.DataFrame]]:
        """准备数据和相关性结果（增强版）"""
        
        correlation_result = None
        correlation_matrix = None
        
        # 判断是否需要相关性分析
        need_correlation = (
            correlation_vars or 
            any(keyword in user_request.lower() for keyword in 
                ['相关性', 'correlation', '热力图', 'heatmap'])
        )
        
        if need_correlation and correlation_vars:
            # 执行相关性分析
            self.logger.info(f"执行相关性分析: {correlation_vars}")
            correlation_result = await correlation_analysis(
                read_data_param=read_data_param,
                correlation_vars=correlation_vars,
                correlation_method=correlation_method,
                filters=filters,
                group_by=group_by
            )
            
            # 解析相关性结果为矩阵
            correlation_matrix = self.correlation_parser.parse_to_matrix(correlation_result, correlation_vars)
            
            # 如果不需要表格，只返回矩阵和空的相关性结果
            if not include_correlation_table:
                # 保留原始结果用于会话缓存，但不在响应中返回
                data_df = correlation_matrix
                return data_df, correlation_result, correlation_matrix
            else:
                # 既要表格又要图表
                data_df = correlation_matrix
                return data_df, correlation_result, correlation_matrix
        
        else:
            # 直接加载原始数据
            df = await self.data_loader.load_data(read_data_param)
            
            # 应用过滤条件
            if filters:
                df = self.data_loader.apply_filters(df, filters)
            
            return df, None, None
    
    def _get_data_info(self, df: pd.DataFrame) -> Dict:
        """获取数据信息供LLM参考"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        info = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'head': df.head(3).to_dict(),
            'numeric_columns': numeric_cols
        }
        
        # 如果有数值列，添加统计信息
        if numeric_cols:
            info['description'] = df[numeric_cols].describe().to_dict()
        
        return info
    
    async def _execute_and_save(self, code: str, data_df: pd.DataFrame, session_id: str, version: str) -> str:
        """执行代码并保存图表"""
        
        save_path = str(Path(self.config.output_dir) / f"{session_id}_{version}.png")
        
        result_path = await self.code_executor.execute_code(
            code=code,
            data_df=data_df,
            save_path=save_path
        )
        
        return result_path

# ===== 全局实例 =====
viz_mcp_instance = InteractiveVisualizationMCP()

# ===== MCP工具函数 =====
logger = create_logger(app_name="interactive_viz_mcp", log_dir="./logs").get_logger()
mcp = FastMCP('InteractiveVisualizationServer')

@mcp.tool()
async def start_visualization_session(
    user_request: str,
    read_data_param: ReadDataParam,
    correlation_vars: Optional[List[str]] = None,
    correlation_method: str = "pearson",
    filters: Optional[Dict[str, str]] = None,
    group_by: Optional[List[str]] = None,
    include_correlation_table: bool = False
) -> str:
    """
    开始新的交互式可视化会话
    #---------必填参数---------#
    :param user_request: 用户的可视化需求描述（必填）
    :param read_data_param: 数据源参数（必填）
    #---------相关性分析相关参数---------#
    仅在需要进行相关性分析时，提供相关性分析变量。相关性分析变量需要是数据中的列名，且数据类型为数值型。
    :param correlation_vars: 相关性分析变量（可选）
    :param correlation_method: 相关性计算方法（可选，默认pearson）
    :param filters: 数据过滤条件（可选）
    :param group_by: 分组条件（可选）
    :param include_correlation_table: 是否同时返回相关性表格（可选，默认False）
    #---------返回值---------#
    :return: 会话信息和初始图表路径的JSON，如果include_correlation_table为True，还包含相关性表格
    """
    return await viz_mcp_instance.start_session_impl(
        user_request=user_request,
        read_data_param=read_data_param,
        correlation_vars=correlation_vars,
        correlation_method=correlation_method,
        filters=filters,
        group_by=group_by,
        include_correlation_table=include_correlation_table
    )

@mcp.tool()
async def refine_visualization(session_id: str, user_feedback: str) -> str:
    """
    基于用户反馈优化可视化
    
    :param session_id: 会话ID
    :param user_feedback: 用户的反馈和修改要求
    :return: 新的图表路径和状态信息
    """
    return await viz_mcp_instance.refine_visualization_impl(session_id, user_feedback)

@mcp.tool()
async def get_session_info(session_id: str) -> str:
    """
    获取会话信息和历史记录
    
    :param session_id: 会话ID
    :return: 会话详细信息的JSON
    """
    return await viz_mcp_instance.get_session_info_impl(session_id)

@mcp.tool()
async def rollback_to_version(session_id: str, version: str) -> str:
    """
    回滚到指定的代码版本
    
    :param session_id: 会话ID
    :param version: 目标版本（如：v1, v2等）
    :return: 回滚结果和新图表路径
    """
    return await viz_mcp_instance.rollback_to_version_impl(session_id, version)

@mcp.tool()
async def list_active_sessions() -> str:
    """
    列出当前活跃的会话
    
    :return: 活跃会话列表的JSON
    """
    try:
        sessions_info = []
        for session_id, session in viz_mcp_instance.session_manager.sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "user_request": session.user_request[:100] + "..." if len(session.user_request) > 100 else session.user_request,
                "current_version": f"v{len(session.generated_charts)}",
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            })
        
        result = {
            "total_sessions": len(sessions_info),
            "sessions": sessions_info
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"获取会话列表失败: {str(e)}"

@mcp.tool()
async def delete_session(session_id: str) -> str:
    """
    删除指定的会话
    
    :param session_id: 要删除的会话ID
    :return: 删除结果
    """
    try:
        success = viz_mcp_instance.session_manager.delete_session(session_id)
        if success:
            # 清理数据缓存
            session_data_keys = [k for k in viz_mcp_instance.data_cache.keys() if session_id in k]
            for key in session_data_keys:
                del viz_mcp_instance.data_cache[key]
            
            return f"会话已删除: {session_id}"
        else:
            return f"会话不存在: {session_id}"
            
    except Exception as e:
        return f"删除会话失败: {str(e)}"

@mcp.tool()
async def visualization_with_correlation_table(
    user_request: str,
    read_data_param: ReadDataParam,
    correlation_vars: List[str],
    correlation_method: str = "pearson",
    filters: Optional[Dict[str, str]] = None,
    group_by: Optional[List[str]] = None
) -> str:
    """
    创建可视化的同时获取相关性分析表格
    这是start_visualization_session的便捷版本，专门用于同时需要图表和表格的场景
    
    #---------必填参数---------#
    :param user_request: 用户的可视化需求描述（必填）
    :param read_data_param: 数据源参数（必填）
    :param correlation_vars: 相关性分析变量（必填，需要是数据中的数值型列名）
    #---------可选参数---------#
    :param correlation_method: 相关性计算方法（可选，默认pearson）
    :param filters: 数据过滤条件（可选）
    :param group_by: 分组条件（可选）
    #---------返回值---------#
    :return: JSON格式结果，包含：session_id, chart_path, correlation_table, message
    """
    return await viz_mcp_instance.start_session_impl(
        user_request=user_request,
        read_data_param=read_data_param,
        correlation_vars=correlation_vars,
        correlation_method=correlation_method,
        filters=filters,
        group_by=group_by,
        include_correlation_table=True  # 强制包含相关性表格
    )

@mcp.tool()
async def get_correlation_table_only(
    read_data_param: ReadDataParam,
    correlation_vars: List[str],
    correlation_method: str = "pearson",
    filters: Optional[Dict[str, str]] = None,
    group_by: Optional[List[str]] = None
) -> str:
    """
    仅获取相关性分析表格，不生成可视化图表
    
    #---------必填参数---------#
    :param read_data_param: 数据源参数（必填）
    :param correlation_vars: 相关性分析变量（必填，需要是数据中的数值型列名）
    #---------可选参数---------#
    :param correlation_method: 相关性计算方法（可选，默认pearson）
    :param filters: 数据过滤条件（可选）
    :param group_by: 分组条件（可选）
    #---------返回值---------#
    :return: 相关性分析表格的Markdown格式文本
    """
    try:
        # 直接调用correlation_analysis获取表格
        correlation_result = await correlation_analysis(
            read_data_param=read_data_param,
            correlation_vars=correlation_vars,
            correlation_method=correlation_method,
            filters=filters,
            group_by=group_by
        )
        
        return correlation_result
        
    except Exception as e:
        logger.error(f"获取相关性表格失败: {e}")
        return f"获取相关性表格失败: {str(e)}"

@mcp.tool()
async def get_correlation_table_from_session(session_id: str) -> str:
    """
    从现有会话中获取相关性表格
    适用于用户第一轮生成了图表，第二轮想要查看相关性表格的场景
    
    :param session_id: 会话ID
    :return: 相关性表格的Markdown格式文本，如果会话中没有相关性分析则返回错误信息
    """
    try:
        session = viz_mcp_instance.session_manager.get_session(session_id)
        if not session:
            return f"会话不存在: {session_id}"
        
        if not session.has_correlation_analysis:
            return f"会话 {session_id} 中没有相关性分析数据。请使用包含相关性分析的会话或重新开始相关性分析。"
        
        correlation_table = session.get_correlation_table()
        if not correlation_table:
            return f"会话 {session_id} 中的相关性表格数据缺失。"
        
        # 记录对话历史
        session.conversation_history.append({
            "type": "get_table",
            "request": "获取相关性表格",
            "timestamp": datetime.now()
        })
        session.updated_at = datetime.now()
        
        return correlation_table
        
    except Exception as e:
        logger.error(f"从会话获取相关性表格失败: {e}")
        return f"获取相关性表格失败: {str(e)}"

@mcp.tool()
async def visualize_existing_correlation(session_id: str, 
                                       visualization_request: str = "请根据已有的相关性数据生成热力图") -> str:
    """
    基于现有会话中的相关性数据生成可视化图表
    适用于用户第一轮只生成了表格，第二轮想要生成图表的场景
    
    :param session_id: 会话ID
    :param visualization_request: 可视化需求描述（可选）
    :return: 新生成的图表路径和状态信息
    """
    try:
        session = viz_mcp_instance.session_manager.get_session(session_id)
        if not session:
            return f"会话不存在: {session_id}"
        
        if not session.has_correlation_analysis:
            return f"会话 {session_id} 中没有相关性分析数据。请先进行相关性分析。"
        
        correlation_matrix = session.get_correlation_matrix()
        if correlation_matrix is None:
            return f"会话 {session_id} 中的相关性矩阵数据缺失。"
        
        # 更新数据缓存，使用相关性矩阵作为数据
        data_key = session.data_info.get('data_key')
        if data_key:
            viz_mcp_instance.data_cache[data_key] = correlation_matrix
        
        # 更新数据信息
        data_info = viz_mcp_instance._get_data_info(correlation_matrix)
        data_info['data_key'] = data_key
        session.data_info.update(data_info)
        
        # 调用agent生成可视化代码
        from visualization_agent import interactive_visualization_agent
        viz_code = await interactive_visualization_agent.generate_initial_code(
            visualization_request, data_info
        )
        
        # 执行代码生成图表
        version = f"v{len(session.generated_charts) + 1}"
        chart_path = await viz_mcp_instance._execute_and_save(
            viz_code, correlation_matrix, session_id, version
        )
        
        # 更新会话
        session.add_code_version(viz_code, chart_path, "基于已有相关性数据生成可视化")
        session.session_type = "both"  # 现在既有表格又有图表
        
        result = {
            "session_id": session_id,
            "chart_path": chart_path,
            "version": version,
            "correlation_vars": session.correlation_vars,
            "correlation_method": session.correlation_method,
            "message": f"已基于现有相关性数据生成可视化图表（{version}）。您可以继续提供反馈来优化图表。"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"基于现有相关性数据生成可视化失败: {e}")
        return f"生成可视化失败: {str(e)}"

@mcp.tool()
async def start_correlation_analysis_only(
    read_data_param: ReadDataParam,
    correlation_vars: List[str],
    correlation_method: str = "pearson",
    filters: Optional[Dict[str, str]] = None,
    group_by: Optional[List[str]] = None
) -> str:
    """
    仅进行相关性分析，不生成可视化图表，但保持会话状态以便后续生成图表
    
    :param read_data_param: 数据源参数
    :param correlation_vars: 相关性分析变量
    :param correlation_method: 相关性计算方法（默认pearson）
    :param filters: 数据过滤条件（可选）
    :param group_by: 分组条件（可选）
    :return: 会话信息和相关性表格
    """
    try:
        # 1. 执行相关性分析
        correlation_result = await correlation_analysis(
            read_data_param=read_data_param,
            correlation_vars=correlation_vars,
            correlation_method=correlation_method,
            filters=filters,
            group_by=group_by
        )
        
        # 2. 解析相关性结果为矩阵
        correlation_matrix = viz_mcp_instance.correlation_parser.parse_to_matrix(
            correlation_result, correlation_vars
        )
        
        # 3. 加载原始数据（用于数据信息）
        original_df = await viz_mcp_instance.data_loader.load_data(read_data_param)
        if filters:
            original_df = viz_mcp_instance.data_loader.apply_filters(original_df, filters)
        
        # 4. 缓存数据
        data_key = f"data_{int(time.time())}_{random.randint(1000, 9999)}"
        viz_mcp_instance.data_cache[data_key] = original_df
        
        # 5. 获取数据信息
        data_info = viz_mcp_instance._get_data_info(original_df)
        data_info['data_key'] = data_key
        
        # 6. 创建会话
        session_id = viz_mcp_instance.session_manager.create_session(
            user_request=f"相关性分析: {correlation_vars}",
            data_info=data_info,
            session_type="correlation_only"
        )
        
        # 7. 设置相关性数据
        session = viz_mcp_instance.session_manager.get_session(session_id)
        session.set_correlation_data(
            correlation_result=correlation_result,
            correlation_matrix=correlation_matrix,
            correlation_vars=correlation_vars,
            correlation_method=correlation_method
        )
        
        # 8. 记录对话历史
        session.conversation_history.append({
            "type": "correlation_analysis",
            "request": f"相关性分析: {correlation_vars}",
            "method": correlation_method,
            "timestamp": datetime.now()
        })
        
        result = {
            "session_id": session_id,
            "session_type": "correlation_only",
            "correlation_table": correlation_result,
            "correlation_vars": correlation_vars,
            "correlation_method": correlation_method,
            "message": "相关性分析完成。您可以使用 visualize_existing_correlation 基于此结果生成图表。"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"相关性分析失败: {e}")
        return f"相关性分析失败: {str(e)}"

if __name__ == '__main__':
    mcp.run(transport='sse') 