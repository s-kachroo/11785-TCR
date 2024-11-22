#!/bin/bash
#SBATCH --mem 50G
#SBATCH -n 1
#SBATCH --gres gpu:A100:1

#SBATCH --error=error_final_regular_finetune_4.log
#SBATCH --output=output_final_regular_finetune_4.log

#SBATCH --time 2-00:00:00 #Time for the job to run
#SBATCH --job-name RegFt4

##SBATCH -p requeue
#SBATCH -p gpu

##SBATCH -p xudong-gpu
##SBATCH -A xudong-lab

module load miniconda3

# Activate the Conda environment
source activate /home/yz3qt/data/miniconda/envs/splm

export TORCH_HOME=/home/yz3qt/data/torch_cache/
export HF_HOME=/home/yz3qt/data/transformers_cache/

python ./run.py --config_path ./config/final/final_regular_finetune_4.yaml --mode train --result_path ./result/final_regular/ || true
