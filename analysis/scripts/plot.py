import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_cv_results(csv_path, save_path=None):
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['pdf.fonttype'] = 42
    
    FONT_TITLE = 10
    FONT_LABEL = 9
    FONT_TICK = 8
    
    sns.set_theme(style="ticks", font_scale=1)
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: 找不到文件 {csv_path}")
        return

    df['Train_Dataset'] = df['Train_Dataset'].str.replace('.csv', '', regex=False)
    df['Test_Dataset'] = df['Test_Dataset'].str.replace('.csv', '', regex=False)
    df_cv = df[~df['Test_Dataset'].str.contains('Train Set', na=False)].copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=150)

    df_heatmap = df.copy()
    df_heatmap['Test_Dataset'] = df_heatmap['Test_Dataset'].str.replace(' (Train Set)', '', regex=False)
    pivot_df = df_heatmap.pivot(index='Train_Dataset', columns='Test_Dataset', values='Spearman_r')
    
    sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap="coolwarm", center=0, 
                square=True, linewidths=.3, ax=ax1,
                annot_kws={"size": 7}, 
                cbar_kws={"shrink": 0.7, "label": "Spearman $r$"})
    
    ax1.set_title("Cross-Validation Matrix", fontsize=FONT_TITLE, fontweight='bold')
    ax1.set_xlabel("Test Dataset", fontsize=FONT_LABEL)
    ax1.set_ylabel("Train Dataset", fontsize=FONT_LABEL)
    ax1.tick_params(labelsize=FONT_TICK, rotation=45)

    if not df_cv.empty:
        order = df_cv.groupby('Train_Dataset')['Spearman_r'].median().sort_values(ascending=False).index
        
        sns.boxplot(x='Train_Dataset', y='Spearman_r', data=df_cv, order=order, 
            hue='Train_Dataset', palette="RdYlBu_r", legend=False, 
            showfliers=False, ax=ax2, width=0.6, linewidth=1)
        
        sns.stripplot(x='Train_Dataset', y='Spearman_r', data=df_cv, order=order, 
                      color=".2", alpha=0.5, size=3, jitter=True, ax=ax2)
        
        ax2.axhline(0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
        ax2.set_title("Generalization Power", fontsize=FONT_TITLE, fontweight='bold')
        ax2.set_xlabel("Training Dataset", fontsize=FONT_LABEL)
        ax2.set_ylabel("Spearman $r$ (Independent)", fontsize=FONT_LABEL)
        ax2.tick_params(labelsize=FONT_TICK, rotation=45)

    plt.tight_layout()
    
    plt.show()



def compare_cv_results(path_a, path_b, save_path=None):

    sns.set_theme(style="whitegrid", font_scale=1.0)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    
    name_a = os.path.basename(path_a).replace('.csv', '')
    name_b = os.path.basename(path_b).replace('.csv', '')

    def load_and_clean(path):
        df = pd.read_csv(path)
        df['Train_Dataset'] = df['Train_Dataset'].str.replace('.csv', '', regex=False)
        df['Test_Dataset'] = df['Test_Dataset'].str.replace('.csv', '', regex=False)\
                                               .str.replace(' (Train Set)', '', regex=False)
        return df

    df_a = load_and_clean(path_a)
    df_b = load_and_clean(path_b)

    df_merge = pd.merge(
        df_a[['Train_Dataset', 'Test_Dataset', 'Spearman_r']], 
        df_b[['Train_Dataset', 'Test_Dataset', 'Spearman_r']], 
        on=['Train_Dataset', 'Test_Dataset'], 
        suffixes=(f'_{name_a}', f'_{name_b}')
    )
    
    col_a = f'Spearman_r_{name_a}'
    col_b = f'Spearman_r_{name_b}'
    df_merge['Delta_r'] = df_merge[col_b] - df_merge[col_a]

    df_cv = df_merge[df_merge['Train_Dataset'] != df_merge['Test_Dataset']].copy()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), dpi=120)

    ax2 = axes[0]
    avg_delta = df_cv.groupby('Train_Dataset')['Delta_r'].mean().sort_values(ascending=False)
    colors = ['#4C72B0' if x > 0 else '#C44E52' for x in avg_delta.values]
    
    sns.barplot(x=avg_delta.index, y=avg_delta.values, palette=colors, ax=ax2)
    ax2.axhline(0, color='black', linewidth=0.8)
    ax2.set_title(f"Gain by Training Set\n({name_b} - {name_a})", fontweight='bold', fontsize=12)
    ax2.set_ylabel("Average $\Delta$ Spearman r")
    ax2.tick_params(axis='x', rotation=45, labelsize=9)

    ax3 = axes[1]
    df_long = pd.melt(df_cv, id_vars=['Train_Dataset', 'Test_Dataset'], 
                      value_vars=[col_a, col_b], var_name='Model', value_name='r')
    df_long['Model'] = df_long['Model'].str.replace('Spearman_r_', '')

    sns.boxplot(x='Model', y='r', data=df_long, palette="Pastel1", showfliers=False, ax=ax3, width=0.5)
    sns.stripplot(x='Model', y='r', data=df_long, color=".3", size=3, alpha=0.4, jitter=True, ax=ax3)
    ax3.set_title("Overall Distribution", fontweight='bold', fontsize=12)
    ax3.set_ylabel("Spearman r")

    plt.tight_layout()
    
    plt.show()