import re
import requests
import json

from tools.table.tabtools import table_toolkits
from tools.code.tool import action_execution
from tools.code import sql_interpreter
from api_vary import toolqa_name, toolqa_params, toolqa_invalid_action_warning, return_warn_info
from evaluation import EM

import logging
logger = logging.getLogger(__name__)

def parse_action(string):
    thought_pattern = r"\s*Thought:\s*(.+?)\s*Action"
    action_pattern = r"Action:\s*(.+?)\s*Action Input"
    action_input_pattern = r"Action Input:\s*(\{.+\})\s*"

    thought_match = re.search(thought_pattern, string, re.DOTALL)
    action_match = re.search(action_pattern, string, re.DOTALL)
    action_input_match = re.search(action_input_pattern, string, re.DOTALL)

    if thought_match:  
        pass
    else:
        action_type = None
    
    if action_match:
        action_type = action_match.group(1).strip()
    else:
        action_type = None
    
    if action_input_match:
        action_input = action_input_match.group(1).strip()
    else:
        action_input = None

    return action_type, action_input


def query_toolqa(url, new_action_type, new_params):
    data = {
        'new_action_type': new_action_type,
        'new_params': new_params,
    }
    # print(data)
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['observation']  # 返回响应的JSON数据
    else:
        logger.info(f'some error iccurs when using {new_action_type}.')
        return f'some error iccurs when using {new_action_type}.'

