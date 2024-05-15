from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import pandas as pd
import sqlite3
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.llms.openai import OpenAI
from mykey import OPEN_API_KEY
import os
os.environ["OPENAI_API_KEY"] = OPEN_API_KEY

app = FastAPI()

# Load the API key from environment or a secure location
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set in the environment")

# Initialize the OpenAI LLM
llm = OpenAI(temperature=0, api_key=api_key)

# Define a Pydantic model for the incoming query data
class QueryModel(BaseModel):
    query: str

# Route to receive and process the query
@app.post("/ask")
async def ask(query_data: QueryModel):
    try:
        # Connect to the SQLite database
        sqlite_connection = sqlite3.connect("ksa.db")
        
        # Load the data from the database into a pandas DataFrame
        df = pd.read_sql("SELECT * FROM Sales", sqlite_connection)
        
        # Create an agent to handle DataFrame based queries
        agent = create_pandas_dataframe_agent(llm, df, verbose=True)
        
        # Append conditions for JSON format based on the presence of keywords
        query = query_data.query
        keywords = ['graph', 'plot', 'chart', 'charts','tabular','table']
        if any(keyword in query for keyword in keywords):
            query += r'Do not draw the chart just Give all data in JSON Format strictly with these keys and proper values only (do not make spelling mistake in any key). Take this format as example - { "title": "Leaves ", "labels": [ "Sick Leave", "Casual Leave", "Earned Leave", "Flexi Leave" ], "backgroundColor": [ "#36a2eb", "#ffcd56", "#ff6384", "#009688", "#c45850" ], "chartsData": [ 5, 10, 22, 3 ], "chartType": "pie,bar,any type", "displayLegend": "true" }'
        
        
        # Execute the query using the agent
        response = agent.run(query)
        
        # Close the database connection
        sqlite_connection.close()
        
        return {"response": response}       
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

