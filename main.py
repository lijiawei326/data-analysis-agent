import asyncio
from agent.load_data_agent import load_data_agent
from agent.data_cleaning_agent import data_cleaning_agent
from agent.analysis_agent import analysis_agent
from agents import Runner, handoff
from custom_types.types import Data, AnalysisContext
from utils.hooks import ExampleHooks, Hooks_with_printer, Hooks_original
from utils.utils import remove_think
from agent.triage_agent import triage_agent
import json
from rich.console import Console
from printer import Printer
from datetime import datetime
from typing import List


class AnalysisManager:
    def __init__(self):
        self.console = Console()
        # self.printer = Printer(self.console)
        # self.hooks = ExampleHooks()
        self.hooks = Hooks_original()
        # self.hooks = Hooks_with_printer(self.printer)
        self.data = AnalysisContext()
        self.message = list()
        
        self.triage = triage_agent
        self.last_agent = self.triage

        ## 编排agent的handoff
        self.triage.handoffs.append(
            handoff(
                agent=load_data_agent,
                tool_name_override="transfer_to_Extractor",
                tool_description_override="当用户需求为从指定路径或数据库提取数据时，转接给Extractor进行数据读取",
            )
        )
        self.triage.handoffs.append(
            handoff(
                agent=data_cleaning_agent,
                tool_name_override="transfer_to_Cleaner",
                tool_description_override="需要进行数据清洗时，转接给Cleaner进行数据清洗。",
            )
        )
        self.triage.handoffs.append(
            handoff(
                agent=analysis_agent,
                tool_name_override="transfer_to_Analysis",
                tool_description_override="当需要进行数据分析/生成报告时，转接给Analysis进行数据分析/生成报告。",
            )
        )
        load_data_agent.handoffs.append(
            handoff(
                agent=self.triage,
                tool_name_override="transfer_to_Triage",
                tool_description_override="确保数据读取完成后，必须返回给triage_agent进行后续处理",
            )
        )
        data_cleaning_agent.handoffs.append(
            handoff(
                agent=self.triage,
                tool_name_override="transfer_to_Triage",
                tool_description_override="确保数据清洗完成后，必须返回给triage_agent进行后续处理",
            )
        )
        analysis_agent.handoffs.append(
            handoff(
                agent=self.triage,
                tool_name_override="transfer_to_Triage",
                tool_description_override="确保数据分析完成后，必须返回给triage_agent进行后续处理",
            )
        )
        # print(extract_data_agent)
    
    async def run(self):
        result = await self.chat_loop()
        if result is not None:
            with open(f'./logs/result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                    json.dump(result.to_input_list(), f, indent=2, ensure_ascii=False)
        # self.printer.end()

    
    async def chat_loop(self):
        print("\n🤖 数据分析智能体已启动！输入 'quit' 退出。")
        last_response = None  # 添加一个变量来存储最后的响应
        while True:
            query = input("\n你: ").strip()
            if query.lower() == "quit":
                break
            try:
                self.message.append({"role": "user", "content": query})
                self.message = self.message[-20:]
                response = await Runner.run(
                    starting_agent=self.last_agent,
                    input = query,
                    context=self.data,
                    hooks=self.hooks
                )
                self.message = response.to_input_list()
                self.last_agent = response.last_agent
                last_response = response  # 保存最后的响应
                print(f"\nAI: {remove_think(response.final_output)}")
            except Exception as e:
                with open(f'./logs/result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                    json.dump(self.message, f, indent=2, ensure_ascii=False)
                print(f"\n⚠️ 调用过程出错: {e}")
        return last_response  # 返回最后的响应

async def main():
    analysis_manager = AnalysisManager()
    await analysis_manager.run()


    # input = "请从test.csv提取数据"
    # result = await Runner.run(
    #     starting_agent=extract_data_agent,
    #     input = input,
    #     context=data
    # )

    # print(result)
    # print(data)

if __name__ == "__main__":
    asyncio.run(main())
