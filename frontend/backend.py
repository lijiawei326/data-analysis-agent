import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import time
from agents import Agent, Runner, ToolCallOutputItem
from agents.mcp.server import MCPServerSse, MCPServerSseParams
from agent_mcp.corr_agent import conversation_agent
from utils.utils import remove_think
from logger_config import create_logger

# 创建针对此应用的日志器
app_logger = create_logger(
    app_name="analysis-agent",
    log_dir="./logs"
)
logger = app_logger.get_logger()

app = FastAPI(title="智能分析对话系统", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储MCP连接和Agent
mcp_server = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict]] = []

class ChatResponse(BaseModel):
    result: str
    conversation_history: Optional[List[Dict]] = []

async def initialize_mcp():
    """初始化MCP服务器连接"""
    global mcp_server
    try:
        mcp_param = MCPServerSseParams(
            url='http://127.0.0.1:8000/sse'
        )
        mcp_server = MCPServerSse(
            name='corr',
            params=mcp_param,
            client_session_timeout_seconds=180
        )
        await mcp_server.connect()
        logger.info("MCP服务器连接成功")
        return True
    except Exception as e:
        logger.error(f"MCP服务器连接失败: {e}")
        return False

async def initialize_agent():
    """初始化分析Agent"""
    global conversation_agent, mcp_server
    
    if mcp_server is None:
        success = await initialize_mcp()
        if not success:
            return False
    
    try:
        conversation_agent.mcp_servers.append(mcp_server)
        logger.info("分析Agent初始化成功")
        return True
    except Exception as e:
        logger.error(f"分析Agent初始化失败: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await initialize_agent()

@app.get("/")
async def root():
    return {"message": "相关性分析对话系统API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理对话请求"""
    global conversation_agent
    
    start_time = time.time()
    logger.info(f"收到聊天请求: {request.message[:100]}...")
    
    # 记录用户输入
    app_logger.log_user_action("发送消息", request.message)
    
    if conversation_agent is None:
        logger.warning("Agent未初始化，正在重新初始化...")
        success = await initialize_agent()
        if not success:
            logger.error("Agent初始化失败")
            raise HTTPException(status_code=500, detail="Agent初始化失败")
    
    try:
        logger.info("开始运行Agent...")
        
        # 使用请求中的对话历史
        messagae = request.conversation_history or []
        logger.info(f"当前对话历史长度: {len(messagae)}")
        
        # 添加当前用户消息到历史
        messagae.append({"role": "user", "content": request.message})
        # 运行Agent
        result = await Runner.run(
            starting_agent=conversation_agent,
            input=messagae
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Agent运行完成，耗时: {processing_time:.2f}秒")
        logger.info(f"result.final_output: {result.final_output}")

        # 判断是否为工具调用结果，如果是，则返回工具调用结果，否则返回模型输出
        if isinstance(result.new_items[-1], ToolCallOutputItem):
            logger.info('输出为工具调用结果')
            result_data = json.loads(result.final_output)
            result_text = result_data.get('text', str(result.final_output))
        else:
            logger.info('输出为模型输出')
            result_text = result.final_output
        
        # 记录AI回复和性能
        app_logger.log_with_tag("info", f"AI回复: {result_text}", "CHAT")
        app_logger.log_performance("Chat Processing", processing_time)
        
        # 添加助手回复到历史
        conversation_history = result.to_input_list()
        logger.info(f"result_text: {result_text}")
        logger.info(f"conversation_history: {conversation_history}")
        
        # 记录对话统计信息
        app_logger.log_business_event("对话完成", {
            "轮次": len(conversation_history)//2,
            "历史长度": len(conversation_history),
            "处理时间": f"{processing_time:.2f}s"
        })
        
        return ChatResponse(result=result_text, conversation_history=conversation_history)
        
    except asyncio.TimeoutError:
        logger.error("Agent运行超时")
        app_logger.log_with_tag("error", f"对话超时 - 用户输入: {request.message[:50]}...", "CHAT")
        raise HTTPException(status_code=504, detail="分析任务超时，请稍后重试")
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"处理请求时出错 (耗时: {error_time:.2f}秒): {str(e)}")
        app_logger.log_error_with_context(e, {
            "用户输入": request.message[:50],
            "处理时间": f"{error_time:.2f}s"
        })
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

@app.post("/reset")
async def reset_conversation():
    """重置对话"""
    logger.info("对话已重置")
    app_logger.log_business_event("会话重置")
    return {"message": "对话已重置"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 