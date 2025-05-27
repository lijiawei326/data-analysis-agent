# 日志系统使用说明

## 概述

本项目使用 `loguru` 实现了简洁高效的日志记录系统，所有日志统一保存到本地文件。

## 日志模块结构

### logger_config.py
独立的日志配置模块，提供以下功能：
- 自动日志轮转（每天）
- 统一的日志记录格式
- 日志文件管理和查看
- 控制台和文件双重输出

## 日志文件

日志文件保存在：`/home/work/disk1/LLM-ljw/agent/analysis-agent/frontend/logs/`

### 文件格式
- **app_YYYY-MM-DD.log** - 统一日志文件
  - 系统启动、错误、警告等系统日志
  - 用户输入和AI回复（带[CHAT]标签）
  - 处理耗时和错误信息
  - 包含详细的代码位置信息

### 日志轮转策略
- 每天00:00自动轮转
- 保留30天的历史日志
- 自动清理过期文件

## 日志格式示例

```
2024-01-15 10:30:25 | INFO     | backend:chat:89 - 收到聊天请求: 你好...
2024-01-15 10:30:25 | INFO     | logger_config:log_chat_input:45 - [CHAT] 用户输入: 你好
2024-01-15 10:30:27 | INFO     | backend:chat:120 - Agent运行完成，耗时: 1.50秒
2024-01-15 10:30:27 | INFO     | logger_config:log_chat_output:50 - [CHAT] AI回复: 你好！有什么可以帮助您的吗？
2024-01-15 10:30:27 | INFO     | logger_config:log_chat_output:51 - [CHAT] 处理耗时: 1.50秒
```

## 使用示例

### 在代码中使用
```python
from logger_config import logger, log_config

# 记录一般日志
logger.info("系统启动成功")
logger.error("发生错误")

# 记录聊天相关日志（带特殊标签）
log_config.log_chat_input("用户输入的消息")
log_config.log_chat_output("AI回复", processing_time=1.5)
log_config.log_chat_error("用户输入", "错误信息", processing_time=2.0)
```

## 功能特性

### LoggerConfig类方法
- `log_chat_input(message)` - 记录用户输入（带[CHAT]标签）
- `log_chat_output(message, processing_time)` - 记录AI回复
- `log_chat_error(user_input, error, processing_time)` - 记录错误
- `log_chat_timeout(user_input)` - 记录超时
- `log_conversation_stats(length, turns)` - 记录对话统计
- `log_session_reset()` - 记录会话重置
- `get_log_files_info()` - 获取日志文件信息
- `read_log_file(filename, lines)` - 读取日志文件

### 安全特性
- 路径穿越攻击防护
- 文件类型验证
- 错误处理和异常捕获

## 依赖安装

确保在 `pyproject.toml` 中已添加：
```toml
"loguru>=0.7.2",
```

然后运行：
```bash
uv sync
# 或
pip install loguru
```

## 注意事项

1. 日志目录会自动创建
2. 日志文件按日期自动轮转
3. 超过30天的日志会自动删除
4. 聊天相关日志通过[CHAT]标签区分
5. 支持中文字符编码（UTF-8）
6. 同时输出到控制台和文件 