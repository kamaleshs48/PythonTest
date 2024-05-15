from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.llms.openai import OpenAI
import pandas as pd
import sqlite3
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.llms.openai import OpenAI
from mykey import OPEN_API_KEY
import os
 
app = FastAPI()
 
os.environ["OPEN_API_KEY"] = OPEN_API_KEY
 
# Load the API key from environment or a secure location
api_key = os.getenv("OPEN_API_KEY")
if not api_key:
    raise EnvironmentError("OPEN_API_KEY not set in the environment")

# Define a Pydantic model for the incoming query data
class QueryModel(BaseModel):
    session_id: str
    query: str

# Initialize the OpenAI LLM
llm = OpenAI(temperature=0.1, api_key=api_key)  # Adjust temperature as needed
sqlite_connection = sqlite3.connect("ksa.db")
 
# Load the data from Excel file into a pandas DataFrame
excel_file_path = r"RB_KSA_Latest_3_Months_Data.xlsx"
data = pd.read_excel(excel_file_path)
 
# Write the data to the SQLite database
data.to_sql("Sales", con=sqlite_connection, index=False, if_exists="replace")
 
# Query data from SQLite table and store it in a pandas DataFrame
df = pd.read_sql("SELECT * FROM Sales", sqlite_connection)
# Create an agent to handle DataFrame based queries
agent = create_pandas_dataframe_agent(llm, df, verbose=True)
 
   
# Define a dictionary to store conversation history for each session
session_conversations = {}
 
@app.get("/")
async def root():
    return "Welcome To FAST API"

@app.post("/ask")
async def ask(query_data: QueryModel):
    try:
        # Extract session ID and query from the request data
        session_id = query_data.session_id
        query = query_data.query
       
 
        # Check if the session ID exists in the session_conversations dictionary
        if session_id not in session_conversations:
            # If the session ID doesn't exist, create a new session and initialize conversation history
            session_conversations[session_id] = []
 
        # Retrieve the conversation history for the session
        conversation_history = session_conversations[session_id]        
        # Append the current query to the conversation history
        conversation_history.append(query)
        # Update the session_conversations dictionary with the new conversation history
        session_conversations[session_id] = conversation_history
 
 
        # Concatenate conversation history to provide context to OpenAI
        context = "\n".join(conversation_history)
        keywords = ['graph','plot','chart','charts','draw','show','plt']

        if any(keyword in query_data.query for keyword in keywords):
            context += r'Do not draw the chart just Give all data in JSON Format strictly with these keys and proper values only (do not make spelling mistake in any key). Take this format as example - { "title": "Leaves ", "labels": [ "Sick Leave", "Casual Leave", "Earned Leave", "Flexi Leave" ], "backgroundColor": [ "#36a2eb", "#ffcd56", "#ff6384", "#009688", "#c45850" ], "chartsData": [ 5, 10, 22, 3 ], "chartType": "pie,bar,any type", "displayLegend": "true" }'

        response = agent.run(context)
 
        # Return the response
        return {"response": response}
    except Exception as e:
        # Handle any exception gracefully
        fallback_response = "An error occurred while processing the response. Please try again later."
        return {"response": fallback_response}