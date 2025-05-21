from typing import Any

from agents import Agent, RunContextWrapper, RunHooks, Tool, Usage
from printer import Printer
from utils.utils import remove_think


class ExampleHooks(RunHooks):
    def __init__(self):
        self.event_counter = 0

    def _usage_to_str(self, usage: Usage) -> str:
        return f"{usage.requests} requests, {usage.input_tokens} input tokens, {usage.output_tokens} output tokens, {usage.total_tokens} total tokens"

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        print(
            f"### {self.event_counter}: Agent {agent.name} started. Usage: {self._usage_to_str(context.usage)}"
        )

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.event_counter += 1
        print(
            f"### {self.event_counter}: Agent {agent.name} ended with output {output}. Usage: {self._usage_to_str(context.usage)}"
        )

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.event_counter += 1
        print(
            f"### {self.event_counter}: Tool {tool.name} started. Usage: {self._usage_to_str(context.usage)}"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        self.event_counter += 1
        print(
            f"### {self.event_counter}: Tool {tool.name} ended with result {result}. Usage: {self._usage_to_str(context.usage)}"
        )

    async def on_handoff(
        self, context: RunContextWrapper, from_agent: Agent, to_agent: Agent
    ) -> None:
        self.event_counter += 1
        print(
            f"### {self.event_counter}: Handoff from {from_agent.name} to {to_agent.name}. Usage: {self._usage_to_str(context.usage)}"
        )


class Hooks_with_printer(RunHooks):
    def __init__(self, printer: Printer):
        print = printer
        self.event_counter = 0
        # print.update_item("print", "##############开始工作##############", is_done=True, hide_checkmark=True)
    async def on_agent_start(self, context: RunContextWrapper, agent: Agent) -> None:
        if self.event_counter == 0:
            print.update_item("print", "##############开始工作##############", is_done=True, hide_checkmark=True)
        print.update_item("usage", f"使用token数量：{context.usage.total_tokens}", hide_checkmark=True)
        # print(f'当前context为：{context.context}')
        # print('#########################')
        # print(agent)
        # print('#########################')
        print.update_item("agent_start", f"智能体 {agent.name} 开始工作...", is_done=True, hide_checkmark=True)
        self.event_counter += 1

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        print.update_item("usage", f"使用token数量：{context.usage.total_tokens}", hide_checkmark=True)
        # print(f'当前context为：{context.context}')
        print.update_item("agent_end", f"Agent {agent.name} ended with output {output}", is_done=True, hide_checkmark=True)
        self.event_counter += 1

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        print.update_item("usage", f"使用token数量：{context.usage.total_tokens}", hide_checkmark=True)
        # print(f'当前context为：{context.context}')
        print(tool)
        print.update_item(tool.name, f"工具 {tool.name} 开始执行...")
        self.event_counter += 1
    
    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        print.update_item("usage", f"使用token数量：{context.usage.total_tokens}", hide_checkmark=True)
        if tool.name == 'fetch_data_info':
            print.mark_item_done(tool.name)
        elif tool.name == 'analysis_single_variable':
            task_name = result['variable']
            print.update_item(task_name, f"变量 {task_name} 的分析结果为：\n {result['description_analysis'].final_output}", is_done=True)
        else:
            print.update_item(tool.name, f"工具 {tool.name} 调用的结果为：\n {result}", is_done=True)
        self.event_counter += 1

    async def on_handoff(self, context: RunContextWrapper, from_agent: Agent, to_agent: Agent) -> None:
        print.update_item("usage", f"使用token数量：{context.usage.total_tokens}", hide_checkmark=True)
        # print(f'当前context为：{context.context}')
        print.update_item(
            f"handoff_{from_agent.name}_to_{to_agent.name}", 
            f"智能体交接：从 {from_agent.name} 交接至 {to_agent.name}",
            is_done=True,
            hide_checkmark=True
        )
        self.event_counter += 1


class Hooks_original(RunHooks):
    def __init__(self,):
        self.event_counter = 0

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent) -> None:
        # print(f"使用token数量：{context.usage.total_tokens}")
        print(f"智能体 {agent.name} 开始工作...")
        self.event_counter += 1

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        # print(f"使用token数量：{context.usage.total_tokens}")
        print(f"Agent {agent.name} 结束工作")
        print(f"{agent.name}: \n {remove_think(output)}")
        self.event_counter += 1

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        # print(f"使用token数量：{context.usage.total_tokens}")
        # print(f'当前context为：{context.context}')
        # print(tool)
        print(f"工具 {tool.name} 开始执行...")
        self.event_counter += 1
    
    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        # print(f"使用token数量：{context.usage.total_tokens}")
        result = remove_think(str(result))
        print_output = result[:200] if len(result) > 200 else result
        print(f"工具 {tool.name} 执行完成。执行结果为：\n{print_output}")

        self.event_counter += 1

    async def on_handoff(self, context: RunContextWrapper, from_agent: Agent, to_agent: Agent) -> None:
        # print(f"使用token数量：{context.usage.total_tokens}")
        # print(f'当前context为：{context.context}')
        print(f"智能体交接：从 {from_agent.name} 交接至 {to_agent.name}")
        self.event_counter += 1

