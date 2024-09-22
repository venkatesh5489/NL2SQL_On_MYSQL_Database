import os
import streamlit as st
from langchain.chains import create_sql_query_chain
from langchain_google_genai import GoogleGenerativeAI
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
db_user = "root"
db_password = "123456"
db_host = "localhost"
db_name = "retail_sales_db"

# Create SQLAlchemy engine
engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

# Initialize SQLDatabase
db = SQLDatabase(engine, sample_rows_in_table_info=3)

# Initialize LLM (Google Generative AI)
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.environ["GOOGLE_API_KEY"])

# Create SQL query chain
chain = create_sql_query_chain(llm, db)

# Function to execute the SQL query
def execute_query(question, chain, db):
    try:
        # Generate the SQL query based on the question
        response = chain.invoke({"question": question})
        
        # Extract the SQL query part from the response
        cleaned_query = response.split('SQLQuery: ')[1].strip()
        
        # Execute the cleaned query
        result = db.run(cleaned_query)
        
        return cleaned_query, result
    except ProgrammingError as e:
        st.error(f"Database error: {str(e)}")
        return None, None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

# Streamlit interface
st.title("Natural Language to SQL Query App")

# Input from the user
question = st.text_input("Enter your question:")

if st.button("Execute"):
    if question:
        # Execute the query and get the result
        cleaned_query, query_result = execute_query(question, chain, db)
        
        if cleaned_query and query_result is not None:
            # Display the generated SQL query and results
            st.write("Generated SQL Query:")
            st.code(cleaned_query, language="sql")
            st.write("Query Result:")
            st.write(query_result)
        else:
            st.write("No result returned due to an error.")
    else:
        st.write("Please enter a question.")
