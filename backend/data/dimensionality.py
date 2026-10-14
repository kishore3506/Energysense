import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from pathlib import Path

from config import DATASETS_DIR, DEFAULT_DATASET
from data.loader import load_dataset
from data.preprocessor import EnergyPreprocessor

def compute_pca_analysis(dataset_name: str = DEFAULT_DATASET, n_components: int = 6) -> Dict[str, Any]:
    """
    Computes Principal Component Analysis (PCA) on the engineered feature space.
    Returns:
    - Scree plot data (explained variance ratio per component)
    - Cumulative explained variance
    - 2D projection data (PC1 vs PC2) with energy target values
    - Feature loadings (component correlation / eigenvector weights)
    """
    dataset_path = DATASETS_DIR / dataset_name
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset '{dataset_name}' not found.")
        
    df, ts_col, target_col, _ = load_dataset(dataset_path)
    
    # Feature engineering
    prep = EnergyPreprocessor()
    engineered = prep.engineer_features(df, ts_col, target_col)
    
    # Exclude timestamp and isolate numeric features
    numeric_cols = [c for c in engineered.columns if c != ts_col and pd.api.types.is_numeric_dtype(engineered[c])]
    
    # Target feature
    y = engineered[target_col].values
    
    # Feature matrix without target
    X_cols = [c for c in numeric_cols if c != target_col]
    X = engineered[X_cols].values
    
    # Standardize features before PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit PCA
    k = min(n_components, X.shape[1], X.shape[0])
    pca = PCA(n_components=k, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    explained_var = [float(round(v * 100, 2)) for v in pca.explained_variance_ratio_]
    cumulative_var = [float(round(v * 100, 2)) for v in np.cumsum(pca.explained_variance_ratio_)]
    
    # Scree plot items
    scree = []
    for idx, (ev, cv) in enumerate(zip(explained_var, cumulative_var)):
        scree.append({
            "component": f"PC{idx + 1}",
            "explained_variance": ev,
            "cumulative_variance": cv
        })
        
    # Feature loadings (how much each original feature contributes to PC1 and PC2)
    loadings = []
    pc1_weights = pca.components_[0]
    pc2_weights = pca.components_[1] if k > 1 else np.zeros_like(pc1_weights)
    
    for feat_name, w1, w2 in zip(X_cols, pc1_weights, pc2_weights):
        loadings.append({
            "feature": feat_name,
            "pc1_loading": float(round(w1, 4)),
            "pc2_loading": float(round(w2, 4)),
            "importance": float(round(abs(w1) + abs(w2), 4))
        })
        
    loadings.sort(key=lambda x: x["importance"], reverse=True)
    
    # 2D projection sample (downsample to ~120 points for fast, responsive UI plotting)
    sample_step = max(1, len(X_pca) // 120)
    sampled_indices = range(0, len(X_pca), sample_step)
    
    projection_points = []
    ts_series = df[ts_col].astype(str)
    
    for idx in sampled_indices:
        projection_points.append({
            "timestamp": str(ts_series.iloc[idx]),
            "pc1": float(round(X_pca[idx, 0], 3)),
            "pc2": float(round(X_pca[idx, 1], 3)) if k > 1 else 0.0,
            "energy_target": float(round(y[idx], 2))
        })
        
    return {
        "dataset_name": dataset_name,
        "total_features_analyzed": len(X_cols),
        "total_components": k,
        "scree_data": scree,
        "feature_loadings": loadings[:15], # Top 15 contributors
        "projection_points": projection_points,
        "cumulative_variance_80": next((i + 1 for i, v in enumerate(cumulative_var) if v >= 80), k),
        "cumulative_variance_90": next((i + 1 for i, v in enumerate(cumulative_var) if v >= 90), k)
    }