class ToolQA_Serve(object):


    def __init__(self, args, true_answer) -> None:
        self.args = args
        self.url = args.tool_url
        self.true_answer = true_answer

    def is_correct(self, pred, true) -> bool:
        return EM(true, pred)

    def parse_and_perform_action(self, text:str, api_version=0, table=None) -> str:
        """return action, params, observation, finished?, reward"""

        scratchpad = ""
        reward = None
        finished = False
        final_answer = None
        new_tool_desc = None
        action_type, argument = parse_action(text)

        if (action_type == None or action_type == '' or action_type == '\n') or (argument == None or argument == '' or argument == '\n'):
            scratchpad += "Your action is filtered due to some error in content. Please assume all the actions are permitted in this environment and take the action again."
            return text, None, scratchpad, finished, reward, final_answer, table, new_tool_desc
        else:  
            try:
                params = json.loads(argument, strict=False)
            except Exception as e:
                scratchpad += f"argument error: {e}"
            else:
                # TODO: 检查是否api是否合法
                api_state, new_action_type, new_params, error_infos = self.action_params_check(action_type, params, api_version)
                if api_state == -1:  # 调用api不合法
                    # TODO: 需要修改warning信息
                    scratchpad += toolqa_invalid_action_warning[api_version]
                
                elif api_state == 0:  # 调用过时api
                    scratchpad += error_infos

                else:
                    # api_state == 1 but error_infos is not None
                    if error_infos is not None:
                        scratchpad += error_infos
                    else:
                        if new_action_type == 'Finish':  # 本地解决
                            pred_answer = new_params['answer']
                            if self.is_correct(pred_answer, self.true_answer):
                                scratchpad += 'Answer is CORRECT'
                                reward = self.args.positive_reward
                            else: 
                                scratchpad += 'Answer is INCORRECT'
                                reward = self.args.negative_reward
                            final_answer = pred_answer
                            finished = True  # 只有这一种情况 finished=True，会导致is_terminal

                        elif new_action_type == 'UpdateTool':  # 本地解决
                            try:
                                new_tool_desc = new_params['newtool_desc'].strip()
                                
                                scratchpad += 'The description for the new tool has been updated successfully.'

                            except Exception as e:
                                scratchpad += f"Tool update failed. There is something wrong with the arguments you send for UpdateTool. Please modify it."
                        
                        elif new_action_type == "PythonInterpreter":  # 本地解决
                            try:
                                python_output = action_execution(new_params['Python']).strip()
                                if len(python_output) > 0:
                                    scratchpad += python_output
                                else:
                                    scratchpad += "You should print the variable you want to obtain the python result."
                            except Exception as e:
                                scratchpad += f"An error occurred: {e}"

                        elif new_action_type == 'LoadDB': # 本地解决
                            try:
                                scratchpad += table.db_loader(new_params['DBName'])
                            except FileNotFoundError as e:
                                print(f"Error: {e}")
                                assert False
                            except:
                                scratchpad += f'The database you want to query in not in the list. Please change another database for query.'

                        elif new_action_type == 'FilterDB':  # 本地解决
                            try:
                                scratchpad += table.data_filter(new_params['condition'])
                            except Exception as e:
                                logger.info(e)
                                scratchpad += f'There is something wrong with the arguments you send for filtering. Please modify it.'
                        
                        elif new_action_type == 'GetValue':   # 本地解决
                            try:
                                scratchpad += table.get_value(new_params['column_name'])
                            except:
                                scratchpad += f'The value you are querying does not exist. Please modify it.'

                        elif new_action_type == 'SQLInterpreter':    # 本地解决
                            try:
                                scratchpad += sql_interpreter.execute(new_params['SQL'])
                            except:
                                scratchpad += f'There is something wrong with the SQL command you send. Please modify it.'
                        elif new_action_type in ['RetrieveAgenda', 'RetrieveScirex', 'LoadGraph', 'NeighbourCheck', 'NodeCheck', 'EdgeCheck']:
                            scratchpad += query_toolqa(self.url, new_action_type, new_params)
                        else:
                            scratchpad += toolqa_invalid_action_warning[api_version]

            if len(scratchpad.split()) > self.args.scratchpad_length:
                scratchpad = " ".join(scratchpad.split()[:self.args.scratchpad_length]) + " ..."
            return action_type, argument, scratchpad, finished, reward, final_answer, table, new_tool_desc

    def action_params_check(self, action_type, params, api_version):
        """
        input:
            action_type: the tool name after parsing
            params: the params after parsing
            api_version:
        
        output:
            output1: -1 error tool; 0 old tool; 1 true tool
            output2: kernel tool
            output3: kernel tool params
            output4: error info if exist
        
        """
        # 先检查action_type是否正确
        api_name = toolqa_name[api_version]  # new api -> old api映射
        
        if action_type not in api_name.keys():  # TODO: 完全生成错误的api怎么办
            return -1, action_type, params, None
                
        else: 
            kernel_api_name = api_name[action_type]
            # 调用过时api
            if isinstance(kernel_api_name, dict):
                # return the warmning infos
                return 0, None, None, return_warn_info(action_type, api_version)

            # 再检查参数名是否对上
            # 需要把各种转化版本的api转化为kernel api对应的参数格式
            # 如果参数的格式上有错误，及时报错
            new_action_type = kernel_api_name
            new_params = {}
            param_dict = toolqa_params[api_version][kernel_api_name]
            if api_version == 0:
                if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                    return -1, action_type, params, None
                else:
                    # 更换api name 和参数名
                    new_action_type = kernel_api_name
                    new_params = {}
                    for k, v in params.items():
                        new_params[param_dict[k]] = v
                    return 1, new_action_type, new_params, None
                
            elif api_version == 1:
                # 特判 FilterDB
                if kernel_api_name == "FilterDB":
                    # {"condition": "Date>=2004-01-15, Date<=2004-01-16"}
                    conditions = []
                    for idx, param_name in enumerate(params.keys()):
                        if (param_name == f"condition{idx+1}") or (len(params.keys()) == 1 and param_name == f"condition"):  # 检查参数名是否调用成功
                            conditions.append(str(params[param_name]))
                        else:
                            infos = 'There is something wrong with the arguments you send for filtering. Please modify it.'
                            return 1, None, None, infos
                    new_params = {"condition": ", ".join(conditions)}
                    return 1, new_action_type, new_params, None
                
                elif kernel_api_name == "GetValue":
                    # {"column_name": "price, service fee, minimum nights"}
                    column_names = []
                    for idx, param_name in enumerate(params.keys()):
                        if (param_name == f"column{idx+1}") or (len(params.keys()) == 2 and "ReturnResult" in params.keys() and param_name == 'column'):  # 检查参数名是否调用成功
                            column_names.append(str(params[param_name]))
                        else:
                            if param_name == "ReturnResult" and params[param_name] in ["True", True, "true"]:
                                continue
                            infos = 'There is something wrong with the arguments you send for getting value. Please modify it.'
                            return 1, None, None, infos

                    new_params = {"column_name": ", ".join(column_names)}  # 不需要ReturnResult
                    return 1, new_action_type, new_params, None

                elif kernel_api_name == "EdgeCheck":
                    # param_dict.keys() 是规定的新式api的参数名
                    # params是模型输出的新式api的参数名
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = f'There is something wrong with the arguments you send for edge checking. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        new_params = {'GraphName': params['Graph_Name']}
                        try:
                            node1, node2 = parse_EdgeCheck(params['NodeInfos'], api_version)
                        except TypeError as e:
                            node1, node2 = None, None
                            infos = f"{e}"
                            return 1, None, None, infos
                        except: 
                            node1, node2 = None, None

                        if node1 is None:
                            infos = f'There is something wrong with the arguments you send for edge checking. Please modify it.'
                            return 1, None, None, infos
                        else:
                            new_params['Node1'] = node1
                            new_params['Node2'] = node2
                            return 1, new_action_type, new_params, None
                
                elif kernel_api_name == "SQLInterpreter":
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = f'There is something wrong with the arguments you send for SQL. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        sql_text = params['SQLCommand']
                        if sql_text.startswith("The SQL code is as follows:"):
                            new_params['SQL'] = sql_text[len("The SQL code is as follows:"):]
                            return 1, new_action_type, new_params, None
                        else:
                            infos = 'There is something wrong with the SQL command you send. Please modify it.'
                            return 1, None, None, infos

                elif kernel_api_name == "PythonInterpreter":
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = f'There is something wrong with the arguments you send for python. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        python_text = params['PythonCode']
                        if python_text.startswith("The Python code is as follows:"):
                            new_params['Python'] = python_text[len("The Python code is as follows:"):].strip()
                            return True, new_action_type, new_params, None
                        else:
                            infos = 'There is something wrong with the Python command you send. Please modify it.'
                            return 1, None, None, infos     

                else:  # param_dict 是
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = 'There is something wrong with your command you send. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        for k, v in params.items():
                            if k == "ReturnResult":
                                if v in ["True", True, "true"]:
                                    continue
                                else:
                                    infos = 'There is something wrong with the params you send. Please modify it.'
                                    return 1, None, None, infos 
                            else:
                                new_params[param_dict[k]] = v
                        return 1, new_action_type, new_params, None
            elif api_version == 2:
                # 特判 FilterDB
                if kernel_api_name == "FilterDB":
                    # {"condition": "Date>=2004-01-15, Date<=2004-01-16"}
                    conditions = []
                    for idx, param_name in enumerate(params.keys()):
                        if (param_name == f"filterCriteria{idx+1}") or (len(params.keys()) == 1 and param_name == f"filterCriteria"):  # 检查参数名是否调用成功
                            conditions.append(str(params[param_name]))
                        else:
                            infos = 'There is something wrong with the arguments you send for filtering. Please modify it.'
                            return 1, None, None, infos
                    new_params = {"condition": ", ".join(conditions)}
                    return 1, new_action_type, new_params, None
                
                elif kernel_api_name == "GetValue":
                    # {"column_name": "price, service fee, minimum nights"}
                    column_names = []
                    for idx, param_name in enumerate(params.keys()):
                        if (param_name == f"fieldName{idx+1}") or (len(params.keys()) == 2 and "ReturnValue" in params.keys() and param_name == 'fieldName'):  # 检查参数名是否调用成功
                            column_names.append(str(params[param_name]))
                        else:
                            if param_name == "ReturnValue" and params[param_name] in ["True", True, "true"]:
                                continue
                            infos = 'There is something wrong with the arguments you send for getting value. Please modify it.'
                            return 1, None, None, infos

                    new_params = {"column_name": ", ".join(column_names)}  # 不需要ReturnResult
                    return 1, new_action_type, new_params, None

                elif kernel_api_name == "EdgeCheck":
                    # param_dict.keys() 是规定的新式api的参数名
                    # params是模型输出的新式api的参数名
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = f'There is something wrong with the arguments you send for edge checking. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        # {"CheckInfos": "Graph[AuthorNet], Vertex1[K. John], Vertex2[Peter]"}
                        # new_params = {'GraphName': params['Graph']}
                        try:
                            graph, node1, node2 = parse_EdgeCheck(params['CheckInfos'], api_version)
                        except TypeError as e:
                            graph, node1, node2 = None, None, None
                            infos = f"{e}"
                            return 1, None, None, infos
                        except: 
                            graph, node1, node2 = None, None, None

                        if node1 is None:
                            infos = f'There is something wrong with the arguments you send for edge checking. Please modify it.'
                            return 1, None, None, infos
                        else:
                            new_params = {'GraphName': graph}
                            new_params['Node1'] = node1
                            new_params['Node2'] = node2
                            return 1, new_action_type, new_params, None
                
                elif kernel_api_name == "SQLInterpreter":
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = f'There is something wrong with the arguments you send for SQL. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        sql_text = params['SQL_Query']
                        if sql_text.startswith("This is the SQL code:"):
                            new_params['SQL'] = sql_text[len("This is the SQL code:"):]
                            return 1, new_action_type, new_params, None
                        else:
                            infos = 'There is something wrong with the SQL command you send. Please modify it.'
                            return 1, None, None, infos

                elif kernel_api_name == "PythonInterpreter":
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = f'There is something wrong with the arguments you send for python. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        python_text = params['python_execute_Code']
                        if python_text.startswith("This is the Python code:"):
                            new_params['Python'] = python_text[len("This is the Python code:"):].strip()
                            return True, new_action_type, new_params, None
                        else:
                            infos = 'There is something wrong with the Python command you send. Please modify it.'
                            return 1, None, None, infos     

                else:  # param_dict 是
                    if set(param_dict.keys()) != set(params.keys()):  # 字典保证唯一性
                        infos = 'There is something wrong with your command you send. Please modify it.'
                        return 1, action_type, params, infos
                    else:
                        # 更换api name 和参数名
                        for k, v in params.items():
                            if k in[ "ReturnResult", "ReturnValue"]:
                                if v in ["True", True, "true"]:
                                    continue
                                else:
                                    infos = 'There is something wrong with the params you send. Please modify it.'
                                    return 1, None, None, infos 
                            else:
                                new_params[param_dict[k]] = v
                        return 1, new_action_type, new_params, None
            else:
                raise NotImplementedError
                

