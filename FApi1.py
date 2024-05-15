from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
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
 
# Initialize the OpenAI LLM
llm = OpenAI(temperature=0.7, api_key=api_key)  # Adjust temperature as needed
 
# Define a Pydantic model for the incoming query data
class QueryModel(BaseModel):
    query: str
 
# Define a global variable to store conversation history
conversation_history = []
 
# Route to receive and process the query
@app.post("/ask")
async def ask(query_data: QueryModel):
    try:
        global conversation_history
 
        # Connect to the SQLite database
        sqlite_connection = sqlite3.connect("ksa.db")
 
        # Load the data from the database into a pandas DataFrame
        df = pd.read_sql("SELECT * FROM Sales", sqlite_connection)
 
        # Create an agent to handle DataFrame based queries
        agent = create_pandas_dataframe_agent(llm, df, verbose=True)
 
        # Append the current query to conversation history
        conversation_history.append(query_data.query)
 
        # Concatenate conversation history to provide context to OpenAI
        context = "\n".join(conversation_history)
 
        # Concatenate query and context into a single string
        query_with_context = f"{query_data.query}\n{context}"
        keywords = ['graph','plot','chart','charts','draw','show','plt']
        if any(keyword in query_data.query for keyword in keywords):
            query_with_context += r'Do not draw the chart just Give all data in JSON Format strictly with these keys and proper values only (do not make spelling mistake in any key). Take this format as example - { "title": "Leaves ", "labels": [ "Sick Leave", "Casual Leave", "Earned Leave", "Flexi Leave" ], "backgroundColor": [ "#36a2eb", "#ffcd56", "#ff6384", "#009688", "#c45850" ], "chartsData": [ 5, 10, 22, 3 ], "chartType": "pie,bar,any type", "displayLegend": "true" }'
        # Execute the query using the agent
        response = agent.run(query_with_context)  
 
        # Close the database connection
        sqlite_connection.close()
 
        # Append the response to conversation history
        conversation_history.append(response)
 
        return {"response": response}
    except Exception as e:
        # Handle any exception gracefully
        fallback_response = "An error occurred while processing the response. Please try again later."
        return {"response": fallback_response}