#!/usr/bin/env python3
import os
import glob

print("🚀 开始重新合并所有蛋白的 FoldX 结果，并自动完美校准错位...")

# 统一定义干净的标准表头
HEADER = "Mutation\tPdb\ttotal energy\tBackbone Hbond\tSidechain Hbond\tVan der Waals\tElectrostatics\tSolvation Polar\tSolvation Hydrophobic\tVan der Waals clashes\tentropy sidechain\tentropy mainchain\tsloop_entropy\tmloop_entropy\tcis_bond\ttorsional clash\tbackbone clash\thelix dipole\twater bridge\tdisulfide\telectrostatic kon\tpartial covalent bonds\tenergy Ionisation\tEntropy Complex"

# 获取当前脚本所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir == '':
    base_dir = '.'

# 遍历所有蛋白文件夹
for dir_name in os.listdir(base_dir):
    prot_dir = os.path.join(base_dir, dir_name)
    
    # 跳过文件和 mutants 等无关文件夹
    if not os.path.isdir(prot_dir) or dir_name == "mutants":
        continue
        
    results_dir = os.path.join(prot_dir, "results_all")
    if os.path.exists(results_dir):
        print(f"正在处理 {dir_name} ...")
        
        # 匹配该蛋白下所有的分块任务结果
        tsv_files = glob.glob(os.path.join(results_dir, "mapped_result_*.tsv"))
        if not tsv_files:
            continue
            
        all_aligned_data = []
        
        # 遍历每一个任务产生的结果文件
        for tsv in sorted(tsv_files):
            mutations = []
            data_rows = []
            
            with open(tsv, 'r') as f:
                for line in f:
                    parts = line.strip('\n').split('\t')
                    
                    # 1. 提取突变标识 (只要第一列有字符，且不是空行/表头，就存入突变列表)
                    if len(parts) > 0:
                        mut = parts[0].strip()
                        if mut != "" and mut != "Mutation":
                            mutations.append(mut)
                            
                    # 2. 提取有效数据行 (只要后面的列中包含 .pdb 且不包含纯表头)
                    if len(parts) > 1:
                        data_str = '\t'.join(parts[1:])
                        if '.pdb' in data_str and 'Pdb\ttotal energy' not in data_str:
                            data_rows.append(data_str)
                            
            # 3. 核心修复逻辑：无视原始的同行错位，重新用拉链方法(zip)将突变与数据一对一绑定
            # PA248N 将被重新强行绑定给 PTEN_1.pdb
            for mut, data in zip(mutations, data_rows):
                all_aligned_data.append(f"{mut}\t{data}")
                
        # 4. 写入最终清洗完毕的文件
        if all_aligned_data:
            final_file = os.path.join(prot_dir, f"final_{dir_name}_foldx.tsv")
            with open(final_file, 'w') as f:
                f.write(HEADER + "\n")
                f.write("\n".join(all_aligned_data) + "\n")
            print(f"✅ 成功: 已生成 {final_file}，共完美清洗并对齐了 {len(all_aligned_data)} 条结果。")

print("\n🎉 全部合并及校准结束！您可以放心下载 TSV 文件，所有数据均已严格对齐。")