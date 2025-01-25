import pandas as pd
import jsonlines
import json
import re
import copy
from datetime import datetime


def convert_time(time_str):
    # 尝试指定的两种格式
    for time_format in ("%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(time_str, time_format).time()
        except ValueError:
            pass  # 忽略转换异常，尝试下一个格式
    # 如果两种格式都失败了，可以返回原始字符串或者抛出异常
    return time_str


def time_to_str(time_obj):
    """将datetime.time对象转换为其字符串表示形式"""
    return time_obj.strftime("%H:%M:%S")


class table_toolkits():
    # init
    def __init__(self, path):
        self.data = None
        self.path = path
        self.loaded_db_name = None

    def db_loader(self, target_db):
        target_db = target_db.lower()
        scratchpad = ""
        # if self.loaded_db_name is None or self.loaded_db_name != target_db:
        if target_db == 'flights':
            file_path = "{}/data/external_corpus/flights/Combined_Flights_2022.csv".format(self.path)
            self.data = pd.read_csv(file_path)
        elif target_db == 'coffee':
            file_path = "{}/data/external_corpus/coffee/coffee_price.csv".format(self.path)
            self.data = pd.read_csv(file_path)
        elif target_db =='airbnb':
            file_path = "{}/data/external_corpus/airbnb/Airbnb_Open_Data.csv".format(self.path)
            self.data = pd.read_csv(file_path)
        elif target_db == 'yelp':
            data_file = open("{}/data/external_corpus/yelp/yelp_academic_dataset_business.json".format(self.path))
            data = []
            for line in data_file:
                data.append(json.loads(line))
            self.data = pd.DataFrame(data)
            data_file.close()
        elif target_db =='agenda':
            contents = []
            file_path = "{}/data/raw_data/agenda/agenda_events.jsonl".format(self.path)
            with open(file_path, 'r') as f:
                for item in jsonlines.Reader(f):
                    contents.append(item)
            self.data = pd.DataFrame(contents)
            # 对时间进行处理
            self.data['start_time'] = self.data['start_time'].apply(convert_time)
            self.data['end_time'] = self.data['end_time'].apply(convert_time)

        else:
            raise ValueError("The requested database is not available")
        self.loaded_db_name = target_db
        self.data = self.data.astype(str)
        column_names = ', '.join(self.data.columns.tolist())
        scratchpad += "We have successfully loaded the {} database, including the following columns: {}.".format(target_db, column_names)
        # else:
        #     scratchpad += f"You have already loaded database {target_db}, please do not reload the database."
        
        return scratchpad

    # def get_column_names(self, target_db):
    #     return ', '.join(self.data.columns.tolist())

    def process_commands(self, command):
        column_name = command[0].strip()
        value = command[1].strip()
        if column_name in ['Distance', "latitude", "longitude", "lat", "long"]:
            try:
                value = float(value)
            except:
                value = command[1].strip()

            try:
                if isinstance(value, float):
                    self.data.loc[:, column_name] = self.data.loc[:, column_name].astype(float)
            except:
                pass
        
        if column_name in ["start_time", "end_time"]:
            try:
                value = time_to_str(convert_time(value))
            except:
                pass

        return column_name, value

    def data_filter(self, argument):
        # commands = re.sub(r' ', '', argument)
        if self.data is None:
            return "Please first load the relevant database using `LoadDB` before proceeding with `FilterDB`."

        backup_data = self.data
        commands = argument.split(', ')
        
        for i in range(len(commands)):
            try:
                # commands[i] = commands[i].replace(' ', '')
                if '>=' in commands[i]:
                    command = commands[i].split('>=')
                    column_name, value = self.process_commands(command)
                    # value = command[1].strip()
                    self.data = self.data[self.data[column_name] >= value]
                elif '<=' in commands[i]:
                    command = commands[i].split('<=')
                    column_name, value = self.process_commands(command)
                    # column_name = command[0].strip()
                    # value = command[1].strip()
                    self.data = self.data[self.data[column_name] <= value]
                elif '>' in commands[i]:
                    command = commands[i].split('>')
                    column_name, value = self.process_commands(command)
                    # column_name = command[0].strip()
                    # value = command[1].strip()
                    self.data = self.data[self.data[column_name] > value]
                elif '<' in commands[i]:
                    command = commands[i].split('<')
                    column_name, value = self.process_commands(command)
                    # column_name = command[0].strip()
                    # value = command[1].strip()
                    self.data = self.data[self.data[column_name] < value]
                elif '=' in commands[i]:
                    command = commands[i].split('=')
                    column_name, value = self.process_commands(command)
                    # column_name = command[0].strip()
                    # value = command[1].strip()
                    if column_name in ['categories']:
                        self.data = self.data[self.data[column_name].str.contains(value)]
                    else:
                        self.data = self.data[self.data[column_name] == value]
                
                else:  # 给出了不满足上述约束的语句
                    return "The filtering query {} is incorrect. Please modify the condition.".format(commands[i])

                if len(self.data) == 0:
                    self.data = backup_data
                    return "The filtering query {} is incorrect. Please modify the condition.".format(commands[i])
            except:
                return "we have failed when conducting the {} command. Please make changes.".format(commands[i])
        current_length = len(self.data)
        if len(self.data) > 0:
            return "We have successfully filtered the data ({} rows).".format(current_length)
        else:
            # convert to strings, with comma as column separator and '\n' as row separator
            return_answer = []
            for i in range(len(self.data)):
                outputs = []
                for attr in list(self.data.columns):
                    outputs.append(str(attr)+": "+str(self.data.iloc[i][attr]))
                outputs = ', '.join(outputs)
                return_answer.append(outputs)
            return_answer = '\n'.join(return_answer)
            return return_answer

    # def get_value(self, argument):
    #     if self.data is None:
    #         return "Please first load the relevant database using `LoadDB` before proceeding with `GetValue`."
    #     column = argument.strip()
    #     if len(self.data) == 1:
    #         return str(self.data.iloc[0][column])
    #     else:
    #         return ', '.join(self.data[column].tolist())

    def get_value(self, arguments):
        if self.data is None:
            return "Please first load the relevant database using `LoadDB` before proceeding with `GetValue`."
        
        # Split the argument into a list of column names
        columns = []
        for column in arguments.split(','):
            if column.strip() not in columns:
                columns.append(column.strip())
        
        # Now, extract the data for each column
        if len(self.data) == 1:
            # If there is only one row, return the value for each column as a dictionary
            return json.dumps({column: str(self.data.iloc[0][column]) for column in columns})
        else:
            # If there are multiple rows, return the values as a list for each column
            return json.dumps({column: self.data[column].tolist() for column in columns})
            

if __name__ == "__main__":
    db = table_toolkits("/<YOUR_OWN_PATH>/ToolQA-D")
    print(db.db_loader('flights'))
    print(db.data_filter('IATA_Code_Marketing_Airline=AA, Flight_Number_Marketing_Airline=5647, Origin=BUF, Dest=PHL, FlightDate=2022-04-20'))
    print(db.get_value('DepTime'))

    print("*" * 20)
    print(db.db_loader('FilterDB'))
    print(db.data_filter('Origin=PHX, Dest=ATL, Airline=Spirit Air Lines'))
    