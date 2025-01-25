task=$1

arg2="$2"
IFS=',' read -r -a dataname_lists <<< "$arg2"
echo ${dataname_lists[@]}

checkpoint_dir=$3

sft_prompt=$4

api_kernel_version=$5

root_path=/your_root_path


python=/yourpython/tooldyna/bin/python

export VLLM_USE_MODELSCOPE="False"

debug_num=-1
output_dir=${root_path}/output_dir/greedy/run

seed=42

tool_url=http://xx.xxx.xxx.xx:5010/toolqa

# api_kernel_version=3
instruct=False

# 遍历数据集
for dataname in "${dataname_lists[@]}"  
do
    $python ../src/batch_search_generate.py \
        --debug_num $debug_num \
        --task $task \
        --dataname $dataname \
        --output_dir $output_dir \
        --seed $seed \
        --checkpoint_dir $checkpoint_dir \
        --sft_prompt $sft_prompt \
        --api_kernel_version $api_kernel_version \
        --instruct $instruct \
        --tool_url $tool_url
done



