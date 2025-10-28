from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
import sys

from opaiui.app import AgentConfig, AppConfig, serve

def get_arxiv_agent_config() -> AgentConfig:

    ###############
    ## Agent Definition
    ###############

    # This agent uses the MCP server defined in arxiv_mcp.py to search for papers on arXiv.
    # sys.executable is the preferred way execute the current Python interpreter in a streamlit app,
    # see https://docs.streamlit.io/knowledge-base/deploy/invoking-python-subprocess-deployed-streamlit-app
    arxiv_mcp = MCPServerStdio(
        command = f"{sys.executable}",
        args = ["examples/arxiv_mcp.py"],
    )

    agent = Agent('openai:gpt-4o', toolsets = [arxiv_mcp])

    arxiv_agent_config = AgentConfig(agent = agent,
                             greeting= "Hello! What can I help you find on arXiv today?",
                             agent_avatar= "📖")

    # that's it - the agent will have access to the MCP server and can use its tools.
    # note that due to the way Pydantic.AI manages tool context, MCP server connections
    # will be reinitialized for each request, which may cause delays if this is a long-running process.

    return arxiv_agent_config

################
## App Config and serve
################

# start the app with serve, or use the function above importing this file as a module.
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(override = True)

    app_config = AppConfig(sidebar_collapsed= False,
                       page_icon= "📖",
                       page_title= "MCP Bot")

    agent_configs = {
        "arXiv Bot": get_arxiv_agent_config()
    }

    serve(app_config, agent_configs)

