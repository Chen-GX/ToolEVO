import os
import os.path as osp
import time
import argparse
import random
import numpy as np
import torch
from log_utils import log_params


# max_depth_dict = {"agenda-easy": 6, "airbnb-easy": 12, "coffee-easy": 12, "dblp-easy": 12, "flights-easy": 12, "scirex-easy": 6, "yelp-easy": 12,
# "agenda-hard": 12, "airbnb-hard": 12, "coffee-hard": 15, "dblp-hard": 12, "flights-hard": 15, "scirex-hard": 6, "yelp-hard": 12,}

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v == 'True':
        return True
    if v == 'False':
        return False

def set_seed(seed: int = 1024) -> None:
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    # When running on the CuDNN backend, two further options must be set
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    # logger.info(f"Random seed set as {seed}")


def get_args():
    root_path = "your path"

    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--verbose', type=str2bool, default=False, help="print intermediate result on screen")
    parser.add_argument('--process_num', type=int, default=1)
    parser.add_argument("--path", type=str, default=f"{root_path}/data/ToolQA-D")
    parser.add_argument("--num_epoch", type=int, default=1)
    parser.add_argument("--tool_url", type=str, default="http:/xx.xxx.xxx.xx:5010/toolqa")
    # parser.add_argument("--filter", type=str2bool, default=False)
    # parser.add_argument("--filter_path", type=str, default="")

    ## params of LLM
    parser.add_argument('-c', '--checkpoint_dir', type=str, default=f'llama3.1-8b')
    parser.add_argument('--model_type', type=str, default=f'gpt')
    parser.add_argument('--api_key', type=str, default=f'your api key')
    parser.add_argument('--base_url', type=str, default=f'your base url')

    parser.add_argument('--temperature', type=float, default=0.0)
    parser.add_argument("--top_k", type=int, default=-1)
    parser.add_argument("--top_p", type=float, default=1.0)  
    # parser.add_argument("--frequency_penalty", type=float, default=1.2)
    parser.add_argument("--scratchpad_length", type=int, default=1024)


    ## params of api varying
    parser.add_argument("--api_kernel_version", type=int, default=1)
    

    ## params of mcts
    # parser.add_argument("--Cpuct", type=float, default=1.25)
    parser.add_argument('--n_generate_sample', type=int, default=1, help="how many samples generated for each step")
    parser.add_argument('--max_iter', type=int, default=20, help="maximally allowed iterations")
    parser.add_argument("--max_depth", type=int, default=20)
    parser.add_argument('--positive_reward', type=float, default=1.)
    parser.add_argument('--negative_reward', type=float, default=-1.)
    parser.add_argument("--max_new_tokens", type=int, default=1024)
    parser.add_argument("--max_load_db", type=int, default=5)

    ## params of file
    parser.add_argument("--debug_num", type=int, default=1)
    parser.add_argument('--datapath', type=str, default=f"{root_path}/test_data")
    parser.add_argument('--task', type=str, default='toolqa_easy', choices=["toolqa_easy", "toolqa_hard"])
    parser.add_argument('--dataname', type=str, default='coffee-easy',
                        choices=["agenda-easy", "airbnb-easy", "coffee-easy", "dblp-easy", "flights-easy", "scirex-easy", "yelp-easy", "agenda-hard", "airbnb-hard", "coffee-hard", "dblp-hard", "flights-hard", "scirex-hard", "yelp-hard"])
    parser.add_argument("--output_dir", type=str, default=f"{root_path}/output_dir/greedy/test")
    parser.add_argument("--num_examples", type=int, default=2)

    # few-shot
    parser.add_argument("--sft_prompt", type=str2bool, default=False)
    parser.add_argument("--instruct", type=str2bool, default=False)

    args = parser.parse_args()  # 解析参数

    args.model_name = osp.basename(osp.dirname(args.checkpoint_dir))
    args.ckpt = osp.basename(args.checkpoint_dir)

    args.timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    
    args.output_dir = osp.join(args.output_dir, args.task, str(args.api_kernel_version), args.model_name, args.ckpt)
    os.makedirs(args.output_dir, exist_ok=True)

    # args.max_depth = max_depth_dict[args.dataname]

    args.prompt_split_len = 10000
    if "Qwen2" in args.checkpoint_dir:
        args.prompt_split_len = 35000

    log_params(args)
    
    return args