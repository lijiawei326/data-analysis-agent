import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import time
from enum import Enum
from dataclasses import dataclass
from agents import Agent, Runner, ToolCallOutputItem
from agents.mcp.server import MCPServerSse, MCPServerSseParams
from agent_mcp.corr_agent import conversation_agent
from utils.utils import remove_think
from logger_config import create_logger

# 创建针对此应用的日志器
app_logger = create_logger(
    app_name="intelligent-analysis-agent",
    log_dir="./logs"
)
logger = app_logger.get_logger()

# 分析类型枚举
class AnalysisType(str, Enum):
    CORRELATION = "correlation"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    TIME_SERIES = "time_series"
    DESCRIPTIVE = "descriptive"
    STATISTICAL_TEST = "statistical_test"
    CUSTOM = "custom"

# MCP服务器配置
@dataclass
class MCPServerConfig:
    name: str
    url: str
    timeout: int = 180
    enabled: bool = True
    analysis_types: List[AnalysisType] = None

# 预定义的MCP服务器配置
MCP_SERVERS_CONFIG = {
    "correlation": MCPServerConfig(
        name="correlation",
        url="http://127.0.0.1:8000/sse",
        analysis_types=[AnalysisType.CORRELATION]
    ),
    "regression": MCPServerConfig(
        name="regression", 
        url="http://127.0.0.1:8001/sse",
        analysis_types=[AnalysisType.REGRESSION],
        enabled=False  # 待实现
    ),
    "clustering": MCPServerConfig(
        name="clustering",
        url="http://127.0.0.1:8002/sse", 
        analysis_types=[AnalysisType.CLUSTERING],
        enabled=False  # 待实现
    ),
    "statistics": MCPServerConfig(
        name="statistics",
        url="http://127.0.0.1:8003/sse",
        analysis_types=[AnalysisType.DESCRIPTIVE, AnalysisType.STATISTICAL_TEST],
        enabled=False  # 待实现
    )
}

app = FastAPI(
    title="智能数据分析系统", 
    version="2.0.0",
    description="通用智能数据分析后端，支持相关性分析、回归分析、聚类分析等多种数据分析功能"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储MCP连接和Agent
mcp_servers: Dict[str, MCPServerSse] = {}
analysis_agent: Optional[Agent] = None

# 请求和响应模型
class AnalysisRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict]] = []
    analysis_type: Optional[AnalysisType] = None
    context: Optional[Dict[str, Any]] = {}

class AnalysisResponse(BaseModel):
    result: str
    conversation_history: Optional[List[Dict]] = []
    analysis_type: Optional[AnalysisType] = None
    metadata: Optional[Dict[str, Any]] = {}

class ServerStatus(BaseModel):
    server_name: str
    status: str
    analysis_types: List[str]
    last_check: str

class SystemStatus(BaseModel):
    status: str
    active_servers: List[ServerStatus]
    total_servers: int
    enabled_servers: int

