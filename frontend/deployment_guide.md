# 智能数据分析系统部署指南

## 🚀 快速开始

### 1. 启动相关性分析服务器（已有）
```bash
cd analysis-agent/server
python corr_server.py
```
服务器将在 `http://127.0.0.1:8000/sse` 启动

### 2. 启动通用分析后端
```bash
cd analysis-agent/frontend
python backend.py
```
后端将在 `http://127.0.0.1:8001` 启动

### 3. 测试系统状态
```bash
curl http://localhost:8001/status
```

## 📋 系统要求

### Python依赖
```bash
pip install fastapi uvicorn pandas numpy scikit-learn
pip install mcp agents  # 根据实际MCP库安装
```

### 目录结构
```
analysis-agent/
├── frontend/
│   ├── backend.py                          # 通用分析后端
│   ├── intelligent_analysis_backend_guide.md
│   ├── deployment_guide.md
│   └── example_new_server.py               # 新服务器示例
├── server/
│   ├── corr_server.py                      # 相关性分析服务器
│   └── corr_final.py                       # 相关性分析核心逻辑
└── custom_types/
    └── types.py                            # 共享数据类型
```

## 🔧 添加新分析功能

### 步骤1：创建新的MCP服务器

以回归分析为例：

```python
# 创建 regression_server.py
from mcp.server.fastmcp import FastMCP
from custom_types.types import ReadDataParam

mcp = FastMCP('RegressionServer')

@mcp.tool()
async def linear_regression_analysis(
    read_data_param: ReadDataParam,
    target_variable: str,
    feature_variables: List[str],
    **kwargs
) -> str:
    # 实现回归分析逻辑
    pass

if __name__ == '__main__':
    mcp.run(transport='sse', port=8002)  # 使用新端口
```

### 步骤2：更新后端配置

在 `backend.py` 中更新 `MCP_SERVERS_CONFIG`：

```python
MCP_SERVERS_CONFIG["regression"] = MCPServerConfig(
    name="regression",
    url="http://127.0.0.1:8002/sse",
    analysis_types=[AnalysisType.REGRESSION],
    enabled=True  # 设为True启用
)
```

### 步骤3：启动新服务器

```bash
python regression_server.py
```

### 步骤4：重启后端

```bash
# 停止现有后端 (Ctrl+C)
python backend.py
```

## 🌐 API使用示例

### 基础分析请求
```python
import requests

# 相关性分析
response = requests.post("http://localhost:8001/analyze", json={
    "message": "分析温度和湿度的相关性",
    "analysis_type": "correlation"
})

print(response.json()["result"])
```

### 带上下文的分析
```python
response = requests.post("http://localhost:8001/analyze", json={
    "message": "请分析销售数据中价格对销量的影响",
    "analysis_type": "regression",
    "context": {
        "dataset": "sales_data.csv",
        "priority": "high"
    }
})
```

### 对话式分析
```python
# 第一轮
response1 = requests.post("http://localhost:8001/analyze", json={
    "message": "我有一个客户数据集，想做聚类分析"
})

# 第二轮，带历史
response2 = requests.post("http://localhost:8001/analyze", json={
    "message": "请使用K-means算法，分成5个群组",
    "conversation_history": response1.json()["conversation_history"],
    "analysis_type": "clustering"
})
```

## 🔍 系统监控

### 检查系统状态
```bash
curl http://localhost:8001/status
```

### 查看支持的分析类型
```bash
curl http://localhost:8001/analysis-types
```

### 动态管理服务器
```bash
# 启用服务器
curl -X POST http://localhost:8001/servers/regression/enable

# 禁用服务器
curl -X POST http://localhost:8001/servers/regression/disable

# 添加新服务器
curl -X POST http://localhost:8001/servers/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "clustering",
    "url": "http://127.0.0.1:8003/sse",
    "analysis_types": ["clustering"],
    "enabled": true
  }'
```

## 📊 生产环境部署

### 使用Docker部署

创建 `Dockerfile`：
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["python", "backend.py"]
```

创建 `docker-compose.yml`：
```yaml
version: '3.8'
services:
  correlation-server:
    build: 
      context: ./server
    ports:
      - "8000:8000"
    
  regression-server:
    build:
      context: ./regression
    ports:
      - "8002:8002"
    
  analysis-backend:
    build:
      context: ./frontend
    ports:
      - "8001:8001"
    depends_on:
      - correlation-server
      - regression-server
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🛠️ 开发最佳实践

