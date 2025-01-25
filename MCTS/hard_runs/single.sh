timestamp=$( date +"%Y%m%d_%H%M%S")

echo $timestamp

mkdir -p ./logs

temperature=0.5
frequency_penalty=1.2
max_iter=12
# max_depth=12

CUDA_VISIBLE_DEVICES="1" bash base_sample.sh toolqa_hard dblp-hard 1 $temperature $frequency_penalty $max_iter > ./logs/dblp-hard_$timestamp.log 2>&1 &
sleep 20


wait