import os, sys
os.chdir(sys.path[0])
import os.path as osp
import time
import torch
import torch.nn as nn
import json
import re
import copy
import numpy as np
import random
import importlib

from tqdm import tqdm
from typing import List, Dict, Tuple
from termcolor import colored

from vllm import LLM, SamplingParams
from vllm.outputs import RequestOutput

from arguments import get_args, set_seed
from prompts import custom_prefix, custom_suffix, STOP, OBSERVATION_LTAG, OBSERVATION_RTAG, TOOL_DESC_TOOLQA, UpdateTool_Example
from constants import (
    TOO_MANY_STEPS,
    NO_VALID_CHILD,
    TOO_MANY_LOADS,
)

from toolqa import ToolQA_Serve
from tools.table.tabtools import table_toolkits

import logging
logger = logging.getLogger(__name__)

def load_function(args):
    import_path = f"few_shots.{args.task}.{args.dataname}"
    module = importlib.import_module(import_path)
    
    examples = getattr(module, "examples", None)
    
    return examples


def load_data(args):
    with open(osp.join(args.datapath, args.task, f'{args.dataname}.jsonl'), 'r') as f:
        data = [json.loads(line) for line in f]
    if args.debug_num > 0:
        data = data[:args.debug_num]
    # 对data进行遍历，去掉已经有solution的结果
    if args.filter:
        with open(args.filter_path, 'r') as f:
            collected_ids = json.load(f)[args.dataname]["question_ids"]
        filtered_data = []
        for item in data:
            if item['qid'] not in collected_ids:
                filtered_data.append(item)
        return filtered_data
    else:
        return data

def load_agent(args):
    llm = LLM(model=args.checkpoint_dir, tensor_parallel_size=1, seed=args.seed)
    sampling_params = SamplingParams(
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        use_beam_search=False,
        best_of=args.n_generate_sample,
        max_tokens=args.max_new_tokens, 
        n=args.n_generate_sample,
        stop=STOP,
    )

    return llm, sampling_params


class State():
    """
    This class represents the state of a node
    param text: new generation text in this node
    param text: previous text from root to current node
    param is_terminal: whether stopping
    
    """
    def __init__(self, text="", action=None, action_input=None, final_answer=None, is_terminal=False, reward=None):
        self.text = text
        self.is_terminal = is_terminal

        self.action = action
        self.action_input = action_input
        self.final_answer = final_answer
        self.reward = reward


class Node():
    """
    This class defines a node of the tree
    param parent: parent node
    param state: state of current node
    param visit_count: number of visit
    param P: prior probability
    param total_value: the expected probability of solving this problem
    """
    def __init__(self, tag='', parent=None, state=None, P=None, depth=0, table=None, new_tool=[], load_cnt=0):
        self.tag = tag
        self.parent = parent
        self.state = state
        self.depth = depth

        self.visit_count = 0
        self.P = P
        self.total_value = 0
        
        self.children = []

        self.table = table
        self.load_cnt = load_cnt

        self.new_tool = new_tool

    
    def has_children(self) -> bool:
        return self.children != []


