timestamp=$( date +"%Y%m%d_%H%M%S")

echo $timestamp

mkdir -p ./logs

temperature=0.5
frequency_penalty=1.2
max_iter=12
# max_depth=12

CUDA_VISIBLE_DEVICES="1" bash base_sample.sh toolqa_hard agenda-hard 1 $temperature $frequency_penalty $max_iter > ./logs/agenda-hard_$timestamp.log 2>&1 &
sleep 20

CUDA_VISIBLE_DEVICES="2" bash base_sample.sh toolqa_hard airbnb-hard 1 $temperature $frequency_penalty $max_iter> ./logs/airbnb-hard_$timestamp.log 2>&1 &
sleep 20

CUDA_VISIBLE_DEVICES="3" bash base_sample.sh toolqa_hard coffee-hard 1 $temperature $frequency_penalty $max_iter> ./logs/coffee-hard_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="4" bash base_sample.sh toolqa_hard dblp-hard 1 $temperature $frequency_penalty $max_iter > ./logs/dblp-hard_$timestamp.log 2>&1 &
sleep 20

CUDA_VISIBLE_DEVICES="5" bash base_sample.sh toolqa_hard yelp-hard 1 $temperature $frequency_penalty $max_iter> ./logs/yelp-hard_2_$timestamp.log 2>&1 &
sleep 20

CUDA_VISIBLE_DEVICES="6" bash base_sample.sh toolqa_hard yelp-hard 1 $temperature $frequency_penalty $max_iter > ./logs/yelp-hard_$timestamp.log 2>&1 &
sleep 20

CUDA_VISIBLE_DEVICES="7" bash base_sample.sh toolqa_hard airbnb-hard 1 $temperature $frequency_penalty $max_iter> ./logs/airbnb-hard_2_$timestamp.log 2>&1 &
sleep 20
wait