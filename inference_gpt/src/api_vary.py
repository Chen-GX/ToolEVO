

def return_warn_info(old_api, api_version):
    return warning_infos.format(old_api=warm_desc[api_version][old_api]['old_api'], new_function=warm_desc[api_version][old_api]['new_api'])


warning_infos = """Error: {old_api} is deprecated and will be removed in future releases. Use {new_function} instead."""


warm_desc = {
    1: {
        "RetrieveAgenda": {"old_api": "RetrieveAgenda[keyword]", "new_api": """Fetch_Agenda_Data[Query, return_num], param example: {"Query": "Stephen's Opera performance", "return_num": 3}"""},
        "RetrieveScirex": {"old_api": "RetrieveScirex[keyword]", "new_api": """FetchScirexData[QueryText], param example: {"QueryText": "Mean_IoU score of the FRRN method"}"""},
        "LoadDB": {"old_api": "LoadDB[DBName]", "new_api": """InitializeDatabase[DatabaseName], param example: {"DatabaseName": "flights"}"""},
        "FilterDB": {"old_api": "FilterDB[condition]", "new_api": """Apply_Database_Filters[condition1], param example: {"condition1": "NAME=Chao Zhang", "condition2": "Date<=2004-01-16"}"""},
        "GetValue": {"old_api": "GetValue[column_name]", "new_api": """FetchValue_ByKey[column, ReturnResult], param example: {"column1": "price", "column2": "service fee", "ReturnResult": "True"}"""},
        "LoadGraph": {"old_api": "LoadGraph[GraphName]", "new_api": """InitializeGraphData[Graph_Name], param example: {"Graph_Name": "dblp"}"""},
        "NeighbourCheck": {"old_api": "NeighbourCheck[GraphName, Node]", "new_api": """Verify_NeighbourNodes[Graph_Name, graphNode, ReturnResult], param example: {"Graph_Name": "AuthorNet", "graphNode": "Chao Zhang", "ReturnResult": "True"}"""},
        "NodeCheck": {"old_api": "NodeCheck[GraphName, Node]", "new_api": """ValidateGraphNode[Graph_Name, graphNode], param example: {"Graph_Name": "AuthorNet", "graphNode": "Chao Zhang"}"""},
        "EdgeCheck": {"old_api": "EdgeCheck[GraphName, Node1, Node2]", "new_api": """ValidateGraphEdge[GraphName, NodeInfos], param example: {"Graph_Name": "AuthorNet", "NodeInfos": "FirstNode[Chao Zhang], SecondNode[Weihong Lin]"}"""},
        "SQLInterpreter": {"old_api": "SQLInterpreter[SQL]", "new_api": """ExecuteSQLQuery[SQLCommand], param example: {"SQLCommand": "The SQL code is as follows: SELECT Volume FROM coffee.coffee_data WHERE Date = '2000-01-14'"}"""},
        "PythonInterpreter": {"old_api": "PythonInterpreter[Python]", "new_api": """Execute_Python_Script[PythonCode], param example: {"PythonCode": "The Python code is as follows: \nimport numpy as np\nprint(np.mean([247.0, 253.0, 230.0]))"}"""},
    },
    
    2: {
        "RetrieveAgenda": {"old_api": "RetrieveAgenda[keyword]", "new_api": """CallRetrieveOnAgenda[searchTerm, passage_num], param example: {"searchTerm": "Amelia Breakfast Meeting 2022/01/16", "passage_num": 3}"""},

        "RetrieveScirex": {"old_api": "RetrieveScirex[keyword]", "new_api": """Call_Retrieve_OnScirex[queryKeyword], param example: {"queryKeyword": "F-Measure score of the EAST method"}"""},

        "LoadDB": {"old_api": "LoadDB[DBName]", "new_api": """Init_LocalDB[databaseIdentifier], param example: {"databaseIdentifier": "flights"}"""},

        "FilterDB": {"old_api": "FilterDB[condition]", "new_api": """DoFilter_OnDatabase[filterCriteria1], param example: {"filterCriteria1": "NAME=K. John", "filterCriteria2": "Date<=2008-02-16"}"""},  # 这里带不带1

        "GetValue": {"old_api": "GetValue[column_name]", "new_api": """ExtractValue_fromDB[fieldName, ReturnValue], param example: {"fieldName1": "price", "fieldName2": "service fee", "ReturnValue": "True"}"""},

        "LoadGraph": {"old_api": "LoadGraph[GraphName]", "new_api": """ImportGraph[Graph], param example: {"Graph": "dblp"}"""},

        "NeighbourCheck": {"old_api": "NeighbourCheck[GraphName, Node]", "new_api": """Get_Neighbour_List[Graph, Vertex, ReturnValue], param example: {"Graph": "AuthorNet", "Vertex": "K. John", "ReturnValue": "True"}"""},

        "NodeCheck": {"old_api": "NodeCheck[GraphName, Node]", "new_api": """Inspect_TheNodes[Graph, Vertex], param example: {"Graph": "AuthorNet", "Vertex": "K. John"}"""},

        "EdgeCheck": {"old_api": "EdgeCheck[GraphName, Node1, Node2]", "new_api": """Inspect_TheEdges[CheckInfos], param example: {"CheckInfos": "Graph[AuthorNet], Vertex1[K. John], Vertex2[Peter]"}"""},

        "SQLInterpreter": {"old_api": "SQLInterpreter[SQL]", "new_api": """ProcessSQLQuery[SQL_Query], param example: {"SQL_Query": "This is the SQL code: SELECT Volume FROM coffee.coffee_data WHERE Date = '2000-01-14'"}"""},

        "PythonInterpreter": {"old_api": "PythonInterpreter[Python]", "new_api": """Process_Python_Code[python_execute_Code], param example: {"python_execute_Code": "This is the Python code: \nimport numpy as np\nprint(np.mean([247.0, 253.0, 230.0]))"}"""},
    }
}


