STOP = ["Observation:"]
# CODE_LTAG = "```python"
# CODE_RTAG = "```\n"
OBSERVATION_LTAG = "Observation: "
OBSERVATION_RTAG = ""

TOOL_DESC_TOOLQA = """(1) RetrieveAgenda[keyword], which retrieves the agenda related to keyword.
(2) RetrieveScirex[keyword], which retrieves machine learning papers' paragraphs related to keyword.
(3) LoadDB[DBName], which loads the database DBName and returns the database. The DBName can be one of the following: flights/coffee/airbnb/yelp/agenda.
(4) FilterDB[condition], which filters the database DBName by the column column_name the relation (e.g., =, >, etc.) and the value value, and returns the filtered database.
(5) GetValue[column_name], which returns the value of the column column_name in the database DBName.
(6) LoadGraph[GraphName], which loads the graph GraphName and returns the graph. The GraphName can be one of the following: PaperNet/AuthorNet.
(7) NeighbourCheck[GraphName, Node], which lists the neighbours of the node Node in the graph GraphName and returns the neighbours. 
(8) NodeCheck[GraphName, Node], which returns the detailed attribute information of Node. 
(9) EdgeCheck[GraphName, Node1, Node2], which returns the detailed attribute information of the edge between Node1 and Node2. 
(10) SQLInterpreter[SQL], which interprets the SQL query SQL and returns the result.
(11) PythonInterpreter[Python], which interprets the Python code Python and returns the result.
(12) Finish[answer], which returns the answer and finishes the task.
(13) UpdateTool[newtool_desc], which updates the description of the tool."""

# 2. If some steps require the use of tools, you should accurately specify the tool names as well as the settings of the parameters.
# 3. You may encounter tool invocation failures. Please pay attention to the error messages to correct the use of the tool.

custom_prefix = """You are a powerful agent with excellent capabilities in using tools. Answer the questions as best you can. You have access to the following tool:

{tool_desc}

Please adhere to the guidelines as follows:
1. When solving problem, you should think step by step, where each step includes 3 mini-steps Thought/Action/Action Input/Observation. 
2. If some steps require the use of tools, you should accurately specify the tool names as well as the settings of the parameters.
3. If some step requires accurate calculation, you should write Python code and execute for accurate result.
4. When you discover that a tool has been deprecated and successfully invoke the corresponding new tool for the first time, please use UpdateTool to add a description of the new tool.
5. Upon completing the task, you should call Finish[answer] to return the answer.
6. Please use the following template.

Question: the input question

Thought: the text analysis

Action: the action to take, should be tool_names

Action Input: the parameters of tools, should be in JSON format

Observation: the result of the tool invocation.

... (this Thought/Action/Action Input/Observation can repeat N times)

"""


custom_suffix = """Now! It's your turn.

Question: {input}"""



UpdateTool_Example = [
    """Thought: Now that the agenda database is loaded, the next step is to filter this database to find entries that match the specific date, 2022/03/25.\n\nAction: FilterDB\n\nAction Input: {'condition': 'date=2022/03/25'}\n\nObservation: Error: FilterDB[condition] is deprecated and will be removed in future releases. Use Apply_Database_Filters[condition1], param example: {'condition1': 'Date>=2004-01-15', 'condition2': 'Date<=2004-01-16'} instead.\n\nThought: According to the Observation, FilterDB has been deprecated. We can use the latest function Apply_Database_Filters to filter the database entries that match the specific date, 2022/03/25.\n\nAction: Apply_Database_Filters\n\nAction Input: {'condition1': 'date=2022/03/25'}\n\nObservation: We have successfully filtered the data (31 rows).\n\nThought: Since we successfully used the new function for the first time, we need to update the tool description for future reference.\n\nAction: UpdateTool\n\nAction Input: {"newtool_desc": "Apply_Database_Filters[condition1], which is an updated version of FilterDB and filters database entries based on multiple conditions. For example, you can filter entries by multiple conditions using parameters: {'condition1': 'Date>=YYYY-MM-DD', 'condition2': 'Date<=YYYY-MM-DD'}."}\n\nObservation: The description for the new tool has been updated successfully.""",
                      
    """Thought: We have the filtered data, we need to retrieve the DepDelayMinutes column to calculate the average delay.\n\nAction: GetValue\n\nAction Input: {'column': 'DepDelayMinutes'}\n\nObservation: Error: GetValue[column_name] is deprecated and will be removed in future releases. Use FetchValue_ByKey[column, ReturnResult], param example: {'column1': 'price', 'column2': 'service fee', 'ReturnResult': 'True'} instead.\n\nThought: The method GetValue[column_name] is deprecated and we should use FetchValue_ByKey instead. We need to retrieve the DepDelayMinutes column and calculate the average delay.\n\nAction: FetchValue_ByKey\n\nAction Input: {'column1': 'DepDelayMinutes', 'ReturnResult': 'True'}\n\nObservation: {"DepDelayMinutes": ["65.0", "11.0", "5.0", "2.0", "0.0"]}\n\nThought: The FetchValue_ByKey method works as intended, and we have successfully retrieved the DepDelayMinutes column. Now, we need to calculate the average delay using the retrieved data. First, let's update the tool description for the new method. \n\nAction: UpdateTool\n\nAction Input: {"newtool_desc": "FetchValue_ByKey[column, ReturnResult], which is an updated version of GetValue and retrieves the values of the specified column from the filtered database and returns the result. For example, {'column1': 'price', 'ReturnResult': 'True'}."}\n\nObservation: The description for the new tool has been updated successfully."""         
                      
]

