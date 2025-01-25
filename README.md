# Learning Evolving Tools for Large Language Models

<center>
<a href='https://arxiv.org/abs/2410.06617'><img src='https://img.shields.io/badge/Paper-Arxiv-red'> </a>
</center>

This repository contains the code and benchmark (ToolQA-D) for our research paper titled "[Learning Evolving Tools for Large Language Models](https://arxiv.org/abs/2410.06617)", which has been accepted at ICLR 2025.

# 💥 News 💥
- **[2025.01.25]** We release our code and data.
- **[2025.01.23]** Our [ToolEVO](https://arxiv.org/pdf/2410.06617) is accepted at ICLR 2025.

# :pushpin: TODO 
- [ ] Release the checkpoint
- [x] Release the Code and Data

# :paperclip: Preparation

## Python Environment
* For ToolEVO
```bash
conda create -n toolevo python=3.11
conda activate toolevo
pip install -r requirements.txt
```
* For API Server
```bash
conda create -n api_server python=3.11
conda activate api_server
pip install -r api_server_requirements.txt
```

## Download Pre-train LLM
Please download the `LLama3-8B` and `Qwen2-7B` in the huggingface.


## Benchmark (ToolQA-D)
* The external corpus can be downloaded from [ToolQA](https://github.com/night-chen/ToolQA). After downloading and unzipping, users need to place it under the directory `/<YOUR_OWN_PATH>/ToolQA-D/data/external_corpus/`.
* You can assess the test data in `./test_data`, and training data for MCTS in `./train_data_for_mcts`
* You can change the parameter `api_kernel_version` in `'./MCTS/src/arguments.py` for different environment of API usage:
    * `api_kernel_version = 0` for $\mathcal{P}_c$
    * `api_kernel_version = 1` for $\mathcal{P}_{s_{\text{in}}}$
    * `api_kernel_version = 2` for $\mathcal{P}_{s_{\text{OOD}}}$

# :paperclip: Usage

## API Server
```bash
cd ./MCTS/src
bash start_gunicorn.sh
```

## MCTS in ToolEVO
* ToolQA-D easy
```bash
cd ./MCTS/easy_runs
bash multi_run.sh # or bash single_run.sh
```

* ToolQA-D hard
```bash
cd ./MCTS/hard_runs
bash multi_run.sh # or bash single_run.sh
```


## Self-improvement in ToolEVO
* Please `git clone` [Llama-Factory](https://github.com/hiyouga/LLaMA-Factory).
* Here is our parameters for training `./self_improvement.sh`
* We also provide our processed training data in `./train_data`
    * `llama3.json` is the training data for LLama3.
    * `qwen2.json` is the training data for Qwen2.


## Evaluate the performance on the test set
You can change `api_kernel_version=0 / 1 / 2` in `base_sample.sh` for $\mathcal{P}_c$ / $\mathcal{P}_{s_{\text{in}}}$ / $\mathcal{P}_{s_{\text{OOD}}}$.

### gpt_series model
```bash
cd ./inference_gpt/runs
bash gpt_easy.sh
bash gpt_hard.sh
```

### our model
```bash
cd ./inference/runs
bash easy.sh
bash hard.sh
```

## Others
* We provide the few-shot examples for ToolQA-D easy and hard in `./MCTS/src/few_shots`
* You can modify the prompt in `./MCTS/src/prompts.py`
* You can increase your own API version in `./MCTS/src/api_vary.py`.

# :heart: Acknowledgments

Special thanks to [ToolQA](https://arxiv.org/abs/2306.13304) and [Llama-Factory](https://arxiv.org/abs/2403.13372) for their valuable work.

# Citation
If you find this work useful in your research, please consider citing:
```bibtex
@article{DBLP:journals/corr/abs-2410-06617,
  author       = {Guoxin Chen and
                  Zhong Zhang and
                  Xin Cong and
                  Fangda Guo and
                  Yesai Wu and
                  Yankai Lin and
                  Wenzheng Feng and
                  Yasheng Wang},
  title        = {Learning Evolving Tools for Large Language Models},
  journal      = {CoRR},
  volume       = {abs/2410.06617},
  year         = {2024},
  url          = {https://doi.org/10.48550/arXiv.2410.06617},
  doi          = {10.48550/ARXIV.2410.06617},
  eprinttype    = {arXiv},
  eprint       = {2410.06617},
  timestamp    = {Mon, 18 Nov 2024 14:52:13 +0100},
  biburl       = {https://dblp.org/rec/journals/corr/abs-2410-06617.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```
