from agents import Runner, Agent, ModelSettings, handoff
from custom_types.types import AnalysisContext
from agent.conversation_agent import conversation_agent
import asyncio
import os
import json
from typing import Optional, Dict
from utils.hooks import Hooks_original
from datetime import datetime
from utils.utils import remove_think
from agent.analysis_agent import analysis_agent


class Client:
    def __init__(self):
        self.message = list()
        self.hooks = Hooks_original()
        self.context = AnalysisContext()
        self.init_agents()
        self.init_handoff()

    def init_agents(self):
        self.conversation_agent = conversation_agent
        self.analysis_agent = analysis_agent
        self.last_agent = self.conversation_agent

    def init_handoff(self):
        self.conversation_agent.handoffs.append(
            handoff(
                agent=self.analysis_agent,
                tool_name_override="analysis_agent",
                tool_description_override="分析智能体，用于进行数据分析。"
            )
        )
        self.analysis_agent.handoffs.append(
            handoff(
                agent=self.conversation_agent,
                tool_name_override="conversation_agent",
                tool_description_override="对话智能体，用于进行日常对话。"
            )
        )

    async def chat_base(self, messages: list) -> list:
        response = await Runner.run(
            starting_agent=self.last_agent,
            input=messages,
            context=self.context,
            hooks=self.hooks
        )
        self.last_agent = response.last_agent
        return response
    
    async def chat_loop(self):
        print("\n🤖 客户端已启动！输入 'quit' 退出。")
        while True:
            query = input("\n你: ").strip()
            if query.lower() == "quit":
                break
            try:
                self.message.append({"role": "user", "content": query})
                self.message = self.message[-20: ]
                # print(messages)
                response = await self.chat_base(self.message)
                self.message = response.to_input_list()
                result = remove_think(response.final_output)
                # print(f"\nAI: {result}")
            except Exception as e:
                print(f"\n⚠️ 调用过程出错: {e}")

    async def save_message(self):
        with open(f'./logs/result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(self.message, f, indent=2, ensure_ascii=False)

async def main():
    # 服务器脚本
    client = Client()
    await client.chat_loop()
    await client.save_message()

if __name__ == "__main__":
    asyncio.run(main())

