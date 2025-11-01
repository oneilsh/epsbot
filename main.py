from pydantic_ai import Agent
from pydantic_ai.tools import RunContext

import streamlit as st
from opaiui.app import AgentConfig, AppConfig, AgentState, current_deps, serve, render_in_chat

from defs import fetch_markdown_content, fetch_bibtex_content

import dotenv
dotenv.load_dotenv(override = True)


desc = fetch_markdown_content()
bibtex, bibtex_dict = fetch_bibtex_content()

print(bibtex_dict["O-Neil2024-gq"])

# desc contains strings like {% cite O-Neil2024-gq %} {% cite McCorkell2021-am %}
# bibtex_dict contains keys like O-Neil2024-gq and McCorkell2021-am; entries are bibtex parsed
# dictionaries, e.g.
# {'language': 'en', 'doi': '10.1038/s41746-024-01286-3', 'url': 'http://dx.doi.org/10.1038/s41746-024-01286-3', 'year': '2024', 'month': '21~October', 'abstract': 'Post-Acute Sequelae of SARS-CoV-2 infection (PASC), also known as\nLong-COVID, encompasses a variety of complex and varied outcomes\nfollowing COVID-19 infection that are still poorly understood. We\nclustered over 600 million condition diagnoses from 14 million\npatients available through the National COVID Cohort\nCollaborative (N3C), generating hundreds of highly detailed\nclinical phenotypes. Assessing patient clinical trajectories\nusing these clusters allowed us to identify individual conditions\nand phenotypes strongly increased after acute infection. We found\nmany conditions increased in COVID-19 patients compared to\ncontrols, and using a novel method to associate patients with\nclusters over time, we additionally found phenotypes specific to\npatient sex, age, wave of infection, and PASC diagnosis status.\nWhile many of these results reflect known PASC symptoms, the\nresolution provided by this unprecedented data scale suggests\navenues for improved diagnostics and mechanistic understanding of\nthis multifaceted disease.', 'pages': '296', 'number': '1', 'volume': '7', 'publisher': 'Nature Publishing Group', 'journal': 'NPJ Digit. Med.', 'author': "O'Neil, Shawn T and Madlock-Brown, Charisse and Wilkins, Kenneth\nJ and McGrath, Brenda M and Davis, Hannah E and Assaf, Gina S and\nWei, Hannah and Zareie, Parya and French, Evan T and Loomba,\nJohanna and McMurry, Julie A and Zhou, Andrea and Chute,\nChristopher G and Moffitt, Richard A and Pfaff, Emily R and Yoo,\nYun Jae and Leese, Peter and Chew, Robert F and Lieberman,\nMichael and Haendel, Melissa A and {N3C and RECOVER Consortia}", 'title': 'Finding Long-{COVID}: temporal topic modeling of electronic\nhealth records from the {N3C} and {RECOVER} programs', 'ENTRYTYPE': 'article', 'ID': 'O-Neil2024-gq'}

# we need to replace strings like {% cite O-Neil2024-gq %} with markdown-formatted 
# links of the form ([Last Name et al., year](url or doi url)), with the url or doi url being the url or doi url from the bibtex entry; if neither is available, do not format as a link.

def format_citations(desc: str) -> str:
    """
    Format citations in the markdown content.
    """
    for key, entry in bibtex_dict.items():
        if entry['url'] or entry['doi']:
            desc = desc.replace(f"{{% cite {key} %}}", f"([{entry['author']}, {entry['year']}]({entry['url'] or entry['doi']}))")
        else:
            desc = desc.replace(f"{{% cite {key} %}}", f"({entry['author']}, {entry['year']})")
    return desc

desc = format_citations(desc)
print(desc)


