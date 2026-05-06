#!/bin/bash
#SBATCH --job-name=foldx
#SBATCH --partition=gpu-2
#SBATCH --gres=gpu:1
#SBATCH --output=logs/foldx_%j.out
#SBATCH --error=logs/foldx_%j.err

source ~/.bashrc
conda activate predict

cd /lustre/home/tbwang/EnzymeShells/Enzyme_Shells/foldx

python /lustre/home/tbwang/EnzymeShells/Enzyme_Shells/foldx/generate_input.py

echo "Job Finished"