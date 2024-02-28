Chatbot for converting natural language question to SQL queries. Uses gpt-4 for generating responses.

Inputs - requires the schema/metadata of the database it is going to be working with beforehand. Specified in the 'schema.txt' file for t2sql.py and pulls from the e6 engine in e6conn.py

Before running the program, please install the prerequisites - 
```
pip install requirements.txt
```
Before running the program, add your OpenAI API Key to the program.

You can then just run the chatbots using either of the following commands - 
```
streamlit run e6conn.py
streamlit run t2sql.py
```
