timestamp=$( date +"%Y%m%d_%H%M%S")

echo $timestamp

mkdir -p ./logs

temperature=0.5
frequency_penalty=1.2
max_iter=12

CUDA_VISIBLE_DEVICES="1" bash base_sample.sh toolqa_easy agenda-easy 1 $temperature $frequency_penalty $max_iter > ./logs/agenda-easy_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="2" bash base_sample.sh toolqa_easy airbnb-easy 1 $temperature $frequency_penalty $max_iter> ./logs/airbnb-easy_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="3" bash base_sample.sh toolqa_easy coffee-easy 1 $temperature $frequency_penalty $max_iter> ./logs/coffee-easy_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="4" bash base_sample.sh toolqa_easy dblp-easy 1 $temperature $frequency_penalty $max_iter > ./logs/dblp-easy_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="5" bash base_sample.sh toolqa_easy yelp-easy 1 $temperature $frequency_penalty $max_iter> ./logs/yelp-easy_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="6" bash base_sample.sh toolqa_easy flights-easy 1 $temperature $frequency_penalty $max_iter > ./logs/flights-easy_$timestamp.log 2>&1 &
sleep 10

CUDA_VISIBLE_DEVICES="7" bash base_sample.sh toolqa_easy scirex-easy 1 $temperature $frequency_penalty $max_iter> ./logs/scirex-easy_$timestamp.log 2>&1 &
sleep 10
wait