### 1. 服务器开发规范

```python
# 每个分析服务器应该：
# 1. 使用统一的数据类型 (ReadDataParam)
# 2. 返回Markdown格式的结果
# 3. 包含详细的错误处理
# 4. 提供完整的文档字符串

@mcp.tool()
async def your_analysis_function(
    read_data_param: ReadDataParam,
    # 其他参数...
    **kwargs
) -> str:
    """
    详细的函数说明
    
    Args:
        read_data_param: 数据读取参数
        # 其他参数说明...
        
    Returns:
        str: Markdown格式的分析结果
    """
    try:
        # 实现分析逻辑
        pass
    except Exception as e:
        return f"❌ **分析过程中出现错误**: {str(e)}"
```

### 2. 错误处理策略

```python
# 在后端中实现优雅降级
try:
    # 尝试使用指定的分析类型
    result = await analyze_with_specific_type(request)
except Exception:
    # 降级到通用分析
    result = await analyze_with_general_agent(request)
```

### 3. 性能优化

```python
# 使用连接池
import aiohttp

class MCPServerManager:
    def __init__(self):
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        await self.session.close()
```

### 4. 日志和监控

```python
# 添加详细的日志记录
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
```

## 🔒 安全考虑

### 1. 文件访问安全
```python
import os
from pathlib import Path

def validate_file_path(file_path: str) -> bool:
    """验证文件路径安全性"""
    try:
        # 解析路径
        path = Path(file_path).resolve()
        
        # 检查是否在允许的目录内
        allowed_dirs = ["/data", "/uploads"]
        return any(str(path).startswith(allowed_dir) for allowed_dir in allowed_dirs)
    except:
        return False
```

### 2. 输入验证
```python
from pydantic import validator

class AnalysisRequest(BaseModel):
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if len(v) > 10000:  # 限制消息长度
            raise ValueError('消息过长')
        return v
```

### 3. 速率限制
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/analyze")
@limiter.limit("10/minute")  # 每分钟最多10次请求
async def analyze_data(request: Request, analysis_request: AnalysisRequest):
    # 分析逻辑
    pass
```

## 🐛 故障排除

### 常见问题及解决方案

1. **MCP服务器连接失败**
   ```bash
   # 检查服务器是否启动
   netstat -tlnp | grep :8000
   
   # 检查防火墙设置
   sudo ufw status
   
   # 查看服务器日志
   tail -f logs/correlation-server.log
   ```

2. **分析结果异常**
   ```python
   # 在分析函数中添加调试信息
   logger.debug(f"输入数据形状: {df.shape}")
   logger.debug(f"数据列名: {df.columns.tolist()}")
   ```

3. **性能问题**
   ```bash
   # 监控系统资源
   htop
   
   # 检查内存使用
   free -h
   
   # 分析慢查询
   tail -f logs/performance.log | grep "slow"
   ```

### 调试模式启动

```bash
# 启动时启用调试模式
export DEBUG=true
python backend.py

# 或者在代码中设置
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        debug=True,  # 启用调试模式
        reload=True  # 启用自动重载
    )
```

## 📈 扩展计划

### 即将支持的分析类型

1. **聚类分析** (clustering)
   - K-means聚类
   - 层次聚类
   - DBSCAN聚类

2. **分类分析** (classification)
   - 逻辑回归
   - 决策树
   - 随机森林

3. **时间序列分析** (time_series)
   - ARIMA模型
   - 季节性分解
   - 趋势分析

4. **描述性统计** (descriptive)
   - 基础统计量
   - 分布分析
   - 异常值检测

### 功能增强计划

- 🔄 **自动化工作流**: 支持多步骤分析流程
- 📊 **可视化集成**: 自动生成图表和可视化
- 🤖 **智能推荐**: 基于数据特征推荐最佳分析方法
- 🔗 **数据源集成**: 支持数据库、API等多种数据源
- 📱 **移动端支持**: 提供移动端友好的API

通过这个通用的智能数据分析后端系统，您可以轻松构建一个功能强大、可扩展的数据分析平台！ 