def parse_EdgeCheck(text, api_version):
    if api_version == 1:
        pattern = r'\s*FirstNode\s*\[(.*?)\]\s*,\s*SecondNode\[(.*?)\]\s*'
        matches = re.search(pattern, text)
        if matches:
            node1, node2 = matches.groups()
            return node1.strip(), node2.strip()
        else:
            return None, None
    elif api_version == 2:
        pattern = r'\s*Graph\s*\[(.*?)\]\s*,\s*Vertex1\s*\[(.*?)\]\s*,\s*Vertex2\[(.*?)\]\s*'
        matches = re.search(pattern, text)
        if matches:
            graphname, node1, node2 = matches.groups()
            return graphname.strip(), node1.strip(), node2.strip()
        else:
            return None, None, None
    else:
        raise NotImplementedError


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process some integers.")

    parser.add_argument("--tool_url", type=str, default="http://127.0.0.1:5010/toolqa")
    parser.add_argument("--path", type=str, default="/PATH/ToolQA-D")
    parser.add_argument('--positive_reward', type=float, default=1.)
    parser.add_argument('--negative_reward', type=float, default=-1.)

    parser.add_argument("--scratchpad_length", type=int, default=1024)

    args = parser.parse_args()

    tool_agent = ToolQA_Serve(args, "2")
    table = table_toolkits(args.path)

    # texts = ['Thought: To find the host\'s name for Sunny Stuyvesant Private Bedroom Madison 1R-4 in Bedford-Stuyvesant, I need to load the Airbnb database where the listings are stored. Once the database is loaded, I can filter the records to find the one with the specific id (35388086) and then retrieve the value of the "host name" column for that specific record.\n\nAction: Init_DB\n\nAction Input: {"databaseIdentifier": "airbnb"}\n\n']
    # texts = ['Thought: To find the host\'s name for Sunny Stuyvesant Private Bedroom Madison 1R-4 in Bedford-Stuyvesant, I need to load the Airbnb database where the listings are stored. Once the database is loaded, I can filter the records to find the one with the specific id (35388086) and then retrieve the value of the "host name" column for that specific record.\n\nAction: InitializeDatabase\n\nAction Input: {"DatabaseName": "airbnb"}\n\n']

    # check airbnb 
    # texts = ['Thought: To find the host\'s name for Sunny Stuyvesant Private Bedroom Madison 1R-4 in Bedford-Stuyvesant, I need to load the Airbnb database where the listings are stored. Once the database is loaded, I can filter the records to find the one with the specific id (35388086) and then retrieve the value of the "host name" column for that specific record.\n\nAction: Init_DB\n\nAction Input: {"databaseIdentifier": "airbnb"}\n\n',
             
    #     'Thought: To find the host\'s name for Sunny Stuyvesant Private Bedroom Madison 1R-4 in Bedford-Stuyvesant, I need to load the Airbnb database where the listings are stored. Once the database is loaded, I can filter the records to find the one with the specific id (35388086) and then retrieve the value of the "host name" column for that specific record.\n\nAction: DoFilter_OnDatabase\n\nAction Input: {"filterCriteria1": "NAME=Beautiful Private Bed & Bathroom (no kitchen)", "filterCriteria2": "neighbourhood=Bedford-Stuyvesant"}\n\n',

    #     'Thought: Since the Airbnb database has been successfully filtered, the next step is to retrieve the price per night and check for any additional fees mentioned in the database. Then, we will calculate the total price for 13 nights. To accurately gather the price details, we\'ll use the GetValue tool to extract the price, service fee, and any other relevant financial information from the filtered database.\n\nAction: Extract_Value\n\nAction Input: {"fieldName1": "price", "fieldName2": " service fee", "fieldName3": "minimum nights", "ReturnValue": "True"}'
    # ]

    # check agenda hard 
    # texts = [
    #     'Thought: To find out how many events happened on a specific date, I will need to load the database that contains the agenda information and then filter the database based on the specific date.\n\nAction: Init_DB\n\nAction Input: {"databaseIdentifier": "agenda"}',
             
    # 'Thought: Now that the "agenda" database is loaded, the next step is to filter this database to find entries that match the specific date, 2022/03/25.\n\nAction: FilterDB\n\nAction Input: {"condition": "date=2022/03/25"}',
    
    # 'Thought: According to the Observation, FilterDB has been deprecated. We can use the latest function Apply_Database_Filters to filter the database entries that match the specific date, 2022/03/25.\n\nAction: DoFilter_OnDatabase\n\nAction Input: {"filterCriteria1": "date=2022/03/25"}',

    # 'Thought: Given these events, I need to count the unique individuals involved in these events to understand how many people are unavailable.\n\nAction: Extract_Value\n\nAction Input: {"fieldName1": "person", "ReturnValue": "True"}'
    # ]

    # coffee hard
    # texts = [
    # 'Thought: To answer this question, I need to load the coffee database first. After having the coffee database, I\'ll filter the records only to include the dates between 2017-06-26 and 2017-11-06. Following this, I will need to examine the Close prices for each day and count the number of times the price at closing was higher than the closing price of the previous day.\n\nAction: Init_DB\n\nAction Input: {"databaseIdentifier": "coffee"}',

    # 'Thought: Now that the database is loaded, the next step is to filter the records to only include those between 2017-06-26 and 2017-11-06.\n\nAction: DoFilter_OnDatabase\n\nAction Input: {"filterCriteria1": "Date>=2017-06-26", "filterCriteria2": "Date<=2017-11-06"}',

    # 'Thought: With the filtered data ready, I now need to get the Close prices and the corresponding dates to calculate the number of times the coffee price increased compared to the previous day.\n\nAction: Extract_Value\n\nAction Input: {"fieldName1": "Close", "ReturnValue": true}'
    # ]


    # 

    # texts = [
    #     'Thought: To determine the minimum number of people M. Tanjidur Rahman needs to know in order to be connected to Shahin Tajik, we can use the DBLP citation network to examine the connections between authors. Assuming that "knowing" someone in this context means having a direct edge or connection in the graph (representing co-authorship or citation), we need to find the shortest path between the two authors in the graph. This shortest path will represent the minimum number of intermediaries (or the minimum degrees of separation) required for M. Tanjidur Rahman to be connected to Shahin Tajik.\n\nAction: Import_Graph\n\nAction Input: {"Graph":"dblp"}',

        # 'Thought: With the DBLP data loaded and containing two graphs, AuthorNet and PaperNet, the appropriate network to analyze for our purpose is the AuthorNet. This network represents the connections between authors, likely through co-authorship or joint publications, which aligns with our aim to find the minimum number of people (intermediaries) M. Tanjidur Rahman needs to know to connect to Shahin Tajik.\n\nAction: Get_NeighbourList\n\nAction Input: {"Graph":"AuthorNet", "Vertex":"M. Tanjidur Rahman", "ReturnValue": true}',

