# 交互式可视化系统 API 文档

## 系统概述

交互式可视化系统是一个支持多轮对话的数据可视化解决方案，由两个核心组件组成：

1. **交互式可视化MCP服务器** (`interactive_visualization_server.py`) - 负责会话管理、代码执行和图表生成
2. **可视化Agent** (`visualization_agent.py`) - 负责动态生成和优化matplotlib/seaborn绘图代码

## 系统架构

```
用户请求 → 可视化MCP → 可视化Agent → Python代码 → 图表文件
              ↓
        会话管理/缓存
              ↓
        用户反馈 → 代码优化 → 新图表
```

### 核心特性

- **智能自适应**：自动检测相关性分析需求，调用correlation_analysis获取矩阵
- **多轮对话**：支持基于用户反馈的迭代优化
- **会话管理**：维护代码历史版本，支持回滚
- **安全执行**：沙盒环境执行Python代码，确保安全性
- **数据缓存**：避免重复数据加载和LLM处理

## MCP工具函数

### 1. start_visualization_session

开始新的交互式可视化会话

**参数**：
- `user_request: str` - 用户的可视化需求描述
- `read_data_param: ReadDataParam` - 数据源参数
- `correlation_vars: Optional[List[str]]` - 相关性分析变量（可选）
- `correlation_method: str` - 相关性计算方法（默认"pearson"）
- `filters: Optional[Dict[str, str]]` - 数据过滤条件（可选）
- `group_by: Optional[List[str]]` - 分组条件（可选）
- `include_correlation_table: bool` - 是否同时返回相关性表格（默认False）

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "chart_path": "./visualizations/viz_1234567890_5678_v1.png",
  "correlation_table": "| 变量 | temperature | humidity | pressure |\n|------|-------------|----------|----------|\n...",
  "message": "可视化会话已创建，图表已生成。相关性表格也已包含在结果中。"
}
```

**使用示例**：
```python
# 相关性分析热力图
result = await start_visualization_session(
    user_request="请对温度、湿度、压力进行相关性分析并生成热力图",
    read_data_param=ReadDataParam(read_data_query="weather_data.csv"),
    correlation_vars=["temperature", "humidity", "pressure"],
    include_correlation_table=True
)

# 普通散点图
result = await start_visualization_session(
    user_request="请绘制价格和销量的散点图",
    read_data_param=ReadDataParam(read_data_query="sales_data.csv"),
    include_correlation_table=True
)
```

### 2. refine_visualization

基于用户反馈优化可视化

**参数**：
- `session_id: str` - 会话ID
- `user_feedback: str` - 用户的反馈和修改要求

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "chart_path": "./visualizations/viz_1234567890_5678_v2.png",
  "version": "v2",
  "message": "图表已根据反馈更新（v2）。如需进一步调整，请继续提供反馈。"
}
```

**使用示例**：
```python
# 修改颜色和样式
result = await refine_visualization(
    session_id="viz_1234567890_5678",
    user_feedback="请将颜色改为蓝色系，并增大字体"
)

# 更改图表类型
result = await refine_visualization(
    session_id="viz_1234567890_5678",
    user_feedback="请改为柱状图显示"
)
```

### 3. get_session_info

获取会话信息和历史记录

