# 通用日志模块 (UniversalLogger) 使用说明

## 🎯 概述

`UniversalLogger` 是一个基于 `loguru` 的通用日志模块，设计用于任何 Python 项目。它提供了丰富的功能、灵活的配置选项和开箱即用的最佳实践。

## ✨ 核心特性

### 🔧 高度可配置
- **灵活的目录配置**：支持自定义日志目录或使用默认值
- **多种轮转策略**：按时间、文件大小或其他条件轮转
- **可调节的日志级别**：DEBUG、INFO、WARNING、ERROR、CRITICAL
- **自定义格式**：支持完全自定义的日志格式
- **输出控制**：可选择控制台输出、文件输出或两者兼有

### 🏷️ 丰富的日志类型
- **标签日志**：为日志添加自定义标签
- **用户行为日志**：记录用户操作和行为
- **API请求日志**：记录HTTP请求详情
- **性能监控日志**：记录执行时间和性能指标
- **错误上下文日志**：记录详细的错误信息和上下文
- **业务事件日志**：记录业务逻辑事件
- **安全事件日志**：记录安全相关事件

### 🛡️ 安全特性
- **路径安全检查**：防止路径穿越攻击
- **文件类型验证**：只允许访问日志文件
- **异常处理**：完整的错误处理和恢复机制

## 🚀 快速开始

### 基础使用

```python
from logger_config import create_logger

# 创建日志器
logger_instance = create_logger(
    app_name="my-app",
    log_dir="./logs"
)

# 获取日志器
logger = logger_instance.get_logger()

# 记录日志
logger.info("应用启动成功")
logger.warning("这是一个警告")
logger.error("发生了错误")
```

### 使用默认实例

```python
from logger_config import logger, default_log_config

# 直接使用默认日志器
logger.info("使用默认配置的日志")

# 使用带标签的日志
default_log_config.log_with_tag("info", "带标签的消息", "USER")
```

## 📖 详细配置

### 初始化参数

```python
from logger_config import UniversalLogger

logger_instance = UniversalLogger(
    log_dir="./logs",              # 日志目录
    app_name="my-application",     # 应用名称
    log_level="INFO",              # 日志级别
    rotation="00:00",              # 轮转策略：每天午夜
    retention="30 days",           # 保留策略：保留30天
    console_output=True,           # 控制台输出
    file_output=True,              # 文件输出
    custom_format=None             # 自定义格式
)
```

### 轮转策略选项

```python
# 按时间轮转
rotation="00:00"        # 每天午夜
rotation="1 week"       # 每周
rotation="1 hour"       # 每小时

# 按大小轮转
rotation="100 MB"       # 文件达到100MB时轮转
rotation="1 GB"         # 文件达到1GB时轮转

# 按条件轮转
rotation="500000"       # 文件达到500000字节时轮转
```

### 保留策略选项

```python
retention="30 days"     # 保留30天
retention="1 week"      # 保留1周
retention="10 files"    # 保留最新的10个文件
retention=None          # 永久保留
```

## 🎯 使用场景示例

### 1. Web应用日志

```python
from logger_config import create_logger

# 创建Web应用日志器
web_logger = create_logger(
    app_name="web-api",
    log_dir="/var/log/myapp"
)

# 记录API请求
web_logger.log_api_request("POST", "/api/users", 201, 0.145, "user123")

# 记录用户行为
web_logger.log_user_action("登录", "成功登录系统", "user123")

# 记录性能
web_logger.log_performance("数据库查询", 0.032, "查询用户表")
```

### 2. 数据处理应用

```python
# 创建数据处理日志器
data_logger = create_logger(
    app_name="data-processor",
    log_level="DEBUG",
    rotation="100 MB"
)

# 记录业务事件
data_logger.log_business_event("数据导入开始", {
    "文件名": "data.csv",
    "记录数": 10000
})

# 记录处理进度
data_logger.log_with_tag("info", "已处理50%的数据", "PROGRESS")
```

### 3. 微服务日志

```python
# 为每个服务创建独立的日志器
user_service_logger = create_logger(app_name="user-service")
order_service_logger = create_logger(app_name="order-service")
payment_service_logger = create_logger(app_name="payment-service")

# 各服务独立记录日志
user_service_logger.log_business_event("用户注册", {"user_id": "123"})
order_service_logger.log_business_event("订单创建", {"order_id": "456"})
```

### 4. 安全监控

```python
# 创建安全监控日志器
security_logger = create_logger(
    app_name="security-monitor",
    log_dir="/var/log/security"
)

# 记录安全事件
security_logger.log_security_event("登录失败", "WARNING", "用户名: admin, IP: 192.168.1.100")
security_logger.log_security_event("异常访问", "ERROR", "尝试访问管理员页面")
```

