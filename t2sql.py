from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import streamlit as st
import os

# Add openai access token here
# OPENAI_ACCESS_TOKEN = 
model="gpt-4-1106-preview"

#setting up schema
os.getcwd()
schema_file=open('schema.txt','r')
schema=schema_file.read()

# Setting up the prompt directives
directives_file=open('directives.txt','r')
directives = directives_file.read()


st.set_page_config(page_title="Text2SQL", page_icon="🦜")
st.title("🦜 LangChain: Text2SQL")


# Set up memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

view_messages = st.expander("View the message contents in session state")

# Get an OpenAI API Key before continuing
openai_api_key=OPENAI_ACCESS_TOKEN

# Prompt

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", f"Given the following SQL table schema, your job is to write SQL queries given a user's request.\nThe schema being given is:\n{schema}\n{directives}."
),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

chain = prompt | ChatOpenAI(temperature=0.2, api_key=openai_api_key, model=model)
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,
    input_messages_key="question",
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
    response = chain_with_history.invoke({"question": prompt}, config)
    st.chat_message("ai").write(response.content)

# Draw the messages at the end, so newly generated ones show up immediately
with view_messages:
    view_messages.json(st.session_state.langchain_messages)


