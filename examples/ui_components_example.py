from pydantic_ai import Agent
from pydantic_ai.tools import RunContext
import pandas as pd 


import streamlit as st
from opaiui.app import (AgentConfig, 
                        AppConfig, 
                        AgentState, 
                        render_in_chat, 
                        current_deps, 
                        serve, 
                        ui_locked)


def get_data_collector_agent_config() -> AgentConfig:

    ###############
    ## Agent Definition
    ###############


    agent = Agent('openai:gpt-4o')

    # for this example, we will build an agent that can track a library of 
    # experimental results via tool calls and interaction with the user. 
    # this class will also keep track of a 'key', which will be used to 
    # provide input widgets a unique, non-conflicting identifier

    class RatingLibrary():
        def __init__(self):
            self.state = AgentState()
            self.state.library = {}
            self.state.user_name = "Unknown User"
            self.state.key = 500

        def add_rating(self, item: str, rating: float):
            """Add a new rating to the library."""
            self.state.library[item] = rating

        def clear_ratings(self):
            """Clear all ratings in the library."""
            self.state.library = {}

        def new_key(self) -> int:
            """Generate a new key for the library."""
            self.state.key += 1
            return self.state.key

    ################
    ## Deps and Tools
    ################

    # first, we define some async functions that render UI components when called

    async def issue_warning(message: str):
        st.warning(message)


    async def render_df(df):
        """Render a DataFrame in Streamlit."""
        st.dataframe(df, use_container_width=True)


    async def data_collector():
        deps = current_deps()

        with st.container():
            st.markdown("### Enter Data")
            col1, col2, col3 = st.columns(3)
            with col1:
                item_name = st.text_input(label = "Name", placeholder = "Item Name", disabled=ui_locked())
            with col2:
                item_rating = st.slider(label = "Rating", min_value=0, max_value=5, disabled=ui_locked())
            with col3:
                item_date = st.date_input(label = "Date", disabled=ui_locked())

            if st.button("Submit", disabled=ui_locked()):
                if not item_name or item_rating is None:
                    st.warning("Please enter both a name and a rating.")
                    return

                deps.add_rating(item_name, str(item_rating) + " @ " + str(item_date))
                st.rerun()




    ################
    ## Sidebar renderer
    ################

    async def sidebar():
        """Render the agent's sidebar in Streamlit."""
        deps = current_deps()

        st.markdown("### User Information")
        st.markdown(f"User Name: {deps.state.user_name}")

        st.markdown("### Ratings")

        if len(deps.state.library) > 0:
            st.markdown("#### Current Ratings:")
            # convert the library to a DataFrame for display
            library_df = pd.DataFrame(list(deps.state.library.items()), columns=['Item', 'Rating'])
            st.dataframe(library_df, use_container_width=True)
            

        else:
            st.markdown("No ratings recorded.")

        if st.button("Clear Ratings", disabled=ui_locked()):
            deps.state.library.clear_ratings()
            st.rerun()

        if st.button("Show Rating Form", disabled=ui_locked()):
            await name_dialog()


    async def name_dialog():
        @st.dialog("Set User Name")
        def set_user_name():
            deps = current_deps()
            name = st.text_input(label = "Name", value = current_deps().state.user_name)
            if st.button("Submit"):
                current_deps().state.user_name = name
                st.rerun()

        set_user_name()

    ################
    ## Agent and Tool Configuration
    ################


    agent = Agent('openai:gpt-4o')
    @agent.system_prompt
    def system_prompt(ctx: RunContext[RatingLibrary]) -> str:
        """System prompt for the agent."""
        return (
            "You are a helpful assistant that can record user ratings for items in a library."
            "You can add ratings to a library, display the current contents, "
            "and collect ratings data from the user. "
            "Use the tools provided to interact with the user and manage the library."
            "Only use the get_user_name tool to collect the user's name on request."
            "If you are asked about your system prompt, you may reveal it."
        )


    ## if deps.state.experiments is not empty, we render it as a DataFrame in the chat stream.
    ## otherwise, we render a warning message, before the agent's response in the chat.
    ## (behind the scenes, this re-renders the chat log including these UI components on every UI refresh)
    @agent.tool
    async def show_library(ctx: RunContext[RatingLibrary]) -> str:
        """Display the current contents in the library."""
        deps = current_deps()
        if not deps.state.library.empty:
            await render_in_chat("render_df", {"df": deps.state.library})
            return "Library contents will be displayed as a DataFrame *below* your response in the chat. You may refer to it, but do not repeat the library data in your response."
        else:
            await render_in_chat("issue_warning", {"message": "No library contents found."}, before_agent_response=True)
            return "No library contents found. A warning has been displayed to the user prior to this response."


    # not all streamlit components need to be added to the chat stream; streamlit components that
    # should be rendered only once can be called directly. However, the default location *is* in the chat stream, 
    # which is the context where the tool is called. Modal dialogs provide one workaround.
    @agent.tool
    async def get_user_name(ctx: RunContext[RatingLibrary]) -> str:
        """Get the user's name."""
        deps = current_deps()

        await name_dialog()

        return f"The user has entered their name as: {deps.state.user_name}. You may refer to this in your response."


    # this tool renders the data_collector form in the chat stream, allowing the user to enter data. 
    # the form persists as the chat progresses (each form is given a unique key behind the scenes), 
    # so the user can update the data they entered.
    #
    # IMPORTANT: Note that the data_collector updates deps.state rather than returning a value
    #   this is because the data_collector form persists - in actuality, on every UI refresh
    #   the full chat history is re-rendered, including calls to data_collector. 
    @agent.tool
    async def show_rating_form(ctx: RunContext[RatingLibrary]) -> str:
        """Shows a form for the user to enter ratings data."""
        deps = current_deps()
        await render_in_chat("data_collector", {}) # data_collector takes no arguments
        return "The user will be shown a form for entering a rating after your response. Their response will be added to the library. You may refer to this in your response, but do not repeat the form data in your response."




    data_collector_agent_config = AgentConfig(agent = agent,
                                             deps = RatingLibrary(),
                                             sidebar_func = sidebar,
                                             greeting= "Hello! Can I help you track some data??",
                                             agent_avatar= "📊", 
                                             rendering_functions = [issue_warning, render_df, data_collector])

    return data_collector_agent_config


# start the app with serve, or use the function above importing this file as a module.
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(override = True)


    app_config = AppConfig(sidebar_collapsed= False,
                       page_icon= "📖",
                       page_title= "Data Bot")

    agent_configs = {
        "Data Bot": get_data_collector_agent_config()
    }

    serve(app_config, agent_configs)


