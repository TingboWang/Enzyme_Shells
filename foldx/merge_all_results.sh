#!/bin/bash
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
            echo -e "Mutation	$(cat results_all/FoldX_header.txt)" > final_${PROT_NAME}_foldx.tsv

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
