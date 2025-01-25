from typing import List, Dict
from timeout_decorator import timeout

try:
    from tools.code.python_tool import PythonInterpreter
except:
    from python_tool import PythonInterpreter

def _python_ast_init():
    python = PythonInterpreter(globals=globals(), locals=None)
    return python


def tool_wrapper(tool):
    def _tool(query):
        return tool.run(query)
    return _tool


def no_action_wrapper(tool):
    def _tool(query):
        return "No action, no observation. Please continue to solve."
    return _tool

# We define a dummy tool, to implement multiple tools.
tools = {
    "None": no_action_wrapper(_python_ast_init()),
    "python_interpreter": tool_wrapper(_python_ast_init()),
}


def action_execution(parser_results: str) -> str:

    @timeout(30)
    def _action_execution(parser_results: str) -> str:
        # cur_action = parser_results[-1]["action"]
        tool_func = tools["python_interpreter"]

        # first, execute historical action inputs with the same action, but not output
        # for history_act in parser_results[:-1]:
        #     if history_act["action"] == cur_action:
        #         _ = tool_func(history_act["action_input"])
        
        # then, execute current action input, and return output
        observation = str(tool_func(parser_results))
        del tool_func
        return observation 
    
    try:
        observation = _action_execution(parser_results)
    except Exception as e:
        observation = "{}: {}".format(type(e).__name__, str(e))

    return observation


if __name__=="__main__":
    # code = '# solution in Python: \n# Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?\ngolf_balls_initial = 58\ngolf_balls_lost_tuesday = 23\ngolf_balls_lost_wednesday = 2\ngolf_balls_left = golf_balls_initial - golf_balls_lost_tuesday - golf_balls_lost_wednesday\nresult = golf_balls_left\nprint(result)'
    code = "0.8499999999999943"
    print(action_execution(code))