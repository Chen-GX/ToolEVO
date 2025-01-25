import time
import copy
import gc

from typing import List, Dict
from termcolor import colored

from mcts import MCTS, Node
from prompts import STOP

import logging
logger = logging.getLogger(__name__)

TIMEOUT_SECONDS_PER_REQUEST = 600
TIMEOUT_MESSAGE_PER_REQUEST = f"Execution of vllm decoding has timed out for exceeding {TIMEOUT_SECONDS_PER_REQUEST} seconds."

class LocalMCTS(MCTS):
    """
    This class mainly implements the multi-process MCTS.
    Do MCTS in Local, and Do generator in cloud
    """

    # local info
    local_prompts_cache: Dict[str, str] = None
    local_outputs_cache: Dict[str, List[str]] = None
    local_n_cache: Dict[str, int] = None
    local_n_generate_samples: int = 1

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prompt_split_len = self.args.prompt_split_len

    def set_public_info(self, local_prompts_cache, local_outputs_cache, local_n_cache, local_n_generate_samples):
        # local info
        self.local_prompts_cache = local_prompts_cache
        self.local_outputs_cache = local_outputs_cache
        self.local_n_cache  = local_n_cache
        self.local_n_generate_samples = local_n_generate_samples  # type_flag


    def search(self):

        for i in range(self.args.max_iter):  # maximally allowed iterations
            self.search_once()
            # logger.info(f"round: {i+1}".center(50, '-'))
        
        states = self.return_states()
        solutions_tag = [node.tag for node in self.solution_nodes]
        result = {"id": self.question_id, 'question': self.question, 'answer': self.answer, "tree": states, 'solutions_tag': solutions_tag}
        gc.collect()
        return {self.question_id: result}

    def expansion_evaluation_backpropagation(self, node, rollout=False):
        # perform expansion and evaluation
        # obtain the prior probability of subnode and the value of the leaf node

        if not node.state.is_terminal and not node.has_children():
            # 没有被rollout，需要扩展
            output_texts, prior_probs = self.get_nextstep_and_cur_value(node)
            # 创建叶子节点，进行rollout，并且back——propagation
            self.expand_node(output_texts, prior_probs, node, rollout)
        
        else:
            # 已经有cache了，直接从缓存的节点中对每个节点进行rollout
            self.expand_node_with_cache(node)
        
    
    def get_nextstep_and_cur_value(self, node):
        prompt = self.get_llm_request(node)

        outputs = self.get_llm_outputs(prompt, n=self.args.n_generate_sample)
        if isinstance(outputs, str):
            return [""], [None]

        return outputs['texts'], outputs['prior_probs']

    
    def get_llm_outputs(self, prompt: str, n=1):
        if len(prompt.split()) > self.prompt_split_len:
            return ""
        
        prompt_key = "generator_{}".format(hash(f"{prompt}{self.question_id}"))
        self.local_n_cache[prompt_key] = n
        self.local_prompts_cache[prompt_key] = prompt
        start_time = time.time()
        while self.local_outputs_cache.get(prompt_key, None) is None:
            try:
                current_samples = max(1, self.local_n_generate_samples.value)
            except:
                current_samples = 1
            
            if time.time() - start_time > current_samples * TIMEOUT_SECONDS_PER_REQUEST:
                logger.info(colored(f"Generating Timeout: {TIMEOUT_MESSAGE_PER_REQUEST}", "red"))
                return "Time out"
        result = self.local_outputs_cache[prompt_key]
        # del self.local_outputs_cache[prompt_key]
        return result

    
    def expand_node(self, output_texts: List[str], prior_probs: List[str], node: Node, rollout):
        # 去重
        action_text = set()
        num_child = 0
        # 创建子节点，并且rollout到底部
        for step_output_text, prior_prob in zip(output_texts, prior_probs):
            if len(step_output_text) == 0:  # 上一个节点为止的prompt超长，导致text为空，直接terminal
                prior_prob = 0
                node.state.is_terminal = True
                node.state.reward = self.args.negative_reward
                # if not rollout:
                #     self.back_propagation(node, node.state.reward)
                self.cur_node = None
            else:
                if step_output_text not in action_text:
                    action_text.add(step_output_text)
                    new_node = self.action_parser(step_output_text, node, prior_prob, idx=num_child)
                    num_child += 1
                    self.cur_node = new_node
                    # if not rollout:
                    #     if new_node.state.reward is None:
                    #         reward, end_node = self.rollout(new_node)
                    #     else:
                    #         reward = new_node.state.reward

                    #     self.back_propagation(new_node, reward)
                else:
                    assert False
        
        # 当前节点扩展完后，不会二次扩展，并且table已经被子节点继承，因此可以清空当前节点的table
        
        node.table = None
        if self.args.dataname in ["airbnb-easy", "coffee-easy", "flights-easy", "yelp-easy"]:
            gc.collect()
    