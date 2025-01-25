import os, sys
os.chdir(sys.path[0])
import argparse

from tool_online import ToolQA_OnLine

from flask import Flask, request, jsonify

app = Flask(__name__)

def create_tool_agent(tool_device, path):
    args = argparse.Namespace(tool_device=tool_device, path=path)
    return ToolQA_OnLine(args)

tool_agent = create_tool_agent(tool_device=0, path="YOURPATH/ToolQA-D")

@app.route('/toolqa', methods=['POST'])
def call_toolqa():
    if request.is_json:
        data = request.json
        new_action_type = data.get('new_action_type', '')
        new_params = data.get('new_params', "{}")

        observation = tool_agent.parse_and_perform_action(new_action_type, new_params)

        result = {"observation": observation}
        return jsonify(result)
    else:
        return jsonify({"error": "Request must be JSON"}), 400