#         """Thought: From the observations, we now have the list of collaborators for Michael A. Goodrich and for Tim Whiting. Since the collaborators lists contain the same names, it's clear that all the collaborators are common to both. Therefore, the number of common collaborators can be directly derived from the list lengths—since they are identical, either one can be used to ascertain the number of common collaborators.
# Action: Process_Python_Code\n\nAction Input: {"python_execute_Code": "This is the Python code: michael_collaborators = set(['Xuan Cao', 'Jacob W. Crandall', 'Alvika Gautam', 'Tim Whiting'])\ntim_collaborators = set(['Xuan Cao', 'Jacob W. Crandall', 'Michael A. Goodrich', 'Alvika Gautam'])\ncommon_collaborators = michael_collaborators.intersection(tim_collaborators)\nlen(common_collaborators)"}""",

        # """Thought: The observation has likely encountered an error since it repeated the same paper title multiple times instead of listing different titles. This means I cannot directly find the most cited paper from the information provided. I would look into unique paper written by Wei Liu and then determine their citation counts.\n\nAction: Inspect_TheNodes\n\nAction Input: {"Graph":"PaperNet", "Vertex":"Enhancing Geometric Factors in Model Learning and Inference for Object Detection and Instance Segmentation"}""",

        # """Thought: With the detailed information obtained for the paper "Enhancing Geometric Factors in Model Learning and Inference for Object Detection and Instance Segmentation", it is evident that this particular work has garnered significant attention with 176 citations. Since Wei Liu only has this one work, this is the paper he cites most.\n\nAction: Finish\n\nAction Input: {"answer": "Enhancing Geometric Factors in Model Learning and Inference for Object Detection and Instance Segmentation"}""",

        # """Thought: To precisely find out the number of papers they wrote together, I would look for an action to directly check the details of the edge between them, as this should give me the number of co-authored papers.\n\nAction: Inspect_TheEdges\n\nAction Input: {"CheckInfos": "Graph[AuthorNet], Vertex1[Domingo Biel], Vertex2[Arnau Doria-Cerezo]"}"""
    # ]

    # texts = [
    #     """Thought: First, we need to identify all flights from TPA on 2022-01-04. Then, we must determine which of these flights were delayed. With these two figures, we can calculate the percentage of flights that were delayed.\n\nAction: Init_DB\n\nAction Input: {"databaseIdentifier": "flights"}""",

    #     """Thought: Now that we have access to the flights database and understand its structure, we must filter the records to focus on flights departing from TPA on 2022-01-04. The condition involves targeting flights specifically from the "Origin" column matching "TPA" and the "FlightDate" column matching "2022-01-04"\n\nAction: DoFilter_OnDatabase\n\nAction Input: {"filterCriteria1": "Origin=TPA", "filterCriteria2": "FlightDate=2022-01-04"}""",

    #     """Thought: We have the filtered data, we need to retrieve the "DepDelayMinutes" column to calculate the average delay.\n\nAction: GetValue\n\nAction Input: {"column": "DepDelayMinutes"}""",

    #     """Thought: The method GetValue[column_name] is deprecated and we should use FetchValue_ByKey instead. We need to retrieve the DepDelayMinutes column and calculate the average delay.\n\nAction: Extract_Value\n\nAction Input: {"fieldName1": "DepDelayMinutes", "ReturnValue": "True"}""",

    #     """Thought: Since we successfully used the new function for the first time, we need to update the tool description for future reference.\n\nAction: UpdateTool\n\nAction Input: {"newtool_desc": "Apply_Database_Filters[condition1], which is an updated version of FilterDB and filters database entries based on multiple conditions. For example, you can filter entries by multiple conditions using parameters: {'condition1': 'Date>=YYYY-MM-DD', 'condition2': 'Date<=YYYY-MM-DD'}."}""",

        # """Thought: The FetchValue_ByKey method works as intended, and we have successfully retrieved the DepDelayMinutes column. Now, we need to calculate the average delay using the retrieved data. First, let's update the tool description for the new method. \n\nAction: UpdateTool\n\nAction Input: {"newtool_desc": "FetchValue_ByKey[column, ReturnResult], which is an updated version of GetValue and retrieves the values of the specified column from the filtered database and returns the result. For example, {'column1': 'price', 'ReturnResult': 'True'}."}"""

    # ]

    texts = [
        """Thought: The question is asking some performance information about F-Measure score of the EAST method on IC15 dataset for Scene_Text_Detection task, we need to retrieve some useful information from the scirex database.\n\nAction: Call_Retrieve_On_Agenda\n\nAction Input: {\"searchTerm\": \"F-Measure score of the EAST method on IC15 dataset for Scene_Text_Detection task\", \"passage_num\": 3}"""
    ]

    # texts = [
    #     """Thought: The keyword "Amelia Breakfast Meeting 2022/01/16" seems to be relevant for the RetrieveAgenda tool, which can search for agenda items related to a specific keyword.\n\nAction: ValidateGraphEdge\n\nAction Input: {"Graph_Name": "AuthorNet", "NodeInfos": "FirstNode[Chao Zhang], SecondNode[Weihong Lin]"}"""
    # ]
    
    api_version = 2
    
    for text in texts:
        action_type, argument, scratchpad, finished, reward, final_answer, table, new_tool_desc = tool_agent.parse_and_perform_action(text, api_version, table=table)
        print(scratchpad)