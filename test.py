from agents import Runner, Agent
from model_provider.model_provider import MODEL_PROVIDER
from agents.mcp.server import MCPServerSse, MCPServerSseParams
from datetime import timedelta
import asyncio

async def main():
    params = MCPServerSseParams(
        url="http://localhost:8000/sse/",
        timeout=180
    )

    async with MCPServerSse(name="Assistant", params=params) as mcp:
        analysis_agent = Agent(
            name="analysis_agent",
            instructions="""
            你是一个数据分析专家，负责生成数据分析报告。
            """,
            model=MODEL_PROVIDER.get_model(None),
            mcp_servers=[mcp]
        )
        report = await Runner.run(
            starting_agent=analysis_agent,
            input="分析./test.csv"
            )
        print(report)

if __name__ == "__main__":
    asyncio.run(main())