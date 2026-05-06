#!/bin/bash

IN_DIR="/share/home/wangtb/enzyme_shells/structure"
OUT_BASE_DIR="/share/home/wangtb/enzyme_shells/mpnn"

mkdir -p "$OUT_BASE_DIR"

shopt -s nullglob

for struct_path in "$IN_DIR"/*.pdb "$IN_DIR"/*.cif; do
    filename=$(basename -- "$struct_path")
    id="${filename%.*}"
    
    out_folder="$OUT_BASE_DIR/$id"
    mkdir -p "$out_folder"

    echo "▶️ 正在处理: $id ($filename)"
    
    python score.py \
        --model_type "ligand_mpnn" \
        --checkpoint_ligand_mpnn "./model_params/ligandmpnn_v_32_020_25.pt" \
        --seed 111 \
        --single_aa_score 1 \
        --pdb_path "$struct_path" \
        --out_folder "$out_folder" \
        --use_sequence 1 \
        --batch_size 1 \
        --number_of_batches 1
        
    echo "✅ $id 处理完成！结果已保存至: $out_folder"
    echo "------------------------------------------------------------"
done

shopt -u nullglob

echo "🎉 所有结构批量打分完毕！"