**参数**：
- `session_id: str` - 会话ID

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "original_request": "请对温度、湿度、压力进行相关性分析",
  "current_version": "v3",
  "total_iterations": 3,
  "generated_charts": [
    "./visualizations/viz_1234567890_5678_v1.png",
    "./visualizations/viz_1234567890_5678_v2.png",
    "./visualizations/viz_1234567890_5678_v3.png"
  ],
  "conversation_summary": [
    {
      "type": "initial",
      "feedback": "请对温度、湿度、压力进行相关性分析",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "type": "iteration",
      "feedback": "请将颜色改为蓝色系",
      "timestamp": "2024-01-15T10:35:00"
    }
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

### 4. rollback_to_version

回滚到指定的代码版本

**参数**：
- `session_id: str` - 会话ID
- `version: str` - 目标版本（如：v1, v2等）

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "chart_path": "./visualizations/viz_1234567890_5678_v1_rollback.png",
  "message": "已回滚到v1并重新生成图表"
}
```

### 5. list_active_sessions

列出当前活跃的会话

**返回值**：
```json
{
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "viz_1234567890_5678",
      "user_request": "请对温度、湿度、压力进行相关性分析...",
      "current_version": "v3",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:35:00"
    }
  ]
}
```

### 6. delete_session

删除指定的会话

**参数**：
- `session_id: str` - 要删除的会话ID

**返回值**：
```
"会话已删除: viz_1234567890_5678"
```

## 可视化Agent API

### 类：`InteractiveVisualizationAgent`

专门生成和优化数据可视化代码的智能代理。

#### 方法：`generate_initial_code(user_request: str, data_info: Dict) -> str`

**功能**：根据用户需求和数据信息生成初始的Python绘图代码

**参数**：
- `user_request: str` - 用户的自然语言可视化需求
- `data_info: Dict` - 数据结构信息，包含列名、类型、统计信息等

**返回值**：
- `str` - 完整的Python绘图代码

#### 方法：`modify_code(current_code: str, user_feedback: str, ...) -> str`

**功能**：基于用户反馈修改现有的绘图代码

**参数**：
- `current_code: str` - 当前的绘图代码
- `user_feedback: str` - 用户的反馈和修改要求
- `original_request: str` - 原始用户需求
- `data_info: Dict` - 数据信息
- `conversation_history: List[Dict]` - 对话历史

**返回值**：
- `str` - 修改后的Python绘图代码

## 支持的图表类型

### 1. 相关性热力图
- **适用场景**：展示多变量间的相关关系
- **自动触发**：当提供`correlation_vars`参数或用户需求包含"相关性"、"热力图"等关键词
- **特殊处理**：自动调用`correlation_analysis`获取相关性矩阵

### 2. 散点图
- **适用场景**：展示两个连续变量的关系
- **支持功能**：颜色分组、大小映射、趋势线

### 3. 折线图
- **适用场景**：展示时间序列或连续变化趋势
- **支持功能**：多系列、置信区间、标注

### 4. 柱状图
- **适用场景**：展示分类数据的对比
- **支持功能**：分组柱状图、堆叠图、水平图

### 5. 直方图
- **适用场景**：展示数据分布
- **支持功能**：密度曲线、分组对比

### 6. 箱线图/小提琴图
- **适用场景**：展示数据分布和异常值
- **支持功能**：分组对比、数据点叠加

### 7. 子图组合
- **适用场景**：多视角展示数据
- **支持功能**：灵活布局、统一样式

## 使用流程

### 1. 基础使用流程

```python
# 1. 开始会话
result = await start_visualization_session(
    user_request="请绘制销售趋势图",
    read_data_param=ReadDataParam(read_data_query="sales.csv"),
    include_correlation_table=True
)
session_id = json.loads(result)["session_id"]

# 2. 查看结果并提供反馈
result = await refine_visualization(
    session_id=session_id,
    user_feedback="请增加趋势线，并使用更鲜艳的颜色"
)

# 3. 继续优化
result = await refine_visualization(
    session_id=session_id,
    user_feedback="请添加网格线，并调整字体大小"
)
```

### 2. 相关性分析流程

```python
# 1. 开始相关性分析会话
result = await start_visualization_session(
    user_request="分析客户数据的相关性",
    read_data_param=ReadDataParam(read_data_query="customers.csv"),
    correlation_vars=["age", "income", "spending", "satisfaction"],
    correlation_method="pearson",
    include_correlation_table=True
)

# 2. 优化热力图
result = await refine_visualization(
    session_id=session_id,
    user_feedback="请使用蓝红色方案，并显示相关系数值"
)
```

### 3. 会话管理流程

```python
# 查看所有会话
sessions = await list_active_sessions()

# 获取特定会话信息
info = await get_session_info(session_id)

# 回滚到之前版本
result = await rollback_to_version(session_id, "v1")

