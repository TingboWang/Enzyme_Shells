import os
import glob
import csv
from structuredca import StructureDCA

# --- 路径配置 ---
STRUCTURE_DIR = "/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/structure"
RESULT_ROOT = "/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/structure_dca"
ORIG_FASTA_DIR = "/lustre/home/tbwang/EnzymeShells/Enzyme_Shells/fasta"  # 新增：原始 FASTA 文件夹

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

def get_wt_seq(msa_path):
    with open(msa_path, "r") as f:
        # 跳过第一行的 title (例如 >WT)
        f.readline()
        # 读取第二行的序列内容
        wt_seq = f.readline().strip()
    return wt_seq

def patch_msa_for_target(orig_fasta_path, raw_msa_path, patched_msa_path):
    # 1. 提取真实的 WT 纯序列
    with open(orig_fasta_path, "r") as f:
        f.readline()  # 跳过标题
        true_wt_seq = "".join(line.strip() for line in f)

    # 2. 读取当前生成的 MSA
    titles = []
    seqs = []
    with open(raw_msa_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                titles.append(line)
                seqs.append("")
            else:
                seqs[-1] += line

    if not titles:
        return False

    # 3. 寻找与真实 WT 匹配的序列 (去除 gap 后一致)
    wt_idx = 0  # 默认第一条
    for i, s in enumerate(seqs):
        if s.replace("-", "").replace(".", "").upper() == true_wt_seq.upper():
            wt_idx = i
            break

    # 4. 强行移动到第一位 (如果它本来不在第一位)
    if wt_idx != 0:
        titles.insert(0, titles.pop(wt_idx))
        seqs.insert(0, seqs.pop(wt_idx))

    # 5. 找到基准序列中的所有 Gap，并在整个 MSA 中全局删除这些列
    wt_aligned = seqs[0]
    gap_indices = {i for i, char in enumerate(wt_aligned) if char in ['-', '.']}

    if gap_indices:
        print(f"  [修复] 在基准序列中发现 {len(gap_indices)} 个占位 Gap。正在全局剔除以严格对齐 PDB...")
        for i in range(len(seqs)):
            # 仅保留不是基准 gap 的列
            seqs[i] = "".join([char for idx, char in enumerate(seqs[i]) if idx not in gap_indices])

    # 6. 重命名首序列标题，确保规范
    titles[0] = ">WT_TARGET"

    # 7. 保存修复后的完美 MSA
    with open(patched_msa_path, "w") as f:
        for t, s in zip(titles, seqs):
            f.write(t + "\n" + s + "\n")

    return True

def main():
    pdb_files = glob.glob(os.path.join(STRUCTURE_DIR, "*.pdb"))
    
    for pdb_path in pdb_files:
        file_name = os.path.basename(pdb_path)
        prefix = file_name.replace(".pdb", "")
        
        # 构建所有相关文件的路径
        work_dir = os.path.join(RESULT_ROOT, prefix)
        orig_fasta_path = os.path.join(ORIG_FASTA_DIR, f"{prefix}.fasta")
        raw_msa_path = os.path.join(work_dir, f"{prefix}.hmmer.fasta")
        patched_msa_path = os.path.join(work_dir, f"{prefix}.patched.fasta") # 修复后的 MSA
        out_csv = os.path.join(work_dir, f"{prefix}_dms_scores.csv")
        
        print("="*50)
        print(f"开始处理靶标: {prefix}")
        
        if not os.path.exists(raw_msa_path):
            print(f"  找不到对应的原始 MSA 文件: {raw_msa_path}，跳过该蛋白。")
            continue
            
        if not os.path.exists(orig_fasta_path):
            print(f"  找不到对应的原始 FASTA 文件: {orig_fasta_path}，跳过该蛋白。")
            continue

        # --- 新增：自动修复 MSA ---
        print("  正在校准并修复 MSA 矩阵对齐...")
        success = patch_msa_for_target(orig_fasta_path, raw_msa_path, patched_msa_path)
        if not success:
            print("  [错误] MSA 修复失败，跳过。")
            continue
            
        # 动态判定 pLDDT 过滤
        if "RUBISCO" in prefix.upper():
            use_plddt = False
            print("  真实结构 (RUBISCO)，已关闭 pLDDT 过滤。")
        else:
            use_plddt = True
            print("  预测结构，已开启 pLDDT 过滤。")
            
        print("  正在初始化模型 (推断参数中)...")
        try:
            sdca = StructureDCA(
                msa_path=patched_msa_path, # <--- 注意这里改成了 patched_msa_path
                pdb_path=pdb_path,
                chains='A', 
                distance_cutoff=8.0, 
                use_contacts_plddt_filter=use_plddt,
                contacts_plddt_cutoff=70.0,
                verbose=False
            )
        except Exception as e:
            print(f"  模型初始化失败: {e}")
            continue

        # 从修复后的 MSA 中提取，确保绝对纯净
        wt_seq = get_wt_seq(patched_msa_path) 
        seq_len = len(wt_seq)
        print(f"  提取到精准 WT 序列，长度: {seq_len} aa. 开始全位点扫描...")
        
        results = []
        for i, wt_aa in enumerate(wt_seq):
            pos = i + 1
            for mut_aa in AMINO_ACIDS:
                if wt_aa == mut_aa:
                    continue
                
                mut_str = f"{wt_aa}{pos}{mut_aa}"
                
                dE_raw = sdca.eval_mutation(mut_str, reweight_by_rsa=False)
                dE_rsa = sdca.eval_mutation(mut_str, reweight_by_rsa=True)
                
                results.append({
                    "mutation": mut_str,
                    "position": pos,
                    "wt_aa": wt_aa,
                    "mut_aa": mut_aa,
                    "dca_score_raw": round(dE_raw, 4),
                    "dca_score_rsa_reweight": round(dE_rsa, 4)
                })
                
        print(f"  扫描完成，共产生 {len(results)} 个突变评分。正在写入 CSV...")
        with open(out_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["mutation", "position", "wt_aa", "mut_aa", "dca_score_raw", "dca_score_rsa_reweight"])
            writer.writeheader()
            writer.writerows(results)
            
        print(f"  结果已保存至: {out_csv}")

if __name__ == "__main__":
    main()