#!/bin/bash
#SBATCH --job-name=run_sdca_dms
#SBATCH --partition=fat,q2,q5
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --output=sdca_dms_%j.out
#SBATCH --error=sdca_dms_%j.err

echo "Job started on $(hostname) at $(date)"

source /share/home/wangtb/miniconda3/etc/profile.d/conda.sh
conda activate ligandmpnn

python /share/home/wangtb/enzyme_shells/structure_dca/run_structure_dca.py

echo "All targets finished at $(date)"