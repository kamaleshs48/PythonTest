from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core import SQLDatabase
from llama_index.llms.openai import OpenAI
import pandas as pd
import sqlite3
import os
 
app = Flask(__name__)
 
# Set the OpenAI API key
api_key = "sk-proj-PDMFh3JgZaKNEFt6wcriT3BlbkFJQfj9lqi4MIC0wuvh6kar"
os.environ["OPENAI_API_KEY"] = api_key
llm = OpenAI(temperature=0.0, model="gpt-3.5-turbo", api_key=api_key)
 
# Step 1: Read the Excel file
excel_file_path = "RB_KSA_Latest_3_Months_Data.xlsx"
df = pd.read_excel(excel_file_path)
 
# Step 2: Create a SQLite database and store the data from the Excel file into it
sqlite_connection = sqlite3.connect("ksa.db")
df.to_sql("sales", con=sqlite_connection, index=False, if_exists="replace")
 
# Step 3: Create an SQLAlchemy engine using the SQLite connection
engine = create_engine("sqlite:///ksa.db")
 
# Step 4: Initialize NLSQLTableQueryEngine with the SQLAlchemy engine
sql_db = SQLDatabase(engine)
query_engine = NLSQLTableQueryEngine(sql_database=sql_db)
 
# Route to handle queries
@app.route("/ask", methods=["POST"])
def ask():
    query_str = request.form.get("query")  # Get query from form data
    response = query_engine.query(query_str)
    return str(response)  # Ensure response is converted to string
 
if __name__ == "__main__":
    app.run(debug=True)