"""
交互式可视化Agent
负责根据用户需求动态生成和优化matplotlib/seaborn绘图代码
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
import re

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'frontend'))

from logger_config import create_logger
from agents import Runner, Agent
from utils.utils import remove_think

class InteractiveVisualizationAgent(Agent):
    """交互式可视化Agent"""
    
    def __init__(self):
        super().__init__(
            name="交互式可视化Agent",
            description="根据用户需求动态生成和优化matplotlib/seaborn绘图代码，支持多轮对话迭代",
            instructions="""
你是一个专业的交互式数据可视化代码生成专家。你的主要职责是：

1. **理解用户需求和数据结构**：
   - 分析用户的自然语言描述，理解他们想要的图表类型和风格
   - 理解数据的结构、列名、数据类型和分布特点
   - 确定最适合的matplotlib/seaborn可视化方法

2. **生成高质量的Python绘图代码**：
   - 使用matplotlib和seaborn库
   - 支持中文字体和标签显示
   - 生成完整可执行的Python代码
   - 包含必要的数据处理和错误处理

3. **支持代码迭代优化**：
   - 基于用户反馈理解问题和改进点
   - 在现有代码基础上进行修改，而不是完全重写
   - 保持代码的一致性和完整性
   - 响应各种修改需求：颜色、布局、标签、图表类型等

4. **代码规范要求**：
   - 数据变量统一使用 `data_df`
   - 图表保存路径使用 `save_path` 变量
   - 包含完整的import语句
   - 设置中文字体支持
   - 添加适当的注释说明
   - 确保图形正确关闭（plt.close()）

5. **支持的图表类型**：
   - 相关性热力图：展示变量间相关性
   - 散点图：展示两变量关系
   - 折线图：展示趋势变化
   - 柱状图：展示分类对比
   - 直方图：展示数据分布
   - 箱线图：展示分布和异常值
   - 小提琴图：展示分布密度
   - 子图组合：多个图表组合展示

6. **输出格式要求**：
   - 只返回纯Python代码，不要有额外的解释文字
   - 代码要完整可执行
   - 包含必要的异常处理

示例代码结构：
```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 创建图形
fig, ax = plt.subplots(figsize=(12, 8))

# 绘图逻辑
# ... 具体的绘图代码 ...

# 设置标题和标签
plt.title('图表标题', fontsize=16, fontweight='bold')
plt.xlabel('X轴标签', fontsize=12)
plt.ylabel('Y轴标签', fontsize=12)

# 优化布局
plt.tight_layout()

# 保存图表
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
```

注意事项：
- 始终考虑数据的特点和分布
- 选择合适的颜色方案和样式
- 确保图表的可读性和美观性
- 处理可能的数据异常情况
- 优化图表的布局和比例
"""
        )
        self.logger = create_logger(app_name="viz_agent", log_dir="./logs").get_logger()
    
    async def generate_initial_code(self, 
                                  user_request: str,
                                  data_info: Dict) -> str:
        """生成初始的可视化代码"""
        
        try:
            self.logger.info(f"生成初始代码: {user_request}")
            
            prompt = self._build_initial_prompt(user_request, data_info)
            
            result = await Runner.run(
                starting_agent=self,
                input=prompt
            )
            
            code = self._extract_code(result.final_output)
            self.logger.info("初始代码生成成功")
            return code
            
        except Exception as e:
            self.logger.error(f"初始代码生成失败: {e}")
            raise
    
    async def modify_code(self, 
                         current_code: str,
                         user_feedback: str,
                         original_request: str,
                         data_info: Dict,
                         conversation_history: List[Dict]) -> str:
        """基于用户反馈修改代码"""
        
        try:
            self.logger.info(f"修改代码: {user_feedback}")
            
            prompt = self._build_modification_prompt(
                current_code, user_feedback, original_request, 
                data_info, conversation_history
            )
            
            result = await Runner.run(
                starting_agent=self,
                input=prompt
            )
            
            code = self._extract_code(result.final_output)
            self.logger.info("代码修改成功")
            return code
            
        except Exception as e:
            self.logger.error(f"代码修改失败: {e}")
            raise
    
    def _build_initial_prompt(self, user_request: str, data_info: Dict) -> str:
        """构建初始代码生成的提示"""
        
        prompt = f"""请根据用户需求生成matplotlib/seaborn绘图代码。

用户需求：{user_request}

数据信息：
- 数据形状：{data_info.get('shape', 'N/A')}
- 列名：{data_info.get('columns', [])}
- 数据类型：{data_info.get('dtypes', {})}
- 数值列：{data_info.get('numeric_columns', [])}
- 数据预览：
{self._format_data_preview(data_info.get('head', {}))}

"""
        
        # 添加统计信息（如果有）
        if 'description' in data_info and data_info['description']:
            prompt += f"""数据统计信息：
{self._format_statistics(data_info['description'])}

"""
        
        prompt += """请生成完整的Python绘图代码，要求：