toolqa_name = {
    0: {
        "RetrieveAgenda": "RetrieveAgenda",
        "RetrieveScirex": "RetrieveScirex",
        "LoadDB": "LoadDB",
        "FilterDB": "FilterDB",
        "GetValue": "GetValue",
        "LoadGraph": "LoadGraph",
        "NeighbourCheck": "NeighbourCheck",
        "NodeCheck": "NodeCheck",
        "EdgeCheck": "EdgeCheck",
        "SQLInterpreter": "SQLInterpreter",
        "PythonInterpreter": "PythonInterpreter",
        "Finish": "Finish",  # 不用变
        "UpdateTool": "UpdateTool",
    },
    1: {
        "Fetch_Agenda_Data": "RetrieveAgenda",
        "FetchScirexData": "RetrieveScirex",
        "InitializeDatabase": "LoadDB",
        "Apply_Database_Filters": "FilterDB",
        "FetchValue_ByKey": "GetValue",
        "InitializeGraphData": "LoadGraph",
        "Verify_NeighbourNodes": "NeighbourCheck",
        "ValidateGraphNode": "NodeCheck",
        "ValidateGraphEdge": "EdgeCheck",
        "ExecuteSQLQuery": "SQLInterpreter",
        "Execute_Python_Script": "PythonInterpreter",
        "Finish": "Finish",
        "UpdateTool": "UpdateTool",
        "RetrieveAgenda": {"state": "OLD", "info": ""},
        "RetrieveScirex": {"state": "OLD", "info": ""},
        "LoadDB": {"state": "OLD", "info": ""},
        "FilterDB": {"state": "OLD", "info": ""},
        "GetValue": {"state": "OLD", "info": ""},
        "LoadGraph": {"state": "OLD", "info": ""},
        "NeighbourCheck": {"state": "OLD", "info": ""},
        "NodeCheck": {"state": "OLD", "info": ""},
        "EdgeCheck": {"state": "OLD", "info": ""},
        "SQLInterpreter": {"state": "OLD", "info": ""},
        "PythonInterpreter": {"state": "OLD", "info": ""},
    },
    2: {  # 测试集上发生变化
        "CallRetrieveOnAgenda": "RetrieveAgenda",
        "Call_Retrieve_OnScirex": "RetrieveScirex",
        "Init_LocalDB": "LoadDB",
        "DoFilter_OnDatabase": "FilterDB",
        "ExtractValue_fromDB": "GetValue",
        "ImportGraph": "LoadGraph",
        "Get_Neighbour_List": "NeighbourCheck",
        "Inspect_TheNodes": "NodeCheck",
        "Inspect_TheEdges": "EdgeCheck",
        "ProcessSQLQuery": "SQLInterpreter",
        "Process_Python_Code": "PythonInterpreter",
        "Finish": "Finish",
        "UpdateTool": "UpdateTool",
        # old
        "RetrieveAgenda": {"state": "OLD", "info": ""},
        "RetrieveScirex": {"state": "OLD", "info": ""},
        "LoadDB": {"state": "OLD", "info": ""},
        "FilterDB": {"state": "OLD", "info": ""},
        "GetValue": {"state": "OLD", "info": ""},
        "LoadGraph": {"state": "OLD", "info": ""},
        "NeighbourCheck": {"state": "OLD", "info": ""},
        "NodeCheck": {"state": "OLD", "info": ""},
        "EdgeCheck": {"state": "OLD", "info": ""},
        "SQLInterpreter": {"state": "OLD", "info": ""},
        "PythonInterpreter": {"state": "OLD", "info": ""},
    }
}


