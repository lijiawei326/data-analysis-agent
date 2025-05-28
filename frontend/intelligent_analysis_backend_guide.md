# 智能数据分析后端系统指南

## 系统概述

这是一个通用的智能数据分析后端系统，支持多种数据分析功能，具有高度的可扩展性。系统采用模块化架构，可以轻松添加新的分析功能和服务器。

## 核心特性

### 🎯 **多分析类型支持**
- **相关性分析** - 变量间相关关系分析
- **回归分析** - 预测模型构建（待实现）
- **聚类分析** - 数据群组发现（待实现）
- **分类分析** - 分类模型构建（待实现）
- **时间序列分析** - 时间数据模式分析（待实现）
- **描述性统计** - 基础统计信息（待实现）
- **统计检验** - 假设检验（待实现）
- **自定义分析** - 可扩展的自定义分析

### 🔧 **高可扩展性**
- **模块化MCP服务器管理**
- **动态服务器添加/移除**
- **智能工具路由**
- **分析类型自动识别**

### 📊 **智能分析Agent**
- **上下文感知**
- **多工具协调**
- **结果解释和建议**
- **中文友好交互**

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ MCPServerManager│  │ IntelligentAnalysisAgent        │   │
│  │                 │  │                                 │   │
│  │ - 服务器管理     │  │ - 智能分析协调                   │   │
│  │ - 健康检查       │  │ - 工具动态路由                   │   │
│  │ - 动态配置       │  │ - 结果解释                      │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    MCP Servers                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────┐ │
│  │Correlation  │ │ Regression  │ │ Clustering  │ │  ...  │ │
│  │   Server    │ │   Server    │ │   Server    │ │       │ │
│  │:8000        │ │:8001        │ │:8002        │ │       │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────┘
```

## API 接口

### 1. 主要分析接口

#### `POST /analyze`
执行数据分析的主要接口

**请求格式：**
```json
{
    "message": "请分析温度和湿度的相关性",
    "analysis_type": "correlation",
    "conversation_history": [],
    "context": {
        "dataset": "weather_data.csv",
        "priority": "high"
    }
}
```

**响应格式：**
```json
{
    "result": "分析结果的Markdown文本",
    "conversation_history": [...],
    "analysis_type": "correlation",
    "metadata": {
        "processing_time": "2.34s",
        "analysis_mode": "correlation",
        "active_servers": 1,
        "timestamp": "2024-01-01 12:00:00"
    }
}
```

#### `POST /chat`
兼容性接口，重定向到 `/analyze`

### 2. 系统管理接口

#### `GET /status`
获取系统状态

**响应示例：**
```json
{
    "status": "healthy",
    "active_servers": [
        {
            "server_name": "correlation",
            "status": "healthy",
            "analysis_types": ["correlation"],
            "last_check": "2024-01-01 12:00:00"
        }
    ],
    "total_servers": 4,
    "enabled_servers": 1
}
```

#### `GET /analysis-types`
获取支持的分析类型

**响应示例：**
```json
{
    "supported_analysis_types": {
        "correlation": ["correlation"],
        "regression": ["regression"]
    },
    "total_types": 2
}
```

### 3. 服务器管理接口

#### `POST /servers/{server_name}/enable`
启用指定服务器

#### `POST /servers/{server_name}/disable`
禁用指定服务器

#### `POST /servers/add`
动态添加新服务器

**请求示例：**
```json
{
    "name": "new_analysis",
    "url": "http://127.0.0.1:8004/sse",
    "timeout": 180,
    "enabled": true,
    "analysis_types": ["custom"]
}
```

## 分析类型枚举

```python
class AnalysisType(str, Enum):
    CORRELATION = "correlation"        # 相关性分析
    REGRESSION = "regression"          # 回归分析
    CLUSTERING = "clustering"          # 聚类分析
    CLASSIFICATION = "classification"  # 分类分析
    TIME_SERIES = "time_series"       # 时间序列分析
    DESCRIPTIVE = "descriptive"       # 描述性统计
    STATISTICAL_TEST = "statistical_test"  # 统计检验
    CUSTOM = "custom"                 # 自定义分析