class MCTS():

    def __init__(self, args, data_item, model=None, sampling_params=None, root=None, epoch=None):
        self.args = args
        self.model = model
        self.sampling_params = sampling_params
        self.question_id = data_item['qid']
        self.question = data_item['question']
        self.answer = str(data_item['answer'])  # 全部转化成字符串
        self.positive_reward = self.args.positive_reward
        self.negative_reward = self.args.negative_reward

        # 每个mcts的tool desc是不同的
        self.tool_desc = TOOL_DESC_TOOLQA

        self.epoch = epoch

        if root is None:
            self.root = Node(tag='0', parent=None, state=State(text=""), P=1, table=None)
        else:
            self.root = root

        self.example_pool = load_function(args)

        assert self.example_pool is not None, "example_pool is None"

        self.solution_nodes = []  # store the node that solved the problem (both positive and negative)

        # create tool pool
        self.tool_agent = ToolQA_Serve(args, self.answer)

        # api varying
        self.api_version = self.args.api_kernel_version

        self.update_example = UpdateTool_Example


    @torch.inference_mode()
    def search(self):

        for i in range(self.args.max_iter):  # maximally allowed iterations
            self.search_once()
            # print(f"round: {i+1}".center(50, '-'))
        
        states = self.return_states()
        solutions_tag = [node.tag for node in self.solution_nodes]
        result = {"id": self.question_id, 'question': self.question, 'answer': self.answer, "tree": states, 'answer_node': solutions_tag}

        with open(osp.join(args.output_dir, f"{self.epoch}_{self.question_id}.json"), 'a') as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        
    def return_states(self):
        candidates = [self.root]
        states = {}
        while candidates:
            node = candidates.pop(0)
            state = {}
            for k, v in node.state.__dict__.items():
                state[k] = v
            tmp = {'state': state, 'P': node.P, 'total_value': node.total_value, 'visit_count': node.visit_count, 'num_child': len(node.children), 'new_tool': node.new_tool}
            states[node.tag] = tmp
            if node.has_children():
                candidates.extend(node.children)
        return states

    def search_once(self):
        # perform an iteration including selection, expansion, evaluation and back_propagation

        ## selection
        front = self.selection(self.root)

        # expansion_evaluation and backpropagation
        if front is not None:
            self.expansion_evaluation_backpropagation(front)
        else:
            if self.args.verbose:
                print('Warning: select the terminal node ...')

    def selection(self, start_node):
        node = start_node
        while (not node.state.is_terminal) and node.has_children():
            all_rollout_children = all([child.visit_count == 0 for child in node.children])
            if all_rollout_children:
                break
            else:
                next_node = self.select_child(node)
                if next_node is None:
                    node.state.is_terminal = True  # all children are terminal
                    break
                node = next_node

        return None if node.state.is_terminal else node

    def select_child(self, node):
        best_value = -float("inf")
        best_childs = []
        total_visits = sum(child.visit_count for child in node.children)

        for child in node.children:
            if child.state.is_terminal:
                continue
            # calculate PUCT
            Q = child.total_value / child.visit_count if child.visit_count > 0 else 0
            U = self.args.Cpuct * child.P * np.sqrt(total_visits) / (1 + child.visit_count)
            puct_value = Q + U

            if puct_value == best_value:
                best_childs.append(child)
            elif puct_value > best_value:
                best_value = puct_value
                best_childs = [child]
        if len(best_childs) > 0:
            return random.choice(best_childs)
        else:
            return None  # 所有children都terminal了

    def expansion_evaluation_backpropagation(self, node, rollout=False):
        # perform expansion and evaluation
        # obtain the prior probability of subnode and the value of the leaf node

        if not node.state.is_terminal and not node.has_children():
            # 没有被rollout，需要扩展
            outputs = self.get_nextstep_and_cur_value(node)
            # 创建叶子节点，进行rollout，并且back——propagation
            self.expand_node(outputs, node, rollout)
        
        else:
            # 已经有cache了，直接从缓存的节点中对每个节点进行rollout
            self.expand_node_with_cache(node)



    def get_nextstep_and_cur_value(self, node):
        prompt = self.get_llm_request(node)
        outputs = self.model.generate([prompt], self.sampling_params, use_tqdm=False)
        return outputs[0]  # 单个生成


    def get_llm_request(self, node) -> str:
        # obtain the prompt of this state
        cur_examples = random.sample(self.update_example, min(len(self.update_example), 1)) + random.sample(self.example_pool, min(len(self.example_pool), self.args.num_examples))

        tool_desc = self.tool_desc if len(node.new_tool) == 0 else self.tool_desc + "\n" + "\n".join(node.new_tool)
        cur_prompt = custom_prefix.format(tool_desc=self.tool_desc + tool_desc) + "\nHere are some examples:\n\n" + "\n\n".join(cur_examples) + "\n\n" + custom_suffix.format(input=self.question)

        # get partial solution
        step_texts = [node.state.text]
        pre_node = node.parent
        while pre_node is not None:
            step_texts.insert(0, pre_node.state.text)
            pre_node = pre_node.parent
        
        _partial_solution = "\n\n".join(step_texts).strip()
        if _partial_solution:
            prompt = cur_prompt.strip() + "\n\n" + _partial_solution + "\n\n"
        else:
            prompt = cur_prompt.strip() + "\n\n"

        return prompt

    
    def expand_node(self, outputs: RequestOutput, node: Node, rollout):
        # 去重
        action_text = set()
        num_child = 0
        # 创建子节点，并且rollout到底部
        for step_output in outputs.outputs:
            if len(step_output.text) == 0:  # 上一个节点为止的prompt超长，导致text为空，直接terminal
                prior_prob = 0
                node.state.is_terminal = True
                node.state.reward = self.args.negative_reward
                if not rollout:
                    self.back_propagation(node, node.state.reward)
            else:
                if step_output.text not in action_text:
                    action_text.add(step_output.text)
                    prior_prob = np.exp(step_output.cumulative_logprob / len(step_output.token_ids))
                    new_node = self.action_parser(step_output.text, node, prior_prob, idx=num_child)
                    num_child += 1
                    if not rollout:
                        if new_node.state.reward is None:
                            reward, end_node = self.rollout(new_node)
                        else:
                            reward = new_node.state.reward

                        self.back_propagation(new_node, reward)
        
        # 当前节点扩展完后，不会二次扩展，并且table已经被子节点继承，因此可以清空当前节点的table
        node.table = None

    def expand_node_with_cache(self, node: Node):
        # 这个节点一定有孩子节点
        for child in node.children:
            if child.state.reward is None:
                reward, end_node = self.rollout(child)
            else:
                reward = child.state.reward

            self.back_propagation(child, reward)

    def action_parser(self, text: str, node: Node, prior_prob: float, idx: int):
        # parse the text and invoke the tool
        if self.args.task in ["toolqa_easy", "toolqa_hard"]:
            
            action_type, action_input, observation, finished, reward, final_answer, table, new_tool_desc = self.tool_agent.parse_and_perform_action(text, api_version=self.api_version, table=table_toolkits(self.args.path) if node.table is None else copy.deepcopy(node.table))
        else:
            raise NotImplementedError
        
        text = f"{text.strip()}\n\n{OBSERVATION_LTAG}{observation.strip()}{OBSERVATION_RTAG}"

        new_node = Node(tag=node.tag + f".{idx}", parent=node, state=State(text=text, action=action_type, action_input=action_input, final_answer=final_answer, is_terminal=finished, reward=reward), P=prior_prob, depth=node.depth + 1, table=table, new_tool=copy.deepcopy(node.new_tool), load_cnt=node.load_cnt)

        # 更新工具
        if new_tool_desc is not None:
            new_node.new_tool.append(f"({14 + len(new_node.new_tool)}) {new_tool_desc}")

        if action_type is None:
            # error in action parser
            new_node.state.is_terminal = True
            new_node.table = None
        elif final_answer is not None:
            # 有答案的时候一定terminal
            # new_node.state.reward = self.get_reward(new_node.state.final_answer)
            new_node.table = None  # terminal了之后不需要table了
            self.solution_nodes.append(new_node)
        elif node.depth > self.args.max_depth:
                new_node.state.is_terminal = True
                new_node.table = None
                new_node.state.final_answer = TOO_MANY_STEPS
                new_node.state.reward = self.args.negative_reward
        else:
            if action_type in ['LoadDB', 'LoadGraph', 'InitializeDatabase', 'InitializeGraphData', 'Init_DB', 'Import_Graph']:
                new_node.load_cnt += 1
            if new_node.load_cnt > self.args.max_load_db:
                new_node.state.is_terminal = True
                new_node.table = None
                if new_node.state.final_answer is None:
                    new_node.state.final_answer =  TOO_MANY_LOADS
                    new_node.state.reward = self.args.negative_reward


        if self.args.verbose:
            print(colored(f"{action_type}[{action_input}]\n", "green"))
            print(colored(f"{OBSERVATION_LTAG}{observation}{OBSERVATION_RTAG}\n", "yellow"))

        node.children.append(new_node)

        return new_node
    
    
    def back_propagation(self, node: Node, value_estimate: float) -> None:
        while node is not None:
            node.visit_count += 1
            node.total_value += value_estimate
            node = node.parent


    def get_partial_solution(self, node) -> str:    
        # get partial solution
        step_texts = [node.state.text]
        pre_node = node.parent
        while pre_node is not None:
            step_texts.insert(0, pre_node.state.text)
            pre_node = pre_node.parent
        
        _partial_solution = "\n".join(step_texts)

        return _partial_solution

    def rollout(self, node):
        while not node.state.is_terminal:
            if not node.has_children():  # 如果没有children，就进行生成
                self.expansion_evaluation_backpropagation(node, rollout=True)
                if not node.has_children():
                    node.state.final_answer = NO_VALID_CHILD
                    node.state.is_terminal = True
                    break
            node = random.choice(node.children)

        if node.state.reward is None:
            node.state.reward = self.get_reward(node.state.final_answer)
        return node.state.reward, node 


    def get_reward(self, pred_answer):
        if self.tool_agent.is_correct(pred_answer, self.answer):
            reward = self.args.positive_reward
        else: 
            reward = self.args.negative_reward
        return reward




def main(args):
    set_seed(args.seed)

    data = load_data(args)

    llm, sampling_params = load_agent(args)

    for epoch in range(args.num_epoch):
        logger.info(f"epoch :{epoch}")
        for data_item in tqdm(data):
            mcts = MCTS(args, data_item, model=llm, sampling_params=sampling_params, epoch=epoch)
            mcts.search()
        
    


if __name__=='__main__':
    args = get_args()
    main(args)