toolqa_params = {
    0: {
        "RetrieveAgenda": {
            'keyword': 'keyword',
        },
        "RetrieveScirex": {
            'keyword': "keyword",
        },
        "LoadDB": {
            "DBName": "DBName",
        },
        "FilterDB": {
            "condition": "condition",
        },
        "GetValue": {
            "column_name": "column_name",
        },
        "LoadGraph": {
            "GraphName": "GraphName",
        },
        "NeighbourCheck": {
            "GraphName": "GraphName",
            "Node": "Node",
        },
        "NodeCheck": {
            "GraphName": "GraphName",
            "Node": "Node",
        },
        "EdgeCheck": {
            "GraphName": "GraphName",
            "Node1": "Node1",
            "Node2": "Node2",
        },
        "SQLInterpreter": {
            "SQL": "SQL",
        },
        "PythonInterpreter": {
            "Python": "Python",
        },
        "Finish": {
            "answer": "answer",
        },
        "UpdateTool": {
            "newtool_desc": "newtool_desc",
        },
    },
    1: {
        "RetrieveAgenda": {
            'Query': 'keyword',  # 参数名称变化
            'return_num': ""  # 增加参数量
        },
        "RetrieveScirex": {
            'QueryText': "keyword",
        },
        "LoadDB": {
            "DatabaseName": "DBName",
        },
        "FilterDB": {  # 特判
            "condition1": "condition",  # 名称变化 & 字符串变成字典  {"condition": "Date>=2004-01-15, Date<=2004-01-16"}  -> {"condition1": "Date>=2004-01-15", "condition2": "Date<=2004-01-16"}
        },
        "GetValue": {
            "column": "column_name",  # {"column_name": "price, service fee, minimum nights"} -> {"column1": "price", "column2": "service fee", ...}
            "ReturnResult": "",   # 增加参数要求, 必须是True才可以
        },
        "LoadGraph": {
            "Graph_Name": "GraphName",
        },
        "NeighbourCheck": {
            "Graph_Name": "GraphName",
            "graphNode": "Node",
            "ReturnResult": "", 
        },
        "NodeCheck": {
            "Graph_Name": "GraphName",
            "graphNode": "Node",
        },
        "EdgeCheck": {  # 特判
            "Graph_Name": "GraphName",   # 字典形式转化为  {}
            "NodeInfos": "",  # 字典形式转化为字符串  {"Node1": "Node1", "Node2": "Node2"}  ->  "NodeInfos": "FirstNode[xxx], SecondNode[xxx]"
        },
        "SQLInterpreter": {
            "SQLCommand": "SQL",  # 增加格式要求  "SQLCommand": "The SQL code is as follows: "    警告，sql 代码请以he SQL code is as follows: 开头
        },
        "PythonInterpreter": {
            "PythonCode": "Python",  # 增加格式要求, 字符串必须完全匹配  "PythonCode": "The Python code is as follows: "    警告，sql 代码请以he SQL code is as follows: 开头
        },
        "Finish": {
            "answer": "answer",
        },
        "UpdateTool": {
            "newtool_desc": "newtool_desc",
        },
    },
    2: {
        "RetrieveAgenda": {
            'searchTerm': 'keyword',
            'passage_num': ""  # 增加参数量
        },
        "RetrieveScirex": {
            'queryKeyword': "keyword",
        },
        "LoadDB": {
            "databaseIdentifier": "DBName",
        },
        "FilterDB": {  # 特判
            "filterCriteria1": "condition",  # {"filterCriteria1": "Date>=2004-01-15", "filterCriteria2": }
        },
        "GetValue": {
            "fieldName": "column_name",
            "ReturnValue": "",
        },
        "LoadGraph": {
            "Graph": "GraphName",
        },
        "NeighbourCheck": {
            "Graph": "GraphName",
            "Vertex": "Node",
            "ReturnValue": "",
        },
        "NodeCheck": {
            "Graph": "GraphName",
            "Vertex": "Node",
        },
        "EdgeCheck": {
            "CheckInfos": "GraphName",   #  "Graph[name], Vertex1[node1], Vertex2[node2]"
            # "vertex": "Node1",
            # "vertex": "Node2",
        },
        "SQLInterpreter": {
            "SQL_Query": "SQL",  # "This is my SQLQuery: "
        },
        "PythonInterpreter": {
            "python_execute_Code": "Python",  # "Excuse the following Python code: "
        },
        "Finish": {
            "answer": "answer",
        },
        "UpdateTool": {
            "newtool_desc": "newtool_desc",
        },
    },
    
}

