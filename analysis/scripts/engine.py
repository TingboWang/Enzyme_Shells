import numpy as np
import pandas as pd
from sklearn.preprocessing import QuantileTransformer
from scipy.optimize import minimize
from scipy.stats import spearmanr
import warnings
from joblib import Parallel, delayed

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

def run_cross_validation(
    datasets,
    predict_fn,
    objective_fn,
    p0,
    scores_cols,
    alpha=0.1
):
    dataset_names = list(datasets.keys())

    def process_single_train_set(train_name):
        print(f"正在启动任务：{train_name}")
        
        train_info = datasets[train_name]
        df_train = train_info['data']
        target_train = train_info['target']
        
        qt_X = QuantileTransformer(
            output_distribution='normal',
            random_state=42,
            n_quantiles=min(1000, len(df_train))
        )
        X_train = qt_X.fit_transform(df_train[scores_cols])

        d_raw_train = df_train['Distance_to_Active_Site'].values
        d_train = d_raw_train / np.max(d_raw_train) if np.max(d_raw_train) != 0 else d_raw_train

        qt_y = QuantileTransformer(
            output_distribution='normal',
            random_state=42,
            n_quantiles=min(1000, len(df_train))
        )
        y_train = qt_y.fit_transform(df_train[[target_train]]).ravel()

        res = minimize(
            objective_fn,
            p0,
            args=(d_train, X_train, y_train, predict_fn, alpha),
            method='L-BFGS-B',
            options={'maxiter': 100, 'disp': False}
        )
        p_opt = res.x
        
        if not res.success:
            print(f"警告: {train_name} 优化未完全收敛: {res.message}")
        local_results = []
        for test_name in dataset_names:
            test_info = datasets[test_name]
            df_test = test_info['data']
            target_test = test_info['target']

            X_test = qt_X.transform(df_test[scores_cols])
            
            d_raw_test = df_test['Distance_to_Active_Site'].values
            d_test = d_raw_test / np.max(d_raw_test) if np.max(d_raw_test) != 0 else d_raw_test

            y_true = df_test[target_test].values
            y_pred = predict_fn(p_opt, d_test, X_test)

            r, p_val = spearmanr(y_true, y_pred)
            if np.isnan(r): r = 0.0
            if np.isnan(p_val): p_val = 1.0

            local_results.append({
                'Train_Dataset': train_name,
                'Test_Dataset': test_name + (' (Train Set)' if test_name == train_name else ''),
                'Spearman_r': r,
                'p_value': p_val,
                'Optimization_Success': res.success,
                'Objective_Value': res.fun,
                'Params': np.round(p_opt, 4)
            })
        return local_results

    results_nested = Parallel(n_jobs=16)(
        delayed(process_single_train_set)(name) for name in dataset_names
    )

    results_list = [item for sublist in results_nested for item in sublist]

    return pd.DataFrame(results_list)