1. 使用data_df作为数据变量，save_path作为保存路径
2. 包含完整的import语句和中文字体设置
3. 根据数据特点选择合适的图表类型和样式
4. 确保代码完整可执行
5. 只返回代码，不要其他解释

代码："""
        
        return prompt
    
    def _build_modification_prompt(self, 
                                 current_code: str,
                                 user_feedback: str,
                                 original_request: str,
                                 data_info: Dict,
                                 conversation_history: List[Dict]) -> str:
        """构建代码修改的提示"""
        
        prompt = f"""请根据用户反馈修改现有的绘图代码。

原始需求：{original_request}

当前代码：
```python
{current_code}
```

用户反馈：{user_feedback}

数据信息：
- 数据形状：{data_info.get('shape', 'N/A')}
- 列名：{data_info.get('columns', [])}
- 数值列：{data_info.get('numeric_columns', [])}

"""
        
        # 添加对话历史（最近3轮）
        if conversation_history:
            prompt += "最近的修改历史：\n"
            for i, conv in enumerate(conversation_history[-3:], 1):
                feedback = conv.get('feedback', conv.get('request', ''))
                if feedback:
                    prompt += f"第{i}轮反馈：{feedback}\n"
            prompt += "\n"
        
        prompt += """请基于用户反馈修改代码，要求：
1. 保持代码的完整性和可执行性
2. 只修改需要改进的部分，保持其他部分不变
3. 确保修改后的代码仍然使用data_df和save_path变量
4. 添加简要的修改说明注释
5. 只返回修改后的完整代码，不要其他解释

修改后的代码："""
        
        return prompt
    
    def _extract_code(self, llm_output: str) -> str:
        """从LLM输出中提取Python代码"""
        
        # 移除思考过程
        cleaned_output = remove_think(llm_output).strip()
        
        # 尝试提取代码块
        code_patterns = [
            r'```python\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'代码：\s*\n(.*?)(?:\n\n|$)',
            r'修改后的代码：\s*\n(.*?)(?:\n\n|$)'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, cleaned_output, re.DOTALL)
            if match:
                code = match.group(1).strip()
                if self._is_valid_python_code(code):
                    return code
        
        # 如果没有代码块标记，检查是否整个输出就是代码
        if self._is_valid_python_code(cleaned_output):
            return cleaned_output
        
        # 尝试从"import"开始提取代码
        lines = cleaned_output.split('\n')
        code_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('# '):
                code_start = i
                break
        
        if code_start >= 0:
            code = '\n'.join(lines[code_start:]).strip()
            if self._is_valid_python_code(code):
                return code
        
        # 如果都无法提取，返回一个基础模板
        self.logger.warning("无法提取有效代码，返回基础模板")
        return self._get_basic_template()
    
    def _is_valid_python_code(self, code: str) -> bool:
        """检查是否是有效的Python代码"""
        if not code.strip():
            return False
        
        # 检查是否包含基本的绘图元素
        required_elements = ['matplotlib', 'plt', 'savefig']
        has_required = any(element in code for element in required_elements)
        
        if not has_required:
            return False
        
        # 尝试语法检查
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _get_basic_template(self) -> str:
        """获取基础代码模板"""
        return """import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 创建图形
fig, ax = plt.subplots(figsize=(12, 8))

# 基础散点图
if len(data_df.columns) >= 2:
    numeric_cols = data_df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        plt.scatter(data_df[numeric_cols[0]], data_df[numeric_cols[1]], alpha=0.7)
        plt.xlabel(numeric_cols[0])
        plt.ylabel(numeric_cols[1])
        plt.title(f'{numeric_cols[0]} vs {numeric_cols[1]}')

# 优化布局
plt.tight_layout()

# 保存图表
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()"""
    
    def _format_data_preview(self, head_data: Dict) -> str:
        """格式化数据预览"""
        if not head_data:
            return "暂无数据预览"
        
        try:
            # 只显示前几行和前几列，避免过长
            formatted_lines = []
            for col, values in list(head_data.items())[:5]:  # 最多5列
                if isinstance(values, dict):
                    sample_values = list(values.values())[:3]  # 最多3行
                    formatted_lines.append(f"  {col}: {sample_values}")
            
            return "\n".join(formatted_lines) if formatted_lines else "数据预览格式异常"
            
        except Exception:
            return "数据预览处理失败"
    
    def _format_statistics(self, description: Dict) -> str:
        """格式化统计信息"""
        if not description:
            return "暂无统计信息"
        
        try:
            formatted_lines = []
            for col, stats in list(description.items())[:3]:  # 最多3列统计
                if isinstance(stats, dict):
                    mean_val = stats.get('mean', 'N/A')
                    std_val = stats.get('std', 'N/A')
                    formatted_lines.append(f"  {col}: 均值={mean_val}, 标准差={std_val}")
            
            return "\n".join(formatted_lines) if formatted_lines else "统计信息格式异常"
            
        except Exception:
            return "统计信息处理失败"

# 创建agent实例
interactive_visualization_agent = InteractiveVisualizationAgent() 