import os, sys
os.chdir(sys.path[0])
import os.path as osp
import time
import numpy as np
import json
import random
import pynvml

from datetime import datetime
from termcolor import colored
from multiprocessing import Process, Manager
from vllm import LLM, SamplingParams
from tqdm import tqdm
from pebble import ProcessPool, ProcessExpired


from arguments import get_args, set_seed
from prompts import STOP
from mcts import load_data
from local_mcts import LocalMCTS

import logging
logger = logging.getLogger(__name__)

TIMEOUT_PROCESS = 3600
TIME_SPAN_LLM = 0.5
MAX_SOLUTIONS_COUNT = 5


# LLM check time
CHECK_INTERVAL = 60 
UNIT = 1024**3

BAR_TIME = 15


def llm_generate(args, public_prompts, public_outputs, public_n, task_flag):
    try:
        random_seed = args.seed
        # init llm
        available_gpus = os.environ.get('CUDA_VISIBLE_DEVICES', "0").split(',')

        llm = LLM(model=args.checkpoint_dir, tensor_parallel_size=len(available_gpus), seed=random_seed, swap_space=8)
        sampling_params = SamplingParams(
                            temperature=args.temperature,
                            top_p=args.top_p,
                            best_of=args.n_generate_sample,
                            max_tokens=args.max_new_tokens,
                            n=args.n_generate_sample,
                            # frequency_penalty=args.frequency_penalty,
                            stop=STOP,
                        )

        while True:
            time.sleep(TIME_SPAN_LLM)
            task_key = []
            prompts = []
            n_list = []

            # generator
            for key, val in public_prompts.items():
                task_key.append(key)
                prompts.append(val)
                n_list.append(public_n[key])
                # if len(prompts) > 5:
                #     break
                
            if len(prompts) > 0:
                # logger.info(f"generate {len(prompts)}, {len(prompts[0].split())}")  # 4079298  24024656
                task_flag.value = len(prompts)
                sampling_params.n = max(n_list) if len(n_list) > 0 else 1 
                # print(prompts)
                # print(len(prompts))
                outputs = llm.generate(prompts, sampling_params, use_tqdm=False)
                for key, output in zip(task_key, outputs):
                    # task finished
                
                    samples, prior_probs = [], []
                    for item in output.outputs:
                        samples.append(item.text)
                        prior_probs.append(0 if len(item.token_ids)==0 else np.exp(item.cumulative_logprob / len(item.token_ids)))

                    del public_prompts[key]
                    del public_n[key]
                    
                    public_outputs[key] = {"texts": samples, "prior_probs": prior_probs}
            # else:
            #     logger.info("cache None")
            #     logger.info(public_prompts)

    except Exception as e:
        logger.exception(f"llm error {e}", exc_info=True)


def get_all_gpu_memory_usage():
    pynvml.nvmlInit()  # 初始化NVML库
    # gpu_count = pynvml.nvmlDeviceGetCount()  # 获取GPU数量
    gpu_memory_info = []
    available_gpus = os.environ.get('CUDA_VISIBLE_DEVICES', "0").split(',')
    for i in available_gpus:
        handle = pynvml.nvmlDeviceGetHandleByIndex(int(i))
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_memory_info.append({
            'index': i,
            'total': mem_info.total,
            'used': mem_info.used,
            'free': mem_info.free
        })
    pynvml.nvmlShutdown()  # 关闭NVML库
    return gpu_memory_info


def monitor_llm_process(args, public_prompts, public_outputs, public_n, task_flag, monitor_flag):
    # 避免检查每一个，只检查自己能访问到的那个gpu，inference暂时没有开启
    llm_process = Process(target=llm_generate, args=(args, public_prompts, public_outputs, public_n, task_flag))
    llm_process.start()
    time.sleep(CHECK_INTERVAL * 4)  # wait llm start
    while monitor_flag.value:
        time.sleep(CHECK_INTERVAL) 
        if monitor_flag.value == 0:
            logger.info(f"monitor break, due to monitor_flag {monitor_flag.value}")
            break
        gpu_memory_info = get_all_gpu_memory_usage()
        for gpu in gpu_memory_info:
            if gpu['used'] / UNIT < 0.3:  # GPU memory less than 10GB
                logger.info('LLM process might be stuck. Restart required.')
                llm_process.terminate()
                llm_process.join()
                llm_process = Process(target=llm_generate, args=(args, public_prompts, public_outputs, public_n, task_flag))
                llm_process.start()
            else:
                logger.info('LLM process is alive.')
    
    logger.info("finish llm_process")
    llm_process.terminate()
    llm_process.join()
    

