from agents import Agent
from model_provider.model_provider import MODEL_PROVIDER
from agents.agent import StopAtTools

column_mapping_agent = Agent(
    name="列名映射agent",
    instructions="""
    你是一个专门负责列名映射的助手。请根据已有列名，判断哪些列名最接近用户提供的变量意图。

    示例1：
    【已有列名】: ["风速(m/s)", "风向(16方位)", "PM2.5浓度"]
    【用户意图】: ["风速", "风向", "PM2.5", "季节"]
    
    正确输出：
    {"风速": "风速(m/s)", "风向": "风向(16方位)", "PM2.5": "PM2.5浓度", "季节": null}

    示例2：
    【已有列名】: ["temperature", "humidity", "pressure"]
    【用户意图】: ["温度", "湿度"]
    
    正确输出：
    {"温度": "temperature", "湿度": "humidity"}

    **严格要求**：
    1. 输出必须是一个完整的JSON对象，以{开头，以}结尾
    2. 不要输出任何解释、说明或其他文字
    3. 不要使用代码块标记（如```json）
    4. 所有字符串必须用双引号包围
    5. 无法匹配的列名设置为null（不是None）
    6. JSON必须在一行内，不要换行
    7. 确保JSON语法完全正确
    8. 风向角度(°)和风向方位要区分，不要混淆
    """,
    model=MODEL_PROVIDER.get_model('qwen3:8b')
)

conversation_agent = Agent(
    name='asistant',
    instructions='你是一个乐于助人的助手。语言：简体中文',
    model=MODEL_PROVIDER.get_model(None),
    tool_use_behavior=StopAtTools(stop_at_tool_names=['correlation_analysis'])
)