system_prompt = f"""
You are a helpful assistant that can answer questions about the project described in the following markdown content:

```
{desc}
```

Instructions:

- Refuse to answer questions that are not related to the project.
- Do not guess about answers that are not available in the project description or reference database; instead, refer the asker to the project authors.
- Before answering a question, ensure the user has proper background knowledge about the project, which may mean providing a brief summary of the project if it has not been previously discussed. Do not assume the user is familiar with the project; treat them as a reviewer deciding if the project is worth funding as part of a program about anxiety, depression, and generative AI applications.
- If a figure is relevant to your answer, display it using the display_figure tool. Note that you cannot use the markdown syntax provided in the project description; you must pass the filename and caption to the display_figure tool. 
- Always provide references as inline markdown links, looking up details by citation key using the get_references_data tool BEFORE your answer. Format citations as e.g. "... estimated 279 and 458 million individuals respectively as of 2019 ([Wang 2025](https://doi.org/10.3389/fpubh.2025.1556981), [Zhang 2024]()https://www.sciencedirect.com/science/article/pii/S0165032725017410)."
- Format your response with markdown headings, italics, and bold as appropriate to make it easy to read and understand.
- Prefer brief answers that prompt discovery via follow-up questions from the user.
- You may display figures inline as markdown images in your reponse, but you must specify the full URL as e.g. https://raw.githubusercontent.com/oneilsh/wellcome-poster-supplement/HEAD/images/gantt.png.
"""



agent = Agent('openai:gpt-4.1', system_prompt = system_prompt)


@agent.tool
async def get_references_data(ctx: RunContext, citation_keys: list[str]) -> str:
    """ 
    Retrieve bibtext entries for the given citation keys.

    Args:
        citation_keys: List of citation keys to retrieve.

    Returns:
        String containing the bibtext entries for the given citation keys.
    """
    return "\n".join(f"[{citation_key}]({bibtex_dict[citation_key]})" for citation_key in citation_keys)


async def render_figure_from_url(url: str, caption: str = None) -> None:
    """
    Render a figure from a URL in the chat.

    Args:
        url: The URL of the figure to display.
        caption: The caption of the figure to display.
    """
    st.image(url, caption = caption)


# @agent.tool
# async def display_figure(ctx: RunContext, figure_filename: str, figure_caption: str) -> str:
#     """
#     Display the given figure in the chat.

#     Args:
#         figure_filename: The filename of the figure to display, e.g. "gantt.png"
#         figure_caption: The caption of the figure to display.
#     """
#     # e.g. https://raw.githubusercontent.com/oneilsh/wellcome-poster-supplement/HEAD/images/gantt.png
#     base_url = "https://raw.githubusercontent.com/oneilsh/wellcome-poster-supplement/HEAD/images/"
#     url = f"{base_url}{figure_filename}"
#     await render_in_chat("render_figure_from_url", {"url": url, "caption": figure_caption}, before_agent_response = False)
#     return "The figure has been displayed in the chat for the user, you may describe it in your response."



################
## Sidebar function
################


agent_config = AgentConfig(agent = agent,
                            greeting= """
Welcome! I'm here to answer quesetions you may have about **Extract, Predict, Support: Improving Medication Choice and Outcomes from Clinical Data to Decision Support.**

What would you like to know about the project?
                            """.strip(),
                            suggested_questions = [
                              "What is this project about?",
                              "How large of a problem is medication choice for anxiety and depression?",
                              "Can you really predict which medications will work best?",
                              "Why has no one done this yet? Where does AI fit in?",
                              "What about clinical note data?",
                              "How are you incorporating lived experiences of those with Anxiety and Depression?",
                              "Can you find and use novel patterns in data about anxiety and depression?",
                              "What databases or other resources will you use?",
                              "How will you protect patient privacy?",
                              "How will you ensure your work is conducted ethically?",
                              "Who is on your team?",
                              "Where would clinicians utilize your tool? Would patients be able to access it?",
                              "Can you do this efficiently? How will you evaluate the components?"
                            ],
                            enable_suggested_questions = True,
                            hide_suggested_questions_after_first_interaction = False,
                            rendering_functions = [render_figure_from_url],
                            agent_avatar= "📖")


###############
## App Config and serve
################


app_config = AppConfig(sidebar_collapsed= False,
                   page_icon= "📖",
                   page_title= "Library Bot")


agent_configs = {
    "Extract, Predict, Support": agent_config
}

print(agent_config)
serve(app_config, agent_configs)