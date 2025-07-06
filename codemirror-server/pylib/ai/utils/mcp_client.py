from mcp import ClientSession
from mcp.client.sse import sse_client
from typing import Optional
import json
from mcp.server.fastmcp.server import Settings

from pylib.basic.sync import sync


class ClientSync:
    def __init__(self, host, port=None):
        self.tools = []
        settings = Settings()
        self.host = host
        if port is None:
            settings = Settings()
            self.port = settings.port
        else:
            self.port = port

        self.server_url = f"http://{host}:{port}/sse"

    async def _list_tools(self):
        async with sse_client(self.server_url) as (read_streams, write_stream):
            async with ClientSession(read_streams, write_stream) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools

    def list_tools(self):
        return sync(self._list_tools)

    async def _call_tool(self, tool_name, **kwargs):
        async with sse_client(self.server_url) as (read_streams, write_stream):
            async with ClientSession(read_streams, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, kwargs)
                result = result.content[0].text
                try :
                    result = json.loads(result)
                except:
                    pass
                return result

    def call_tool(self, tool_name, **kwargs):
        ret = sync(self._call_tool, tool_name, **kwargs)
        return ret


if __name__ == "__main__":
    client = ClientSync()
    client.connect_mcp_server(host='127.0.0.1')
