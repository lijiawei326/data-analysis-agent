import asyncio
from agent.extract_data_agent import extract_data_agent
from agents import Runner
from custom_types.types import Data


data = Data(data={"data": None, "washed": False})
print(data)
async def main():
    result = await Runner.run(
        starting_agent=extract_data_agent,
        input = "请从test.csv提取数据",
        context=data
    )

    print(result)
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
