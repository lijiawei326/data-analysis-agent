from agents import Agent
from model_provider.model_provider import MODEL_PROVIDER

column_mapping_agent = Agent(
    name="列名映射agent",
    instructions="""
    请根据下列已有列名，判断哪些列名最接近用户提供的变量意图。
    示例：
    【已有列名】:
    ["风速(m/s)", "风向(16方位)", "PM2.5浓度"]

    【用户意图】:
    ["风速", "风向", "PM2.5", "季节"]

    请输出一个JSON对象，表示用户列名与真实列名的映射关系，如：
    {
    "风速": "风速(m/s)",
    "风向": "风向(16方位)",
    "PM2.5": "PM2.5浓度",
    "季节": None
    }
    请严格遵守以下规则：
    1. 请直接输出JSON对象，不要输出任何其他内容。
    2. 如果存在任何一个列名你认为无法匹配，请设置为None。
    3. 注意风向角度和风向方位的区别，请勿将两种风向对应（**重要**）
    """,
    model=MODEL_PROVIDER.get_model('qwen3:8b')
)