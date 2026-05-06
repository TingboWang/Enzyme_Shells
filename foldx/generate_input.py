import pandas as pd
import os
import math
import glob

csv_dir = "/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/activity_data"
pdb_dir = "/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/structure"
output_base_dir = "/lustre/home/tbwang/foldx"
mutants_base_dir = os.path.join(output_base_dir, "mutants")
foldx_exe = "/lustre/home/tbwang/foldx/foldx"

chunk_size = 50
target_chain = "A"

csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    dataset_id = filename.replace('.csv', '')
    
    pdb_name = f"{dataset_id}.pdb"
    pdb_file = os.path.join(pdb_dir, pdb_name)
    
    if not os.path.exists(pdb_file):
        print(f"⚠️ 找不到对应的 PDB 文件: {pdb_file}，跳过 {dataset_id} ...")
        continue

    work_dir = os.path.join(output_base_dir, dataset_id)
    split_dir = os.path.join(mutants_base_dir, dataset_id)
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(split_dir, exist_ok=True)
    
    df = pd.read_csv(csv_file)
    if 'mutant' not in df.columns:
        print(f"⚠️ {dataset_id} 中不存在 mutant 列，跳过...")
        continue
        
    mutations = []
    for mut in df['mutant'].dropna():
        if mut != 'WT':
            wt_aa = mut[0]
            mut_aa = mut[-1]
            pos = mut[1:-1]
            foldx_mut = f"{wt_aa}{target_chain}{pos}{mut_aa};"
            mutations.append(foldx_mut)

    if not mutations:
        print(f"⚠️ {dataset_id} 中没有提取到有效突变，跳过...")
        continue

    num_chunks = math.ceil(len(mutations) / chunk_size)
    os.system(f"rm -f {split_dir}/mut_list_*.txt") 
    
    for i in range(1, num_chunks + 1):
        chunk_lines = mutations[(i-1)*chunk_size : i*chunk_size]
        with open(os.path.join(split_dir, f"mut_list_{i}.txt"), 'w') as f:
            f.write("\n".join(chunk_lines) + "\n")

    slurm_script_path = os.path.join(work_dir, "run_foldx.sh")
    slurm_content = f"""#!/bin/bash
#SBATCH --job-name=FX_{dataset_id[:10]}
#SBATCH --partition=cu-1
#SBATCH --array=1-{num_chunks}
#SBATCH --output=logs/foldx_%A_%a.out
#SBATCH --error=logs/foldx_%A_%a.err

cd {work_dir}

mkdir -p logs
mkdir -p results_all

TASK_ID=$SLURM_ARRAY_TASK_ID
MUT_FILE="{split_dir}/mut_list_${{TASK_ID}}.txt"

if [ ! -f "$MUT_FILE" ]; then
    echo "错误：找不到文件 $MUT_FILE"
    exit 1
fi

TEMP_DIR="temp_task_${{TASK_ID}}"
mkdir -p ${{TEMP_DIR}}

cp {pdb_file} ${{TEMP_DIR}}/
cp ${{MUT_FILE}} ${{TEMP_DIR}}/individual_list.txt

cd ${{TEMP_DIR}}

{foldx_exe} --command=BuildModel \\
      --pdb={pdb_name} \\
      --pdb-dir=./ \\
      --mutant-file=individual_list.txt \\
      --numberOfRuns=1 \\
      --output-dir=./

DIF_FILE="Dif_{dataset_id}.fxout"

if [ -f "$DIF_FILE" ]; then
    head -n 1 "$DIF_FILE" > ../results_all/FoldX_header.txt
    
    tail -n +2 "$DIF_FILE" > data_without_header.txt
    
    paste individual_list.txt data_without_header.txt > ../results_all/mapped_result_${{TASK_ID}}.tsv
    
    echo "任务 ${{TASK_ID}} 结果提取成功，已映射突变信息。"
else
    echo "警告：任务 ${{TASK_ID}} 未生成 $DIF_FILE"
fi

cd ..
rm -rf ${{TEMP_DIR}}
"""
    with open(slurm_script_path, 'w') as f:
        f.write(slurm_content)

    print(f"[成功] {dataset_id}: 生成 {num_chunks} 个任务，PDB={pdb_name}")

merge_script_path = os.path.join(output_base_dir, "merge_all_results.sh")
with open(merge_script_path, "w") as f:
    f.write("""#!/bin/bash
echo "🚀 开始合并所有蛋白的 FoldX 结果..."

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 遍历所有文件夹 (即各个 dataset_id)
for dir in */ ; do
    # 排除 mutants 文件夹和其他非任务文件夹
    if [ "$dir" == "mutants/" ]; then
        continue
    fi

    if [ -d "${dir}results_all" ]; then
        PROT_NAME=$(basename "$dir")
        echo "正在合并 ${PROT_NAME} ..."
        
        cd "$PROT_NAME"
        
        if [ -f "results_all/FoldX_header.txt" ]; then
            # 构造新的表头，加上 Mutation 列头
            echo -e "Mutation\t$(cat results_all/FoldX_header.txt)" > final_${PROT_NAME}_foldx.tsv
            
            # 将所有映射好的结果追加合并到最终文件里
            cat results_all/mapped_result_*.tsv >> final_${PROT_NAME}_foldx.tsv
            
            echo "✅ 成功: 已生成 ${PROT_NAME}/final_${PROT_NAME}_foldx.tsv"
        else
            echo "⚠️ 警告: ${PROT_NAME} 尚未生成结果，可能任务还在运行。"
        fi
        
        cd ..
    fi
done
echo "🎉 全部合并结束！您可以将各个 final_XXX_foldx.tsv 下载进行后续分析了。"
""")

os.chmod(merge_script_path, 0o755)

print("\n🎉 所有任务编排完成！")
print(f"👉 提示：当所有 Slurm 任务跑完后，请去 {output_base_dir} 运行 ./merge_all_results.sh 进行一键拼接！")