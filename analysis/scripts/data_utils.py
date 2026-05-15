import os
import glob
import pandas as pd
import numpy as np

SCORES = ['LigandMPNN_score', 'DCA_score', 'FoldX_ddG']

def get_ec_number(filename):
    filename_upper = filename.upper()
    ec_rules = {
        'AICDA': 3, 'AMIE': 3, 'CAS9': 3, 'PTEN': 3, 'RASH': 3, 
        'RNC': 3, 'PAFA': 3, 'LGK': 2, 'OTC': 2, 'SRC': 2, 
        'VKOR1': 1, 'RUBISCO': 4, '2024_01_30': 4
    }
    for keyword, ec_val in ec_rules.items():
        if keyword in filename_upper:
            return ec_val
    return 3

def get_raw_target_col(filename):
    filename_upper = filename.upper()
    if 'RUBISCO' in filename_upper: return 'Km_mean'
    if 'PAFA' in filename_upper: return 'kcat'
    if 'PTEN' in filename_upper:
        return 'DMS_score' if '2018' in filename_upper else 'Cum_score'
    return 'DMS_score'

def filter_single_mutations(df):
    if 'mutant' in df.columns:
        mask = df['mutant'].astype(str).str.match(r'^[A-Za-z]\s*\d+\s*[A-Za-z]$', na=False)
        return df[mask].copy()
    return df

def load_all_datasets(data_dir):
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    datasets = {}
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        raw_target = get_raw_target_col(file_name)
        try:
            df = pd.read_csv(file_path)
            cols_to_check = SCORES + ['Distance_to_Active_Site', raw_target]
            if not all(c in df.columns for c in cols_to_check): continue
            
            df = df.dropna(subset=cols_to_check)
            df = filter_single_mutations(df)
            for col in cols_to_check: df[col] = df[col].astype(float)
            
            final_target = raw_target
            if 'PAFA' in file_name.upper():
                df = df[df['kcat'] > 0].copy()
                df['lg_kcat'] = np.log10(df['kcat'])
                final_target = 'lg_kcat'
            elif 'RUBISCO' in file_name.upper() or '2024_01_30' in file_name.upper():
                df = df[df['Km_mean'] > 0].copy()
                df['neg_lg_Km'] = -np.log10(df['Km_mean'])
                final_target = 'neg_lg_Km'
            
            if len(df) > 0:
                datasets[file_name] = {'data': df, 'target': final_target, 'ec': get_ec_number(file_name)}
        except Exception as e:
            print(f"Error loading {file_name}: {e}")
    return datasets