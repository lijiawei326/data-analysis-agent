from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ExtractData")

@mcp.tool()
async def extract_data(data_path: str):
    """
    从指定路径提取数据
    :param data_path: 数据路径
    :return: 提取的数据
    """
    return f"已从{data_path}提取数据"

if __name__ == "__main__":
    mcp.run(transport="stdio")