class MCPServerManager:
    """MCP服务器管理器"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerSse] = {}
        self.server_configs = MCP_SERVERS_CONFIG
    
    async def initialize_server(self, server_name: str, config: MCPServerConfig) -> bool:
        """初始化单个MCP服务器"""
        if not config.enabled:
            logger.info(f"服务器 {server_name} 已禁用，跳过初始化")
            return False
            
        try:
            mcp_param = MCPServerSseParams(
                url=config.url
            )
            server = MCPServerSse(
                name=config.name,
                params=mcp_param,
                client_session_timeout_seconds=config.timeout
            )
            await server.connect()
            self.servers[server_name] = server
            logger.info(f"MCP服务器 {server_name} 连接成功: {config.url}")
            return True
        except Exception as e:
            logger.error(f"MCP服务器 {server_name} 连接失败: {e}")
            return False
    
    async def initialize_all_servers(self) -> Dict[str, bool]:
        """初始化所有启用的MCP服务器"""
        results = {}
        for server_name, config in self.server_configs.items():
            results[server_name] = await self.initialize_server(server_name, config)
        return results
    
    async def add_server(self, server_name: str, config: MCPServerConfig) -> bool:
        """动态添加新的MCP服务器"""
        self.server_configs[server_name] = config
        return await self.initialize_server(server_name, config)
    
    def get_servers_for_analysis_type(self, analysis_type: AnalysisType) -> List[MCPServerSse]:
        """根据分析类型获取相应的MCP服务器"""
        matching_servers = []
        for server_name, config in self.server_configs.items():
            if (config.enabled and 
                config.analysis_types and 
                analysis_type in config.analysis_types and
                server_name in self.servers):
                matching_servers.append(self.servers[server_name])
        return matching_servers
    
    def get_all_active_servers(self) -> List[MCPServerSse]:
        """获取所有活跃的MCP服务器"""
        return list(self.servers.values())
    
    async def health_check(self) -> Dict[str, bool]:
        """检查所有服务器的健康状态"""
        health_status = {}
        for server_name, server in self.servers.items():
            try:
                # 这里可以添加具体的健康检查逻辑
                health_status[server_name] = True
            except Exception as e:
                logger.error(f"服务器 {server_name} 健康检查失败: {e}")
                health_status[server_name] = False
        return health_status

class IntelligentAnalysisAgent:
    """智能分析Agent管理器"""
    
    def __init__(self, server_manager: MCPServerManager):
        self.server_manager = server_manager
        self.agent = None
        self.initialize_agent()
    
    def initialize_agent(self):
        """初始化通用分析Agent"""
        self.agent = Agent(
            name='intelligent_analysis_assistant',
            instructions='''你是一个智能数据分析助手，能够执行多种类型的数据分析任务。

你的能力包括但不限于：
1. 相关性分析 - 分析变量间的相关关系
2. 回归分析 - 建立预测模型
3. 聚类分析 - 发现数据中的群组模式
4. 分类分析 - 构建分类模型
5. 时间序列分析 - 分析时间相关的数据模式
6. 描述性统计 - 提供数据的基本统计信息
7. 统计检验 - 执行各种统计假设检验

工作流程：
1. 理解用户的分析需求
2. 选择合适的分析方法和工具
3. 执行分析并解释结果
4. 提供可视化建议和后续分析建议

请始终：
- 使用简体中文回复
- 提供清晰的分析结果解释
- 给出实用的建议和见解
- 在需要时询问澄清问题
- **严格复用用户对变量的描述，不要简化与转换**''',
            model=conversation_agent.model,
            tool_use_behavior=conversation_agent.tool_use_behavior
        )
    
    def update_agent_tools(self, analysis_type: Optional[AnalysisType] = None):
        """根据分析类型更新Agent的可用工具"""
        if analysis_type:
            # 获取特定分析类型的服务器
            servers = self.server_manager.get_servers_for_analysis_type(analysis_type)
        else:
            # 获取所有活跃服务器
            servers = self.server_manager.get_all_active_servers()
        
        # 清除现有的MCP服务器
        self.agent.mcp_servers.clear()
        
        # 添加相关的MCP服务器
        for server in servers:
            self.agent.mcp_servers.append(server)
        
        logger.info(f"Agent工具已更新，当前可用服务器数量: {len(servers)}")

# 全局管理器实例
server_manager = MCPServerManager()
analysis_agent_manager = IntelligentAnalysisAgent(server_manager)

async def initialize_system():
    """初始化整个分析系统"""
    logger.info("开始初始化智能数据分析系统...")
    
    # 初始化MCP服务器
    server_results = await server_manager.initialize_all_servers()
    
    # 更新Agent工具
    analysis_agent_manager.update_agent_tools()
    
    # 记录初始化结果
    enabled_count = sum(1 for success in server_results.values() if success)
    total_count = len(server_results)
    
    logger.info(f"系统初始化完成: {enabled_count}/{total_count} 个服务器成功启动")
    
    for server_name, success in server_results.items():
        status = "成功" if success else "失败"
        logger.info(f"  - {server_name}: {status}")
    
    return enabled_count > 0

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    success = await initialize_system()
    if not success:
        logger.warning("警告: 没有成功启动任何MCP服务器，系统功能可能受限")

@app.get("/")
async def root():
    return {
        "message": "智能数据分析系统API",
        "version": "2.0.0",
        "description": "支持多种数据分析功能的通用后端系统"
    }

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    health_status = await server_manager.health_check()
    
    active_servers = []
    for server_name, config in server_manager.server_configs.items():
        if server_name in server_manager.servers:
            status = "healthy" if health_status.get(server_name, False) else "unhealthy"
            analysis_types = [at.value for at in (config.analysis_types or [])]
            active_servers.append(ServerStatus(
                server_name=server_name,
                status=status,
                analysis_types=analysis_types,
                last_check=time.strftime("%Y-%m-%d %H:%M:%S")
            ))
    
    enabled_servers = len([s for s in active_servers if s.status == "healthy"])
    
    return SystemStatus(
        status="healthy" if enabled_servers > 0 else "degraded",
        active_servers=active_servers,
        total_servers=len(server_manager.server_configs),
        enabled_servers=enabled_servers
    )

@app.get("/analysis-types")
async def get_supported_analysis_types():
    """获取支持的分析类型"""
    supported_types = {}
    for server_name, config in server_manager.server_configs.items():
        if config.enabled and config.analysis_types:
            for analysis_type in config.analysis_types:
                if analysis_type.value not in supported_types:
                    supported_types[analysis_type.value] = []
                supported_types[analysis_type.value].append(server_name)
    
    return {
        "supported_analysis_types": supported_types,
        "total_types": len(supported_types)
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(request: AnalysisRequest):
    """执行数据分析"""
    start_time = time.time()
    logger.info(f"收到分析请求: {request.message[:100]}...")
    
    # 记录用户输入
    app_logger.log_user_action("发送分析请求", {
        "message": request.message,
        "analysis_type": request.analysis_type.value if request.analysis_type else "auto",
        "context": request.context
    })
    
    # 检查Agent是否可用
    if analysis_agent_manager.agent is None:
        logger.warning("Agent未初始化，正在重新初始化...")
        success = await initialize_system()
        if not success:
            logger.error("系统初始化失败")
            raise HTTPException(status_code=500, detail="分析系统初始化失败")
    
    try:
        logger.info("开始执行数据分析...")
        
        # 根据分析类型更新Agent工具
        if request.analysis_type:
            analysis_agent_manager.update_agent_tools(request.analysis_type)
            logger.info(f"已切换到 {request.analysis_type.value} 分析模式")
        
        # 准备对话历史
        conversation_history = request.conversation_history or []
        logger.info(f"当前对话历史长度: {len(conversation_history)}")
        
        
        # 构建增强的用户消息
        enhanced_message = request.message
        if request.analysis_type:
            enhanced_message = f"[分析类型: {request.analysis_type.value}] {request.message}"
        
        if request.context:
            context_info = ", ".join([f"{k}: {v}" for k, v in request.context.items()])
            enhanced_message += f" [上下文: {context_info}]"
        
        # 添加当前用户消息到历史
        conversation_history.append({"role": "user", "content": enhanced_message})
        
        # 运行Agent
        result = await Runner.run(
            starting_agent=analysis_agent_manager.agent,
            input=conversation_history
        )
        
        processing_time = time.time() - start_time
        logger.info(f"分析完成，耗时: {processing_time:.2f}秒")
        
        # 处理结果
        if isinstance(result.new_items[-1], ToolCallOutputItem):
            logger.info('输出为工具调用结果')
            try:
                result_data = json.loads(result.final_output)
                result_text = result_data.get('text', str(result.final_output))
            except json.JSONDecodeError:
                result_text = str(result.final_output)
        else:
            logger.info('输出为模型输出')
            result_text = result.final_output
        
        # 构建响应元数据
        metadata = {
            "processing_time": f"{processing_time:.2f}s",
            "analysis_mode": request.analysis_type.value if request.analysis_type else "auto",
            "active_servers": len(server_manager.get_all_active_servers()),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 记录分析结果和性能
        app_logger.log_with_tag("info", f"分析完成: {result_text[:200]}...", "ANALYSIS")
        
        app_logger.log_performance("Data Analysis", processing_time)
        
        # 更新对话历史
        final_conversation_history = result.to_input_list()
        logger.info(f'历史对话：\n{final_conversation_history}')
        # 记录业务事件
        app_logger.log_business_event("数据分析完成", {
            "分析类型": request.analysis_type.value if request.analysis_type else "auto",
            "对话轮次": len(final_conversation_history)//2,
            "处理时间": f"{processing_time:.2f}s",
            "成功": True
        })
        
        return AnalysisResponse(
            result=result_text,
            conversation_history=final_conversation_history,
            analysis_type=request.analysis_type,
            metadata=metadata
        )
        
    except asyncio.TimeoutError:
        error_time = time.time() - start_time
        logger.error("分析任务超时")
        app_logger.log_with_tag("error", f"分析超时 - 请求: {request.message[:50]}...", "ANALYSIS")
        app_logger.log_business_event("数据分析失败", {
            "原因": "超时",
            "处理时间": f"{error_time:.2f}s"
        })
        raise HTTPException(status_code=504, detail="分析任务超时，请稍后重试")
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"执行分析时出错 (耗时: {error_time:.2f}秒): {str(e)}")
        app_logger.log_error_with_context(e, {
            "用户请求": request.message[:50],
            "分析类型": request.analysis_type.value if request.analysis_type else "auto",
            "处理时间": f"{error_time:.2f}s"
        })
        app_logger.log_business_event("数据分析失败", {
            "原因": str(e),
            "处理时间": f"{error_time:.2f}s"
        })
        raise HTTPException(status_code=500, detail=f"执行分析时出错: {str(e)}")

@app.post("/chat", response_model=AnalysisResponse)
async def chat(request: AnalysisRequest):
    """兼容性接口：处理对话请求（重定向到analyze接口）"""
    return await analyze_data(request)

@app.post("/reset")
async def reset_conversation():
    """重置对话"""
    logger.info("对话已重置")
    app_logger.log_business_event("会话重置")
    return {"message": "对话已重置"}

@app.post("/servers/{server_name}/enable")
async def enable_server(server_name: str):
    """启用指定的MCP服务器"""
    if server_name not in server_manager.server_configs:
        raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
    
    config = server_manager.server_configs[server_name]
    config.enabled = True
    
    success = await server_manager.initialize_server(server_name, config)
    if success:
        analysis_agent_manager.update_agent_tools()
        logger.info(f"服务器 {server_name} 已启用")
        return {"message": f"服务器 {server_name} 启用成功"}
    else:
        raise HTTPException(status_code=500, detail=f"启用服务器 {server_name} 失败")

@app.post("/servers/{server_name}/disable")
async def disable_server(server_name: str):
    """禁用指定的MCP服务器"""
    if server_name not in server_manager.server_configs:
        raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
    
    config = server_manager.server_configs[server_name]
    config.enabled = False
    
    if server_name in server_manager.servers:
        del server_manager.servers[server_name]
    
    analysis_agent_manager.update_agent_tools()
    logger.info(f"服务器 {server_name} 已禁用")
    return {"message": f"服务器 {server_name} 已禁用"}

@app.post("/servers/add")
async def add_server(server_config: dict):
    """动态添加新的MCP服务器"""
    try:
        server_name = server_config["name"]
        config = MCPServerConfig(**server_config)
        
        success = await server_manager.add_server(server_name, config)
        if success:
            analysis_agent_manager.update_agent_tools()
            return {"message": f"服务器 {server_name} 添加成功"}
        else:
            raise HTTPException(status_code=500, detail=f"添加服务器 {server_name} 失败")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加服务器失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 