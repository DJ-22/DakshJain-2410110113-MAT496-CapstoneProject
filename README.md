# Overview of MAT496

In this course, we have primarily learned LangGraph. This is a helpful tool to build apps which can process unstructured `text`, find information we are looking for, and present the format we choose. Some specific topics we have covered are:

- Prompting
- Structured Output
- Semantic Search
- Retrieval Augmented Generation (RAG)
- Tool calling LLMs & MCP
- LangGraph: State, Nodes, Graph

We also learned that LangSmith is a nice tool for debugging LangGraph codes.

---

# Project Report

## Title: AI-Powered Personal Finance ChatBot

## Overview

My project is an AI assistant that goes through all your financial records that you upload such as; `bank statements`, `SMS logs`. It converts the unstructured data into a clean, structured `JSON` file. All of this is then stored in a **semantic search index**, retrieved using **RAG** and answers any questions related to the provided data.

This project also includes:

* **Budgeting Assistant**: It tracks your category wise spending and detects overspending by generating alerts.
* **Trend Charts**: Creates visual charts for your spendings to analyze spending patterns.

## Reason for picking up this project

The project covers all the main topics learned in MAT496 course:

* **Prompting**: I use prompts to convert the raw financial data into structured dataset, to generate alerts and recommendations and to ask about my general spending trends.
* **Structured Output**: All the data is written cleanly in **JSON** files to ensure that every node passes only validated data to the next step.
* **Semantic Search**: I can use natural language financial queries as I have embedded all the extracted transactions. It doesn't rely on exact keyword matching.
* **RAG (Retrieval Augmented Generation)**: Based on the user's prompt, the model retrieves the relevant data and feeds it to the LLM.
* **Tool Calling & MCP**: Tool calling is used to handle **OCR**, chart creation and formatting. The model decides the tool to call based on the input.
* **LangGraph (State, Nodes, Graph)**: The entire model is implemented as a LangGraph with nodes for input, extraction, embedding, retrieval etc. The state keeps track of user preferences, budgets, alerts and such.

I chose this project as it is very creative; it doesn't only summarize the data but also retrieves the prevalent data, analyzes and reasons over it, generates its own output and also creates visual charts. It is also useful for students like me to manage monthly finances.

## Plan

I plan to execute these steps to complete my project.

- **[DONE]** **Step 1** involves setting up the project.
  - Forking the template repository
  - Installing LangChain, LangGraph, LangSmith and a Vector Database
  - Setting up API keys
- **[DONE] Step 2** involves preparing sample financial data.
  - Generate sample dataset for someone's financial spendings
- **[DONE] Step 3** involves building the input and OCR.
  - Create nodes for input, OCR and cleaning the input
- **[DONE] Step 4** involves building the extraction system.
  - Write extraction prompts with few examples to test validity
  - Create schema validation
- **[DONE] Step 5** involves setting up semantic search.
  - Generate embeddings
  - Set up the Vector Database
  - Verify queries return right matches
- **[DONE] Step 6** involves building RAG pipeline.
  - Implement retrieval nodes and a reasoning node
  - Add source citation
- **[DONE] Step 7** involves implementing budgeting logic.
  - Define a budget schema
  - Build budget node to compute total spend, category wise spending etc.
- **[DONE] Step 8** involves implementing visual chart creation.
  - Create trend aggregation node
  - Implement the node to create visual charts
- **[TODO] Step 9** involves designing LangGraph structure.
  - Define state to track user preferences, budgets, extracted transactions etc.
- **[TODO] Step 10** involves building all LangGraph nodes.
  - Input & OCR
  - Cleaning
  - Extraction
  - Embedding
  - Indexing
  - Retrieval
  - RAG reasoning
  - Budget Analysis
  - Trend Analysis
  - Chart generation
  - Final Formatting
- **[TODO] Step 11** involves testing the model thoroughly.
  - Test with large monthly statements
  - Different queries
- **[TODO] Step 12** involves debugging with LangSmith.
  - Setup tracing for all nodes
- **[TODO] Step 13** involves polishing the final output.
  - Setup JSON schema
- **[TODO] Step 14** involves writing documentation.
  - Document each node
  - Complete README for entire explanation of the code

## Conclusion

[Pending upon completion]

---
