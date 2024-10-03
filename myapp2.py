import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from langchain.chains import create_sql_query_chain
from langchain_google_genai import GenAIAqa, GoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
import google.generativeai as genai
import nltk
from nltk.tokenize import word_tokenize


api_key = "AIzaSyCH_S-qA2wbGSE-db_Fj8w8059dpjDkEOs"
genai.configure(api_key=api_key)


# Initialize Streamlit session state for conversation history, db, and chain
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'db' not in st.session_state:
    st.session_state.db = None
if 'chain' not in st.session_state:
    st.session_state.chain = None

# Frontend for the MySQL connection details
st.title("Conversational MySQL Query App")
st.write("Enter your MySQL connection details below.")

# Input fields for database connection
db_user = st.text_input("MySQL Username", value="root")
db_password = st.text_input("MySQL Password", value="", type="password")
db_host = st.text_input("MySQL Host", value="localhost")
db_name = st.text_input("Database Name", value="sakila")

# Button to connect to the database
if st.button("Connect to Database"):
    try:
        # Create SQLAlchemy engine using user inputs
        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

        db = SQLDatabase(engine=engine)
        # Initialize SQLDatabase and LangChain chain
        db = SQLDatabase(engine)
        llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key='AIzaSyCH_S-qA2wbGSE-db_Fj8w8059dpjDkEOs')
        chain = create_sql_query_chain(llm, db)

        # Save db and chain in session_state
        st.session_state.db = db
        st.session_state.chain = chain

        st.success("Successfully connected to the database!")

    except OperationalError as e:
        st.error(f"Failed to connect to the database: {str(e)}")

# Ensure that the connection has been established before allowing query execution
if st.session_state.db and st.session_state.chain:
    # Input field for natural language question
    question = st.text_input("Ask a question in natural language:")

    # Button to execute the query
    if st.button("Execute Query"):
        if question:
            # Function to execute query with conversation history
            def execute_query(question, chain, db):
                try:
                    # Prepare full conversation as input
                    conversation_input = "\n".join(st.session_state.conversation_history + [question])

                    # Generate the SQL query based on the full conversation
                    response = chain.invoke({"question": conversation_input})
                    
                    # Check if 'SQLQuery: ' exists in the response
                    if 'SQLQuery: ' in response:
                        # Extract the SQL query part from the response
                        cleaned_query = response.split('SQLQuery: ')[1].strip()

                        # Remove any LIMIT clause to ensure all data is fetched
                        cleaned_query = cleaned_query.replace('LIMIT 5', '')  # Removes any LIMIT clause

                        # Execute the cleaned query
                        result = db.run(cleaned_query)

                        # Update conversation history
                        st.session_state.conversation_history.append(f"Q: {question}")
                        st.session_state.conversation_history.append(f"SQLQuery: {cleaned_query}")
                        st.session_state.conversation_history.append(f"A: {result}")
                        return cleaned_query, result
                    else:
                        st.error("SQL query not found in the response. Please check the question.")
                        return None, None
                except ProgrammingError as e:
                    st.error(f"Database error: {str(e)}")
                    return None, None
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    return None, None

            # Execute the query
            cleaned_query, query_result = execute_query(question, st.session_state.chain, st.session_state.db)

            if cleaned_query and query_result is not None:
                # Display the generated SQL query
                st.write("Generated SQL Query:")
                st.code(cleaned_query, language="sql")

                # Display the query result
                st.write("Query Result:")
                st.write(query_result)
            else:
                st.write("No result returned or an error occurred.")
        else:
            st.error("Please enter a question.")

    # Display conversation history
    st.write("### Conversation History")
    for entry in st.session_state.conversation_history:
        st.write(entry)
else:
    st.warning("Please connect to the database first.")
