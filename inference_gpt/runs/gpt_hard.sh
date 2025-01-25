timestamp=$(date +"%Y%m%d_%H%M%S")
echo $timestamp

mkdir -p ./logs

ckpt_list=(
    gpt-3.5-turbo-0125
    gpt-4o-2024-08-06
    gpt-4o-mini  # gpt-4o-mini-2024-07-18
    claude-3-5-sonnet-20240620
    gpt-4-turbo-2024-04-09
)

api_kernel_version=0

# task=toolqa_easy
# dataname_lists="agenda-easy,airbnb-easy,coffee-easy,dblp-easy,flights-easy,scirex-easy,yelp-easy"

task=toolqa_hard
dataname_lists="agenda-hard,airbnb-hard,coffee-hard,dblp-hard,flights-hard,scirex-hard,yelp-hard"


sft_prompt=False

# ckpt的数量
num_ckpt=${#ckpt_list[@]}
for ((i=0;i<$num_ckpt;i++))
do
    # 取出第i个元素
    ckpt=${ckpt_list[$i]}
    # ckpt_dirname=$(basename "$(dirname "$ckpt")")
    # ckpt_basename=$(basename "$ckpt")
    bash pretrain_base_sample.sh $task $dataname_lists "$ckpt" $sft_prompt $api_kernel_version > "./logs/${ckpt}_${timestamp}.log" 2>&1 &
    sleep 10
    wait
done
wait
