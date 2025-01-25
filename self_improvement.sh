GPU_NUM=8
ADDR_PORT=12345

seed=42

export TOKENIZERS_PARALLELISM=false
export VLLM_USE_MODELSCOPE="False"

echo "Prepare the conda environment"

timestamp=$( date +"%Y%m%d_%H%M%S")
echo $timestamp


root_path=YOUR_ROOT_PATH
model_name_or_path=${root_path}/model_cache/Meta-Llama-3-8B


dataset=llama3
dataset_dir=${root_path}/train_data


finetuning_type=full
learning_rate=2e-5
per_device_train_batch_size=8
gradient_accumulation_steps=8

output_dir=${root_path}/output_dir/sft/Meta-Llama-3-8B/run/$timestamp
deepspeed_config_file=${root_path}/LLaMA-Factory/examples/deepspeed/ds_z2_config.json

deepspeed_env=/PATH/toolevo/bin/deepspeed

${deepspeed_env} --num_gpus ${GPU_NUM} ../src/train.py \
    --deepspeed ${deepspeed_config_file} \
    --stage sft \
    --do_train \
    --model_name_or_path ${model_name_or_path} \
    --dataset_dir ${dataset_dir}\
    --dataset ${dataset} \
    --template llama3 \
    --finetuning_type ${finetuning_type} \
    --save_safetensors \
    --output_dir ${output_dir} \
    --overwrite_cache \
    --max_length 1024 \
    --cutoff_len 1024 \
    --per_device_train_batch_size ${per_device_train_batch_size} \
    --gradient_accumulation_steps ${gradient_accumulation_steps} \
    --warmup_ratio 0.03 \
    --weight_decay 0. \
    --lr_scheduler_type cosine \
    --logging_steps 10 \
    --save_steps 20 \
    --learning_rate ${learning_rate} \
    --num_train_epochs 8.0 \
    --dataloader_num_workers 8 \
    --preprocessing_num_workers 16 \
    --ddp_timeout 180000000 \
    --seed $seed \
    --plot_loss \
    --save_only_model \
    --bf16