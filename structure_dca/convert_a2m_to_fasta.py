import sys
import re

def a2m_to_fasta(input_file, output_file, gap_cutoff=0.2):
    titles = []
    seqs = []
    with open(input_file, "r") as ifile:
        for line in ifile:
            line = line.strip()
            if line.startswith(">"):
                titles.append(line)
                seqs.append("")
            else:
                seq = re.sub(r'[a-z]', '', line)
                seqs[-1] += seq
                
    with open(output_file, "w") as ofile:
        if len(titles) > 0:
            ofile.write(titles[0] + "\n")
            ofile.write(seqs[0] + "\n")
            
        out_count = 0
        for i in range(1, len(titles)):
            percent_of_gap = seqs[i].count("-") / len(seqs[i])
            if percent_of_gap > gap_cutoff or "X" in seqs[i]:
                continue
            ofile.write(titles[i] + "\n")
            ofile.write(seqs[i] + "\n")
            out_count += 1
            
    seq_lengths = set([len(i) for i in seqs])
    print("Seq length:", *seq_lengths)
    print(f"output/all: {out_count + 1}/{len(titles)}")

if __name__ == "__main__":
    # 检查命令行参数数量
    if len(sys.argv) < 3:
        print("Usage: python convert_a2m_to_fasta.py <input.a2m> <output.fasta> [gap_cutoff]")
        sys.exit(1)
        
    input_f = sys.argv[1]
    output_f = sys.argv[2]
    
    # 如果用户在命令行传入了第三个参数作为 cutoff，则使用传入值；否则默认 0.2
    cutoff = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
    
    a2m_to_fasta(input_f, output_f, cutoff)