```

## 使用示例

### 1. 基础相关性分析
```python
import requests

response = requests.post("http://localhost:8001/analyze", json={
    "message": "分析温度和湿度的相关性",
    "analysis_type": "correlation"
})

result = response.json()
print(result["result"])
```

### 2. 带上下文的分析
```python
response = requests.post("http://localhost:8001/analyze", json={
    "message": "请对这个数据集进行聚类分析",
    "analysis_type": "clustering",
    "context": {
        "dataset_path": "/data/customer_data.csv",
        "cluster_count": 5
    }
})
```

### 3. 对话式分析
```python
# 第一轮对话
response1 = requests.post("http://localhost:8001/analyze", json={
    "message": "我有一个销售数据，想分析影响销售额的因素"
})

# 第二轮对话，带历史
response2 = requests.post("http://localhost:8001/analyze", json={
    "message": "请具体分析价格和销售额的关系",
    "conversation_history": response1.json()["conversation_history"],
    "analysis_type": "correlation"
})
```

## 扩展新分析功能

### 1. 创建新的MCP服务器

```python
# 新建 regression_server.py
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
    # 实现线性回归分析
    pass

if __name__ == '__main__':
    mcp.run(transport='sse', port=8001)
```

### 2. 更新服务器配置

```python
# 在 backend.py 中添加新服务器配置
MCP_SERVERS_CONFIG["regression"] = MCPServerConfig(
    name="regression",
    url="http://127.0.0.1:8001/sse",
    analysis_types=[AnalysisType.REGRESSION],
    enabled=True
)
```

### 3. 动态添加服务器

```python
import requests

# 通过API动态添加
requests.post("http://localhost:8001/servers/add", json={
    "name": "regression",
    "url": "http://127.0.0.1:8001/sse",
    "analysis_types": ["regression"],
    "enabled": True
})
```

## 配置说明

### MCP服务器配置
```python
@dataclass
class MCPServerConfig:
    name: str                           # 服务器名称
    url: str                           # 服务器URL
    timeout: int = 180                 # 连接超时时间
    enabled: bool = True               # 是否启用
    analysis_types: List[AnalysisType] = None  # 支持的分析类型
```

### 环境变量配置
```bash
# 可选的环境变量
ANALYSIS_LOG_LEVEL=INFO
ANALYSIS_LOG_DIR=./logs
ANALYSIS_MAX_SERVERS=10
ANALYSIS_DEFAULT_TIMEOUT=180
```

## 监控和日志

### 日志类型
- **用户操作日志** - 记录用户请求
- **性能日志** - 记录处理时间
- **业务事件日志** - 记录分析完成情况
- **错误日志** - 记录异常和错误

### 监控指标
- 活跃服务器数量
- 分析请求处理时间
- 成功/失败率
- 各分析类型使用频率

## 最佳实践

### 1. 服务器管理
- 定期检查服务器健康状态
- 合理设置超时时间
- 按需启用/禁用服务器

### 2. 性能优化
- 根据分析类型选择合适的服务器
- 使用上下文信息优化分析
- 合理设置并发限制

### 3. 错误处理
- 实现优雅的降级机制
- 提供有意义的错误信息
- 记录详细的错误日志

### 4. 扩展开发
- 遵循MCP协议标准
- 实现标准的工具接口
- 提供完整的文档和示例

## 故障排除

### 常见问题

1. **服务器连接失败**
   - 检查服务器是否启动
   - 验证URL和端口配置
   - 查看网络连接状态

2. **分析结果异常**
   - 检查数据格式是否正确
   - 验证分析参数
   - 查看服务器日志

3. **性能问题**
   - 检查服务器负载
   - 优化数据大小
   - 调整超时设置

### 调试命令
```bash
# 检查系统状态
curl http://localhost:8001/status

# 查看支持的分析类型
curl http://localhost:8001/analysis-types

# 查看日志
tail -f logs/intelligent-analysis-agent.log
```

这个通用的智能数据分析后端系统为数据分析提供了强大而灵活的基础架构，可以轻松扩展以支持各种新的分析功能。 