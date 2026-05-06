#!/bin/bash
#SBATCH --job-name=FX_AMIE
#SBATCH --partition=cu-1
#SBATCH --array=1-125
#SBATCH --output=logs/foldx_%A_%a.out
#SBATCH --error=logs/foldx_%A_%a.err

cd /share/home/wangtb/enzyme_shells/foldx/AMIE

mkdir -p logs
mkdir -p results_all

TASK_ID=$SLURM_ARRAY_TASK_ID
MUT_FILE="/share/home/wangtb/enzyme_shells/foldx/mutants/AMIE/mut_list_${TASK_ID}.txt"

if [ ! -f "$MUT_FILE" ]; then
    echo "错误：找不到文件 $MUT_FILE"
    exit 1
fi

TEMP_DIR="temp_task_${TASK_ID}"
mkdir -p ${TEMP_DIR}

cp /share/home/wangtb/enzyme_shells/structure/AMIE.pdb ${TEMP_DIR}/
cp ${MUT_FILE} ${TEMP_DIR}/individual_list.txt

cd ${TEMP_DIR}

/share/home/wangtb/foldx/foldx_20270131 --command=BuildModel \
      --pdb=AMIE.pdb \
      --pdb-dir=./ \
      --mutant-file=individual_list.txt \
      --numberOfRuns=1 \
      --output-dir=./

DIF_FILE="Dif_AMIE.fxout"

if [ -f "$DIF_FILE" ]; then
    head -n 1 "$DIF_FILE" > ../results_all/FoldX_header.txt

    tail -n +2 "$DIF_FILE" > data_without_header.txt

    paste individual_list.txt data_without_header.txt > ../results_all/mapped_result_${TASK_ID}.tsv

    echo "任务 ${TASK_ID} 结果提取成功，已映射突变信息。"
else
    echo "警告：任务 ${TASK_ID} 未生成 $DIF_FILE"
fi

cd ..
rm -rf ${TEMP_DIR}
