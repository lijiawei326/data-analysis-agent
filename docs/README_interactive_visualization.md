# 交互式可视化系统

一个支持多轮对话的智能数据可视化解决方案，专为数据分析和相关性分析设计。

## 🚀 特性亮点

- **🤖 智能代码生成**：LLM动态生成matplotlib/seaborn代码，无需预定义模板
- **💬 多轮对话优化**：支持基于用户反馈的迭代改进
- **🔗 无缝集成**：自动适配correlation_analysis进行相关性可视化
- **⚡ 会话管理**：维护历史版本，支持回滚和比较
- **🔒 安全执行**：沙盒环境执行Python代码，确保系统安全
- **📊 丰富图表**：支持热力图、散点图、折线图、柱状图等多种类型

## 📁 文件结构

```
analysis-agent/
├── server/
│   ├── interactive_visualization_server.py    # MCP服务器主文件
│   ├── start_visualization_server.py          # 服务器启动脚本
│   ├── test_interactive_visualization.py      # 测试脚本
│   ├── interactive_visualization_api.md       # API详细文档
│   └── README_interactive_visualization.md    # 本文件
└── agent_mcp/
    └── visualization_agent.py                 # 可视化代码生成Agent
```

## 🛠 安装和配置

### 前置要求

- Python 3.8+
- 现有的analysis-agent项目环境
- matplotlib, seaborn, pandas, numpy等数据科学库

### 快速开始

1. **启动MCP服务器**：
```bash
cd analysis-agent/server
python start_visualization_server.py
```

2. **运行测试**：
```bash
python test_interactive_visualization.py
```

3. **使用API**：
```python
from interactive_visualization_server import start_visualization_session

# 开始可视化会话
result = await start_visualization_session(
    user_request="请绘制销售趋势图",
    read_data_param=ReadDataParam(read_data_query="data.csv")
)
```

## 📖 使用指南

### 基础使用流程

```python
# 1. 开始新会话
result = await start_visualization_session(
    user_request="请对温度、湿度、压力进行相关性分析并生成热力图",
    read_data_param=ReadDataParam(read_data_query="weather.csv"),
    correlation_vars=["temperature", "humidity", "pressure"]
)

session_info = json.loads(result)
session_id = session_info["session_id"]
chart_path = session_info["chart_path"]

# 2. 基于反馈优化
result = await refine_visualization(
    session_id=session_id,
    user_feedback="请使用更明亮的颜色，并显示相关系数数值"
)

# 3. 继续迭代
result = await refine_visualization(
    session_id=session_id,
    user_feedback="请调整字体大小，并添加标题"
)

# 4. 查看会话信息
info = await get_session_info(session_id)

# 5. 清理会话
await delete_session(session_id)
```

### 相关性分析特殊用法

系统会自动检测相关性分析需求：

```python
# 方式1：明确指定相关性变量
result = await start_visualization_session(
    user_request="分析变量间的相关关系",
    read_data_param=ReadDataParam(read_data_query="data.csv"),
    correlation_vars=["var1", "var2", "var3"],  # 自动调用correlation_analysis
    correlation_method="pearson"
)

# 方式2：通过关键词自动识别
result = await start_visualization_session(
    user_request="请生成相关性热力图",  # 包含"相关性"关键词
    read_data_param=ReadDataParam(read_data_query="data.csv")
)
```

## 🎯 核心优势

### 1. 智能自适应
- 自动检测是否需要相关性分析
- 根据数据类型选择最适合的图表
- 智能处理数据异常和缺失值

### 2. 交互式体验
- 支持自然语言反馈
- 多轮对话迭代优化
- 实时生成和预览图表

### 3. 数据安全
- 数据不经过LLM处理，避免泄露
- 代码在沙盒环境执行
- 严格的import和函数限制

### 4. 高度可扩展
- 模块化设计，易于添加新功能
- 支持多种数据源格式
- 灵活的颜色和样式配置

## 🔧 API 参考

### 主要工具函数

| 函数名 | 功能 | 参数 |
|--------|------|------|
| `start_visualization_session` | 开始新的可视化会话 | user_request, read_data_param, correlation_vars等 |
| `refine_visualization` | 基于反馈优化图表 | session_id, user_feedback |
| `get_session_info` | 获取会话详细信息 | session_id |
| `rollback_to_version` | 回滚到指定版本 | session_id, version |
| `list_active_sessions` | 列出活跃会话 | 无 |
| `delete_session` | 删除会话 | session_id |

详细API文档请参考 `interactive_visualization_api.md`

## 🎨 支持的图表类型

- **相关性热力图** - 自动调用correlation_analysis
- **散点图** - 两变量关系分析
- **折线图** - 时间序列和趋势
- **柱状图** - 分类数据比较
- **直方图** - 数据分布展示
- **箱线图** - 分布和异常值
- **小提琴图** - 密度分布
- **子图组合** - 多视角展示

## ⚙️ 配置选项

```python
# 可视化配置
class VisualizationConfig:
    output_dir: str = "./visualizations"        # 图表输出目录
    default_figsize: Tuple[int, int] = (12, 8)  # 默认图形尺寸
    default_dpi: int = 300                      # 分辨率
    session_timeout: int = 3600                 # 会话超时(秒)
    max_sessions: int = 100                     # 最大会话数
```

## 🧪 测试

运行完整测试套件：

```bash
python test_interactive_visualization.py
```

测试包括：
- ✅ 相关性热力图生成
- ✅ 基础可视化功能
- ✅ 多轮对话优化
- ✅ 会话管理功能
- ✅ 版本回滚功能
- ✅ 资源清理

## 🔍 故障排除

### 常见问题

1. **导入错误**
   ```
   ImportError: No module named 'xxx'
   ```
   解决：确保所有依赖库已安装
   ```bash
   pip install matplotlib seaborn pandas numpy
   ```

2. **中文字体显示问题**
   ```
   UserWarning: Glyph missing from current font
   ```
   解决：系统会自动配置中文字体，如仍有问题请手动安装SimHei字体

3. **会话过期**
   ```
   SessionNotFoundError: 会话不存在
   ```
   解决：会话默认1小时过期，请重新开始新会话

4. **代码执行失败**
   ```
   ChartGenerationError: 代码执行失败
   ```
   解决：检查数据格式和列名，确保数据质量

### 调试模式

启动时开启调试模式：
```bash
python start_visualization_server.py --log-level DEBUG
```

## 🚦 性能建议

1. **及时清理会话**：避免内存累积
2. **合理设置超时**：根据使用频率调整
3. **优化数据大小**：大数据集建议采样
4. **监控资源使用**：定期检查生成的图片文件

## 🔮 未来规划

- [ ] 支持交互式图表（plotly）
- [ ] 增加更多图表类型
- [ ] 数据预处理建议
- [ ] 图表模板库
- [ ] 批量生成功能
- [ ] 图表分享和导出

## 📞 支持

如遇问题，请：
1. 查看日志文件 `./logs/`
2. 运行测试脚本验证环境
3. 检查API文档确认用法
4. 提交issue附带详细错误信息

---

**🎉 享受智能可视化的便利！** 