# 删除会话
await delete_session(session_id)
```

## 配置和设置

### 可视化配置

```python
@dataclass
class VisualizationConfig:
    output_dir: str = "./visualizations"      # 图表输出目录
    default_figsize: Tuple[int, int] = (12, 8)  # 默认图形尺寸
    default_dpi: int = 300                    # 默认分辨率
    session_timeout: int = 3600               # 会话超时时间（秒）
    max_sessions: int = 100                   # 最大会话数
```

### 中文字体支持

系统自动配置中文字体支持：
```python
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
```

### 安全限制

代码执行器包含以下安全限制：
- 禁用危险函数：`exec`, `eval`, `open`, `__import__`等
- 限制导入模块：仅允许数据科学相关库
- 沙盒环境：限制文件系统访问

## 错误处理

### 常见异常类型

- `VisualizationError`: 可视化基础异常
- `CodeSecurityError`: 代码安全异常
- `ChartGenerationError`: 图表生成异常
- `SessionNotFoundError`: 会话不存在异常

### 错误恢复机制

1. **代码生成失败**：自动使用基础模板
2. **代码执行失败**：返回详细错误信息
3. **会话过期**：自动清理，提示重新开始
4. **数据缓存丢失**：提示重新开始会话

## 扩展和定制

### 添加新的图表类型

1. 在Agent的instructions中添加新图表类型说明
2. 更新代码模板和验证逻辑
3. 添加相应的测试用例

### 自定义颜色方案

在配置中修改颜色方案：
```python
color_schemes = {
    "correlation": "RdBu_r",
    "sequential": "viridis",
    "diverging": "RdYlBu",
    "categorical": "Set3"
}
```

### 集成新的数据源

在DataLoader中添加新的文件格式支持：
```python
elif file_ext == '.new_format':
    df = custom_reader(file_path)
```

## 性能优化

### 缓存策略

- **数据缓存**：避免重复加载相同数据文件
- **会话缓存**：维护会话状态，支持快速迭代
- **代码缓存**：保存历史版本，支持快速回滚

### 资源管理

- **会话自动清理**：定期清理过期会话
- **内存管理**：及时关闭matplotlib图形对象
- **文件管理**：图表文件按会话组织

## 最佳实践

1. **明确需求描述**：提供清晰的可视化需求和数据背景
2. **迭代优化**：通过多轮反馈逐步完善图表
3. **会话管理**：及时删除不需要的会话
4. **数据预处理**：确保数据质量和格式正确
5. **安全考虑**：避免在代码中包含敏感信息 

### 新增：同时获取可视化和相关性表格

#### visualization_with_correlation_table

创建可视化的同时获取相关性分析表格

**参数**：
- `user_request: str` - 用户的可视化需求描述
- `read_data_param: ReadDataParam` - 数据源参数
- `correlation_vars: List[str]` - 相关性分析变量（必填）
- `correlation_method: str` - 相关性计算方法（默认"pearson"）
- `filters: Optional[Dict[str, str]]` - 数据过滤条件（可选）
- `group_by: Optional[List[str]]` - 分组条件（可选）

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "chart_path": "./visualizations/viz_1234567890_5678_v1.png",
  "correlation_table": "| 变量 | temperature | humidity | pressure |\n|------|-------------|----------|----------|\n...",
  "message": "可视化会话已创建，图表已生成。相关性表格也已包含在结果中。"
}
```

**使用示例**：
```python
# 同时获取热力图和相关性表格
result = await visualization_with_correlation_table(
    user_request="请生成相关性热力图，我需要同时查看图表和数据表格",
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["var1", "var2", "var3"]
)

result_data = json.loads(result)
chart_path = result_data["chart_path"]
correlation_table = result_data["correlation_table"]
```

#### get_correlation_table_only

仅获取相关性分析表格，不生成可视化图表

**参数**：
- `read_data_param: ReadDataParam` - 数据源参数
- `correlation_vars: List[str]` - 相关性分析变量（必填）
- `correlation_method: str` - 相关性计算方法（默认"pearson"）
- `filters: Optional[Dict[str, str]]` - 数据过滤条件（可选）
- `group_by: Optional[List[str]]` - 分组条件（可选）

**返回值**：
```
相关性分析表格的Markdown格式文本
```