## 🔍 日志查看和管理

### 获取日志文件信息

```python
# 获取所有日志文件信息
files_info = logger_instance.get_log_files_info()
print(f"找到 {files_info['total_files']} 个日志文件")

for file_info in files_info['files']:
    print(f"{file_info['name']} - {file_info['size_mb']}MB")
```

### 读取日志文件

```python
# 读取最后100行
content = logger_instance.read_log_file("my-app_2024-01-15.log", lines=100)

# 搜索特定内容
error_logs = logger_instance.read_log_file(
    "my-app_2024-01-15.log", 
    lines=50,
    search_pattern="ERROR"
)
```

### 动态调整日志级别

```python
# 运行时修改日志级别
logger_instance.set_log_level("DEBUG")
```

### 添加额外的文件处理器

```python
# 为特定功能添加专门的日志文件
logger_instance.add_file_handler(
    "/path/to/special.log",
    level="WARNING",
    rotation="1 week"
)
```

## 🔧 高级功能

### 创建子日志器

```python
# 为不同模块创建子日志器
db_logger = logger_instance.create_child_logger("database")
api_logger = logger_instance.create_child_logger("api")
```

### 环境变量支持

```python
import os

# 通过环境变量配置日志目录
logger_instance = create_logger(
    app_name="my-app",
    log_dir=os.environ.get("LOG_DIR", "./logs")
)
```

### 错误上下文记录

```python
try:
    # 一些可能出错的操作
    risky_operation()
except Exception as e:
    logger_instance.log_error_with_context(e, {
        "用户ID": "123",
        "操作": "数据更新",
        "参数": {"key": "value"}
    })
```

## 📋 最佳实践

### 1. 命名约定
```python
# 使用描述性的应用名称
web_api_logger = create_logger(app_name="web-api-v2")
data_processor_logger = create_logger(app_name="etl-processor")
```

### 2. 结构化日志
```python
# 使用结构化的业务事件记录
logger_instance.log_business_event("订单处理", {
    "order_id": "12345",
    "user_id": "67890",
    "amount": 99.99,
    "status": "completed"
})
```

### 3. 性能监控
```python
import time

start_time = time.time()
# 执行业务逻辑
process_data()
duration = time.time() - start_time

logger_instance.log_performance("数据处理", duration, "处理1000条记录")
```

### 4. 分级日志记录
```python
# 开发环境：DEBUG级别
dev_logger = create_logger(app_name="dev-app", log_level="DEBUG")

# 生产环境：INFO级别
prod_logger = create_logger(app_name="prod-app", log_level="INFO")
```

## 🔗 与现有项目集成

### Flask 集成
```python
from flask import Flask, request
from logger_config import create_logger

app = Flask(__name__)
flask_logger = create_logger(app_name="flask-app")

@app.before_request
def log_request():
    flask_logger.log_api_request(
        request.method, 
        request.path,
        user_id=getattr(request, 'user_id', None)
    )
```

### Django 集成
```python
# settings.py
from logger_config import create_logger

django_logger = create_logger(
    app_name="django-app",
    log_dir="/var/log/django"
)

# 在视图中使用
def my_view(request):
    django_logger.log_user_action("访问页面", request.path)
```

### FastAPI 集成（当前项目示例）
```python
from logger_config import create_logger

app_logger = create_logger(
    app_name="fastapi-app",
    log_dir="./logs"
)

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    app_logger.log_api_request(
        request.method,
        str(request.url),
        response.status_code,
        process_time
    )
    return response
```

## 🎨 自定义格式示例

### 简化格式
```python
simple_logger = create_logger(
    app_name="simple-app",
    custom_format="{time:HH:mm:ss} | {level} | {message}"
)
```

### JSON格式
```python
json_format = "{time} | {level} | {message} | {extra}"
json_logger = create_logger(
    app_name="json-app",
    custom_format=json_format
)
```

## 🚨 注意事项

1. **磁盘空间**：定期监控日志目录的磁盘使用情况
2. **权限管理**：确保应用有写入日志目录的权限
3. **并发安全**：loguru 天然支持多线程安全
4. **性能考虑**：在高并发场景下，考虑使用异步日志记录
5. **敏感信息**：避免在日志中记录密码、密钥等敏感信息

## 📦 依赖要求

```toml
# pyproject.toml
dependencies = [
    "loguru>=0.7.2",
]
```

## 🎉 总结

`UniversalLogger` 提供了一个强大、灵活且易于使用的日志解决方案，适用于从简单脚本到复杂企业应用的各种场景。通过其丰富的功能和简洁的API，您可以轻松地为任何Python项目添加专业级的日志记录能力。 