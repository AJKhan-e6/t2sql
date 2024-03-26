from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import Chroma
from langchain.tools.retriever import create_retriever_tool
from langchain.text_splitter import MarkdownTextSplitter
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.callbacks import get_openai_callback
import streamlit as st
import os
import json

OPENAI_ACCESS_TOKEN = 
model = "gpt-4-turbo-preview"

# setting up schema
os.getcwd()
# schema_file = open("chargebee_schema.txt", "r")
# schema = schema_file.read()
with open(
    "/home/abdul/Downloads/ml-projects/processed_table_metadata.json", "r"
) as file:
    schema = json.load(file)

# Setting up the documentation path
document_path = "./supported-sql-functions"

# Setting up the prompt directives
directives_file = open("directives.txt", "r")
directives = directives_file.read()

st.set_page_config(page_title="Text2SQL", page_icon="🦜")
st.title("🦜 LangChain: Text2SQL")

# Initialize st.session_state["langchain_messages"]
if "langchain_messages" not in st.session_state:
    st.session_state["langchain_messages"] = []  # Empty list for message history


# Initialize st.session_state["langchain_messages"]
if "langchain_messages" not in st.session_state:
    st.session_state["langchain_messages"] = []  # Empty list for message history


# Set up memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

view_messages = st.expander("View the message contents in session state")

# Get an OpenAI API Key before continuing
openai_api_key = OPENAI_ACCESS_TOKEN


@st.cache_resource(show_spinner=False)
def load_data():

    # Setting up the document indexing
    docs = DirectoryLoader(
        document_path,
        glob="**/*.md",
        loader_cls=UnstructuredMarkdownLoader,
        use_multithreading=True,
        recursive=True,
    ).load()
    split_text = MarkdownTextSplitter(chunk_size=128, chunk_overlap=60).split_documents(
        docs
    )
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-large", api_key=openai_api_key
    )
    db = Chroma.from_documents(split_text, embedding_model)
    retriever = db.as_retriever()
    return retriever


retriever = load_data()
# Making a retriever tool
tool = create_retriever_tool(
    retriever,
    "supported_functions",
    "Contains the list of all functions supported by e6data.",
)
tools = [tool]

# Convert schema to string
schema_str = json.dumps(schema)

# Escape curly braces
escaped_schema = schema_str.replace("{", "{{").replace("}", "}}")

# Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"Given the following SQL table schema, your job is to write SQL queries given a user's request.\nThe schema being given is:\n{escaped_schema}\n{directives}. Use the retreiver tool to find the correct supported functions and use them in the query.",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Chat agent core
chat = ChatOpenAI(temperature=0.2, api_key=openai_api_key, model=model, timeout=600)
agent = create_openai_tools_agent(llm=chat, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Making a runnable memory chain
chain_with_history = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: msgs,
    input_messages_key="question",
    output_messages_key="output",
    history_messages_key="history",
)


# Render current messages from StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# If user inputs a new prompt, generate and draw a new response
if prompt := st.chat_input():
    st.chat_message("human").write(prompt)
    # Note: new messages are saved to history automatically by Langchain during run
    config = {"configurable": {"session_id": "any"}}
    with get_openai_callback() as cb:
        response = chain_with_history.invoke({"question": prompt}, config)
        print(f"Total Tokens: {cb.total_tokens}")
        print(f"Prompt Tokens: {cb.prompt_tokens}")
        print(f"Completion Tokens: {cb.completion_tokens}")
        print(f"Total Cost (USD): ${cb.total_cost}")
    output = response.get("output")
    st.chat_message("ai").write(output)

# Draw the messages at the end, so newly generated ones show up immediately
with view_messages:
    view_messages.json(st.session_state.langchain_messages)