**使用示例**：
```python
# 仅获取相关性表格
table = await get_correlation_table_only(
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["var1", "var2", "var3"],
    correlation_method="spearman"
)
```

## 多轮对话场景处理

### 场景1：第一轮要图表，第二轮要表格

#### get_correlation_table_from_session

从现有会话中获取相关性表格

**参数**：
- `session_id: str` - 会话ID

**返回值**：
```
相关性分析表格的Markdown格式文本
```

**使用示例**：
```python
# 第一轮：生成热力图
result = await start_visualization_session(
    user_request="请生成相关性热力图",
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["var1", "var2", "var3"],
    include_correlation_table=False  # 第一轮不要表格
)

session_id = json.loads(result)["session_id"]

# 第二轮：用户想要看表格
table = await get_correlation_table_from_session(session_id)
```

### 场景2：第一轮要表格，第二轮要图表

#### start_correlation_analysis_only

仅进行相关性分析，创建会话但不生成图表

**参数**：
- `read_data_param: ReadDataParam` - 数据源参数
- `correlation_vars: List[str]` - 相关性分析变量（必填）
- `correlation_method: str` - 相关性计算方法（默认"pearson"）
- `filters: Optional[Dict[str, str]]` - 数据过滤条件（可选）
- `group_by: Optional[List[str]]` - 分组条件（可选）

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "session_type": "correlation_only",
  "correlation_table": "| 变量 | var1 | var2 | var3 |\n...",
  "correlation_vars": ["var1", "var2", "var3"],
  "correlation_method": "pearson",
  "message": "相关性分析完成。您可以使用 visualize_existing_correlation 基于此结果生成图表。"
}
```

#### visualize_existing_correlation

基于现有会话中的相关性数据生成可视化图表

**参数**：
- `session_id: str` - 会话ID
- `visualization_request: str` - 可视化需求描述（可选）

**返回值**：
```json
{
  "session_id": "viz_1234567890_5678",
  "chart_path": "./visualizations/viz_1234567890_5678_v1.png",
  "version": "v1",
  "correlation_vars": ["var1", "var2", "var3"],
  "correlation_method": "pearson",
  "message": "已基于现有相关性数据生成可视化图表（v1）。您可以继续提供反馈来优化图表。"
}
```

**完整使用示例**：
```python
# 第一轮：只要相关性表格
result = await start_correlation_analysis_only(
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["var1", "var2", "var3"]
)

session_info = json.loads(result)
session_id = session_info["session_id"]
correlation_table = session_info["correlation_table"]

# 第二轮：基于已有数据生成图表
chart_result = await visualize_existing_correlation(
    session_id=session_id,
    visualization_request="请生成一个漂亮的热力图，使用蓝红色方案"
)

chart_info = json.loads(chart_result)
chart_path = chart_info["chart_path"]
```

### 多轮对话的完整流程

#### 流程1：先图后表
```python
# 1. 第一轮：用户要热力图
result1 = await start_visualization_session(
    user_request="请生成相关性热力图",
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["temperature", "humidity", "pressure"]
)

session_id = json.loads(result1)["session_id"]

# 2. 第二轮：用户想看表格
table = await get_correlation_table_from_session(session_id)

# 3. 第三轮：用户想优化图表
improved_chart = await refine_visualization(
    session_id=session_id,
    user_feedback="请使用更鲜艳的颜色"
)

# 4. 第四轮：用户再次查看表格（数据一致性）
table_again = await get_correlation_table_from_session(session_id)
```

#### 流程2：先表后图
```python
# 1. 第一轮：用户只要相关性表格
result1 = await start_correlation_analysis_only(
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["temperature", "humidity", "pressure"]
)

session_info = json.loads(result1)
session_id = session_info["session_id"]
table = session_info["correlation_table"]

# 2. 第二轮：用户想要图表
chart_result = await visualize_existing_correlation(
    session_id=session_id,
    visualization_request="请生成热力图"
)

# 3. 第三轮：优化图表
improved_chart = await refine_visualization(
    session_id=session_id,
    user_feedback="请调整颜色和字体"
)

# 4. 第四轮：再次查看原始表格
table_again = await get_correlation_table_from_session(session_id)
``` 