def mcts_search(params):
    args, data_item, public_prompts, public_outputs, public_n, task_flag, public_mcts_outputs, epoch = params
    try:
        mcts_tree = LocalMCTS(args=args, data_item=data_item, epoch=epoch)
        mcts_tree.set_public_info(local_prompts_cache = public_prompts,
                            local_outputs_cache = public_outputs,
                            local_n_cache = public_n,
                            local_n_generate_samples=task_flag)

        outputs = mcts_tree.search()

        public_mcts_outputs[data_item['qid']] = outputs

        
    except Exception as e:
        logger.exception(f"mcts error {e}", exc_info=True)


def progress_bar(public_mcts_outputs, epoch_file_path, epoch, monitor_flag, total=None, final_file_name='final_result.jsonl', desc="Execute"):

    progress_bar = tqdm(total=total, desc=desc)
    completed_id = []
    temp_outputs = []
    pre_num = 0
    while True:
        time.sleep(BAR_TIME)

        # save_result
        for key, val in public_mcts_outputs.items():
            if key not in completed_id:
                completed_id.append(key)
                temp_outputs.append(val)
            
            if len(temp_outputs) >= MAX_SOLUTIONS_COUNT:
                logger.info(f'save solutions: {MAX_SOLUTIONS_COUNT}')
                write_solutions_to_file(epoch_file_path, temp_outputs, epoch)
                temp_outputs.clear()

        current_num = len(public_mcts_outputs)
        progress_bar.update(current_num - pre_num)
        if current_num >= total:
            break
        else:
            pre_num = current_num
        
        if monitor_flag.value == 0:
            logger.info(f'monitor_flag is {monitor_flag.value}, stop the progress_bar')
            break

    progress_bar.close()
    logger.info("stop progress_bar")
    # save_result
    all_solutions = []
    for key, val in public_mcts_outputs.items():
        all_solutions.append(val)
        if key not in completed_id:
            completed_id.append(key)
            temp_outputs.append(val)
        
    logger.info(f'save surplus solutions: {len(temp_outputs)}')
    write_solutions_to_file(epoch_file_path, temp_outputs, epoch)

    write_solutions_to_file(osp.join(osp.dirname(epoch_file_path), final_file_name), all_solutions, epoch)
    


def batch_main(args, data, epoch_file_path, epoch):
    try:
        with Manager() as manager:
            public_prompts = manager.dict()  # input text for generator
            public_outputs = manager.dict()  # genrated text, avg prob and value from generator: {"texts": [], "prior_probs": [], "value": float}
            public_n = manager.dict()  # the number of generated text
            task_flag = manager.Value('i', 1)
            monitor_flag = manager.Value('i', 1)

            public_mcts_outputs = manager.dict()

            monitor_process = Process(target=monitor_llm_process, args=(args, public_prompts, public_outputs, public_n, task_flag, monitor_flag))
            monitor_process.start()


            epoch_trees = []
            for item in data:
                epoch_trees.append((args, item, public_prompts, public_outputs, public_n, task_flag, public_mcts_outputs, epoch))
            
            final_file_name = f"{args.dataname}_{args.timestamp}_{str(args.sft_prompt)}_final_result.jsonl"
            progress_bar_process = Process(target=progress_bar, args=(public_mcts_outputs, epoch_file_path, epoch, monitor_flag, len(epoch_trees), final_file_name))
            progress_bar_process.start()

            
            if args.dataname in ["airbnb-easy"]:
                cpu_num = 8
            elif args.dataname in ["flights-easy", "yelp-easy"]:
                cpu_num = 5
            else:
                cpu_num = 10

            with ProcessPool(max_workers=min(len(epoch_trees), min(os.cpu_count(), cpu_num))) as pool:
                future = pool.map(mcts_search, epoch_trees, timeout=TIMEOUT_PROCESS)
                try:
                    for _ in future.result():
                        pass
                except ProcessExpired as e:
                    logger.exception(f"process expired: {e}")
                except Exception as e:
                    logger.exception(f"pool error: {e}")

            logger.info("all question have been sampled.")
            monitor_flag.value = 0
            monitor_process.join()

            progress_bar_process.join()

    except Exception as e:
        logger.exception(colored(f"Exception: {e}", "red"), exc_info=True)
    
    except KeyboardInterrupt as ki:
        logger.info(f"save {epoch} file", exc_info=True)


def write_solutions_to_file(file_path, all_solutions, epoch):
    with open(file_path, 'a') as writer:
        for solution_item in all_solutions:
            solution_item["inference_epoch"] = epoch
            writer.write(json.dumps(solution_item, ensure_ascii=False) + '\n')
            writer.flush()



if __name__=='__main__':
    args = get_args()
    set_seed(args.seed)
    data = load_data(args)

    epoch_file_path = osp.join(args.output_dir, f'{args.dataname}_{args.timestamp}_{str(args.sft_prompt)}.jsonl')
    try:
        batch_main(args, data, epoch_file_path, 0)
    except Exception as e:
        logger.exception(colored(f"Batch Process Exception: {e}", "red"))
            