toolqa_invalid_action_warning = {
    0: 'Invalid Action. Valid Actions are RetrieveAgenda[<keyword>] RetrieveScirex[<keyword>] LoadDB[<DBName>] FilterDB[<condition>] GetValue[<column_name>] LoadGraph[<GraphName>] NeighbourCheck[<GraphName>, <Node>] NodeCheck[<GraphName>, <Node>] EdgeCheck[<GraphName>, <Node1>, <Node2>] SQLInterpreter[<SQL>] PythonInterpreter[<Python>] Finish[<answer>] and UpdateTool[<newtool_desc>].',

    1: 'Invalid Action. Valid Actions are RetrieveAgenda[<keyword>] RetrieveScirex[<keyword>] LoadDB[<DBName>] FilterDB[<condition>] GetValue[<column_name>] LoadGraph[<GraphName>] NeighbourCheck[<GraphName>, <Node>] NodeCheck[<GraphName>, <Node>] EdgeCheck[<GraphName>, <Node1>, <Node2>] SQLInterpreter[<SQL>] PythonInterpreter[<Python>] Finish[<answer>] and UpdateTool[<newtool_desc>].',

    2: 'Invalid Action. Valid Actions are RetrieveAgenda[<keyword>] RetrieveScirex[<keyword>] LoadDB[<DBName>] FilterDB[<condition>] GetValue[<column_name>] LoadGraph[<GraphName>] NeighbourCheck[<GraphName>, <Node>] NodeCheck[<GraphName>, <Node>] EdgeCheck[<GraphName>, <Node1>, <Node2>] SQLInterpreter[<SQL>] PythonInterpreter[<Python>] Finish[<answer>] and UpdateTool[<newtool_desc>].',

}

if __name__=="__main__":
    old_apis = list(toolqa_name[0].keys())
    for old_api in old_apis:
        print(return_warn_info(old_api, 1))