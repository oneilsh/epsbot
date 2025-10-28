from opaiui.app import AgentConfig, AppConfig, serve
from examples.state_example import get_library_agent_config
from examples.mcp_example import get_arxiv_agent_config
from examples.ui_components_example import get_data_collector_agent_config

import streamlit as st

import dotenv
dotenv.load_dotenv(override = True)


agent_configs = {
    # data collector bot is buggy :/
    #"Data Collector Bot": get_data_collector_agent_config(),
    "Library Bot": get_library_agent_config(),
    "arXiv Bot": get_arxiv_agent_config(),
}


app_config = AppConfig(sidebar_collapsed= False,
                       page_icon= "📖",
                       page_title= "Opaiui Demo")

if __name__ == "__main__":
    serve(app_config, agent_configs)