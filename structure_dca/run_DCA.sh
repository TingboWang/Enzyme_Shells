#!/bin/bash
#SBATCH --job-name=enzymes_dca_hmmer
#SBATCH --partition=q2,q5,fat           # 优先使用空闲节点最多的 q2 分区
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --array=0-11                    # 核心修改：并行处理 12 个 fasta 文件
#SBATCH --output=logs/hmmer_%A_%a.out   # %A 为总作业号，%a 为数组索引
#SBATCH --error=logs/hmmer_%A_%a.err

echo "Job started on $(hostname) at $(date)"
mkdir -p logs

BASE_DIR="/share/home/wangtb/enzyme_shells/fasta"
RESULT_ROOT="/share/home/wangtb/enzyme_shells/structure_dca"
DB_PATH="/share/home/wangtb/UniRef/uniref100/uniref100.fasta" 
PY_CONVERT="/share/home/wangtb/enzyme_shells/structure_dca/convert_a2m_to_fasta.py"

FILES=("$BASE_DIR"/*.fasta)
INPUT_FASTA=${FILES[$SLURM_ARRAY_TASK_ID]}

FASTA_NAME=$(basename "$INPUT_FASTA")
PREFIX="${FASTA_NAME%.fasta}"

OUTPUT_DIR="$RESULT_ROOT/$PREFIX"
mkdir -p "$OUTPUT_DIR"

echo "------------------------------------------------"
echo "Processing $INPUT_FASTA (Array ID: $SLURM_ARRAY_TASK_ID)"
echo "Results will be saved to $OUTPUT_DIR"

source /share/home/wangtb/miniconda3/etc/profile.d/conda.sh
conda activate ligandmpnn


jackhmmer --cpu $SLURM_CPUS_PER_TASK -N 2 --incE 1e-7 \
    -o "$OUTPUT_DIR/${PREFIX}.o" \
    -A "$OUTPUT_DIR/${PREFIX}.A" \
    --tblout "$OUTPUT_DIR/${PREFIX}.tbl" \
    "$INPUT_FASTA" "$DB_PATH"


if [ -f "$OUTPUT_DIR/${PREFIX}.A" ]; then
    esl-reformat a2m "$OUTPUT_DIR/${PREFIX}.A" > "$OUTPUT_DIR/${PREFIX}.hmmer.a2m"
fi


if [ -f "$PY_CONVERT" ] && [ -f "$OUTPUT_DIR/${PREFIX}.hmmer.a2m" ]; then
    python "$PY_CONVERT" "$OUTPUT_DIR/${PREFIX}.hmmer.a2m" "$OUTPUT_DIR/${PREFIX}.hmmer.fasta"
else
    echo "Warning: $PY_CONVERT or .a2m file not found, skipping cleaning step."
fi

echo "Finished $PREFIX at $(date)"