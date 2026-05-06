#!/bin/bash
#SBATCH --job-name=Repair_PDB
#SBATCH --partition=cu-1
#SBATCH --array=0-11
#SBATCH --output=logs/repair_%A_%a.out
#SBATCH --error=logs/repair_%A_%a.err

INPUT_DIR="/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/structure"
OUTPUT_DIR="/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/foldx/repaired_structure"
FOLDX_EXE="/lustre/home/tbwang/foldx/foldx" 

mkdir -p ${OUTPUT_DIR}

PDB_FILES=(${INPUT_DIR}/*.pdb)
CURRENT_PDB=${PDB_FILES[$SLURM_ARRAY_TASK_ID]}
PDB_NAME=$(basename $CURRENT_PDB)
BASENAME="${PDB_NAME%.pdb}"

echo "=========================================================="
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Processing File: $PDB_NAME"
echo "=========================================================="


TASK_TEMP_DIR="${OUTPUT_DIR}/temp_task_${SLURM_ARRAY_TASK_ID}"
mkdir -p ${TASK_TEMP_DIR}

${FOLDX_EXE} --command=RepairPDB \
      --pdb-dir=${INPUT_DIR} \
      --pdb=${PDB_NAME} \
      --output-dir=${TASK_TEMP_DIR}

REPAIRED_FILE="${TASK_TEMP_DIR}/${BASENAME}_Repair.pdb"
FINAL_FILE="${OUTPUT_DIR}/${PDB_NAME}"

if [ -f "$REPAIRED_FILE" ]; then
    mv "$REPAIRED_FILE" "$FINAL_FILE"
    echo "成功: 修复完成并重命名为 $FINAL_FILE"
else
    echo "警告: 未找到预期的输出文件 $REPAIRED_FILE，FoldX 可能运行失败。"
fi

rm -rf ${TASK_TEMP_DIR}