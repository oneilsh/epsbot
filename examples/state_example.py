from pydantic_ai import Agent
from pydantic_ai.tools import RunContext

import streamlit as st
from opaiui.app import AgentConfig, AppConfig, AgentState, current_deps, serve


def get_library_agent_config() -> AgentConfig:

    ###############
    ## Agent Definition
    ###############


    agent = Agent('openai:gpt-4o')


    ################
    ## Deps and Tools
    ################

    # Library objects have a self.state, which will to saved and reloaded
    # in shared sessions.
    class Library():
        def __init__(self):
            self.state = AgentState()
            self.state.library = []

        def add(self, article: str):
            self.state.library.append(article)

        def as_markdown(self) -> str:
            if not self.state.library:
                return "None"
            return "\n".join(f"- {entry}" for entry in self.state.library)

    # this tool is in addition to those provided by the MCP server.
    @agent.tool
    async def add_to_library(ctx: RunContext[Library], article: str) -> str:
        deps = current_deps() # or ctx.deps (pydantic.ai standard)
        deps.add(article)
        return f"Article added. Current library size: {len(deps.state.library)}"


    ################
    ## Sidebar function
    ################


    async def library_sidebar():
        """Render the agent's sidebar in Streamlit."""
        deps = current_deps()

        st.markdown("### Library")
        st.markdown(deps.as_markdown())
        
        if st.button("Clear Library"):
            deps.state.library = []
            st.rerun()


    ################
    ## Agent Config
    ################

    # We configure UI elements and set dependencies for agents, as a dictionary
    # mapping agent names to AgentConfig instances.

    library_agent_config = AgentConfig(agent = agent,
                                deps = Library(),
                                sidebar_func = library_sidebar,
                                greeting= "Hello! What should we learn about today?",
                                agent_avatar= "📖")

    return library_agent_config

################
## App Config and serve
################

# start the app with serve, or use the function above importing this file as a module.
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(override = True)

    app_config = AppConfig(sidebar_collapsed= False,
                       page_icon= "📖",
                       page_title= "Library Bot")

    agent_configs = {
        "Library Bot": get_library_agent_config()
    }

    serve(app_config, agent_configs)

