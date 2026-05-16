#!/bin/bash
#SBATCH --job-name=run_sdca_dms
#SBATCH --partition=cu-1
#SBATCH --cpus-per-task=1
#SBATCH --output=sdca_dms_%j.out
#SBATCH --error=sdca_dms_%j.err

echo "Job started on $(hostname) at $(date)"

conda activate predict

python /lustre/home/tbwang/EnzymeShells/Enzyme_Shells/structure_dca/run_structure_dca.py

echo "All targets finished at $(date)"