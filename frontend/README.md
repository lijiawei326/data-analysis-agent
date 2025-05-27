# 智能分析对话系统 - Streamlit前端

这是一个基于Streamlit的简洁前端界面，用于与智能分析对话系统的后端API进行交互。

## 功能特性

- 🤖 实时对话交互
- 💬 对话历史记录
- 🔄 一键重置对话
- 📊 API状态监控
- 🎨 简洁现代的UI设计
- ⚙️ 可配置的API设置
- 🧪 内置测试功能

## 快速开始

### 1. 启动后端服务

首先确保后端API服务正在运行：

```bash
cd /home/work/disk1/LLM-ljw/agent/analysis-agent/frontend
source /home/work/disk1/LLM-ljw/agent/analysis-agent/.venv/bin/activate
python backend.py
```

后端将在 `http://localhost:8001` 运行。

### 2. 启动前端应用

使用提供的启动脚本：

```bash
cd /home/work/disk1/LLM-ljw/agent/analysis-agent/frontend
./run_frontend.sh
```

或者手动启动：

```bash
source /home/work/disk1/LLM-ljw/agent/analysis-agent/.venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

前端将在 `http://localhost:8501` 运行。

### 3. 测试功能

运行测试脚本验证API连接：

```bash
source /home/work/disk1/LLM-ljw/agent/analysis-agent/.venv/bin/activate
python test_frontend.py
```

## 使用说明

1. 打开浏览器访问 `http://localhost:8501`
2. 在输入框中输入您的问题
3. 按Enter键或点击发送按钮提交
4. 系统将进行智能分析并返回结果
5. 可以在侧边栏查看API状态和使用说明
6. 点击"重置对话"按钮可以清空对话历史

## 项目结构

```
frontend/
├── app.py              # 主要的Streamlit应用
├── backend.py          # FastAPI后端服务
├── config.py           # 配置文件
├── requirements.txt    # Python依赖
├── run_frontend.sh     # 启动脚本
├── test_frontend.py    # 测试脚本
└── README.md          # 说明文档
```

## 配置说明

可以通过修改 `config.py` 文件来调整以下设置：

- **API_BASE_URL**: 后端API地址（默认: http://localhost:8001）
- **STREAMLIT_CONFIG**: Streamlit页面配置
- **TIMEOUT_SETTINGS**: 各种API调用的超时设置

## 依赖要求

- Python 3.8+
- Streamlit >= 1.28.0
- Requests >= 2.31.0

## 故障排除

### 常见问题

1. **API连接失败**
   - 确保后端服务正在运行
   - 检查 `config.py` 中的API地址配置
   - 验证端口8001没有被其他程序占用

2. **前端启动失败**
   - 确保已激活正确的虚拟环境
   - 检查依赖是否正确安装
   - 验证端口8501没有被占用

3. **聊天功能异常**
   - 运行 `test_frontend.py` 检查API状态
   - 查看后端日志获取详细错误信息
   - 检查网络连接

### 调试步骤

1. 运行测试脚本：`python test_frontend.py`
2. 检查后端日志输出
3. 验证虚拟环境和依赖
4. 检查防火墙和端口设置

## 注意事项

- 确保后端API服务在前端启动前已经运行
- 如果遇到连接问题，请检查API地址配置
- 前端默认连接到 `http://localhost:8001` 的后端API 