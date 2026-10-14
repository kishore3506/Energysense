import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface DatasetSummary {
  total_rows: number;
  total_columns: number;
  timestamp_column: string;
  target_column: string;
  columns: string[];
  start_time: string;
  end_time: string;
  estimated_frequency: string;
  dataset_name: string;
  metrics: {
    mean: number;
    std: number;
    min: number;
    max: number;
    median: number;
    p25: number;
    p75: number;
    peak_value: number;
    peak_timestamp: string;
  };
  missing_values: Record<string, number>;
  warnings?: string[];
}

export interface DatasetPreview {
  dataset_name: string;
  timestamp_column: string;
  target_column: string;
  columns: string[];
  total_rows: number;
  preview_limit: number;
  rows: Record<string, any>[];
  warnings: string[];
}

export interface DatasetItem {
  name: string;
  size_kb: number;
  is_active: boolean;
}

export interface ModelMetricsResponse {
  active_model_type: string;
  latest_metrics: {
    id: number;
    model_name: string;
    model_type: string;
    dataset_name: string;
    trained_at: string;
    epochs: number;
    batch_size: number;
    lookback: number;
    horizon: number;
    train_loss: number;
    val_loss: number;
    test_mae: number;
    test_rmse: number;
    test_r2: number;
    test_mape: number;
    baseline_mae: number;
    baseline_rmse: number;
    baseline_r2: number;
    baseline_mape: number;
    loss_history: {
      epoch: number;
      train_loss: number;
      val_loss: number;
      train_mae: number;
      val_mae: number;
    }[];
  } | null;
  active_test_metrics: {
    mae: number;
    rmse: number;
    r2: number;
    mape: number;
    max_error: number;
  } | null;
  active_baseline_metrics: {
    mae: number;
    rmse: number;
    r2: number;
    mape: number;
    max_error: number;
  } | null;
  chart_samples: {
    timestamp: string;
    actual: number;
    predicted: number;
    baseline: number;
    error: number;
  }[];
  definitions: Record<string, {
    name: string;
    formula: string;
    unit: string;
    interpretation: string;
  }>;
  history: any[];
}

export interface ForecastResponse {
  forecast_id: number;
  dataset_name: string;
  model_type: string;
  lookback: number;
  horizon: number;
  summary: {
    mean_forecast: number;
    peak_forecast: number;
    peak_time: string;
    total_forecast: number;
    recent_historical_mean: number;
    percentage_change: number;
    target_column: string;
    unit: string;
  };
  predictions: {
    step: number;
    timestamp: string;
    predicted: number;
    baseline: number;
    unit: string;
  }[];
  historical_context: {
    timestamp: string;
    actual: number;
  }[];
}

export interface EnergyInsightsResponse {
  dataset_name: string;
  target_column: string;
  statistics: {
    mean: number;
    max: number;
    min: number;
    total: number;
    peak_to_average_ratio: number;
    weekday_mean: number;
    weekend_mean: number;
    weekend_difference_pct: number;
    total_anomalies_detected: number;
  };
  peak_hours: number[];
  trough_hours: number[];
  hourly_breakdown: {
    hour: number;
    label: string;
    mean: number;
    max: number;
    min: number;
  }[];
  daily_breakdown: {
    day: string;
    mean: number;
    max: number;
    total: number;
  }[];
  spikes: {
    timestamp: string;
    value: number;
    expected_mean: number;
    deviation_pct: number;
    z_score: number;
  }[];
  recommendations: {
    id: string;
    category: string;
    severity: 'High' | 'Medium' | 'Low';
    title: string;
    observation: string;
    suggestion: string;
    potential_impact: string;
  }[];
}

export interface PcaResponse {
  dataset_name: string;
  total_features_analyzed: number;
  total_components: number;
  scree_data: {
    component: string;
    explained_variance: number;
    cumulative_variance: number;
  }[];
  feature_loadings: {
    feature: string;
    pc1_loading: number;
    pc2_loading: number;
    importance: number;
  }[];
  projection_points: {
    timestamp: string;
    pc1: number;
    pc2: number;
    energy_target: number;
  }[];
  cumulative_variance_80: number;
  cumulative_variance_90: number;
}

export interface BenchmarkResponse {
  dataset_name: string;
  mean_actual_load: number;
  benchmark_table: {
    model_name: string;
    category: string;
    mae: number;
    rmse: number;
    cv_rmse: number;
    r2: number;
    mape: number;
    error_reduction_vs_baseline: number;
    is_best: boolean;
  }[];
  paper_citation: {
    title: string;
    authors: string;
    journal: string;
    year: number;
    reported_paper_results: string;
  };
}

export interface ErrorAnalysisResponse {
  dataset_name: string;
  sample_count: number;
  statistical_moments: {
    mean_bias: number;
    std_error: number;
    skewness: number;
    is_unbiased: boolean;
  };
  diurnal_error_profile: {
    hour: number;
    label: string;
    mean_error: number;
    count: number;
  }[];
  residual_scatter: {
    predicted: number;
    residual: number;
    actual: number;
  }[];
  extreme_failure_cases: {
    timestamp: string;
    actual: number;
    predicted: number;
    absolute_error: number;
    percentage_error: number;
  }[];
}

export interface TuningStatusResponse {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  model_type: string;
  dataset_name: string;
  total_trials: number;
  trials: {
    trial_number: number;
    lookback: number;
    lstm_units: number;
    dropout: number;
    learning_rate: number;
    batch_size: number;
    val_loss: number;
    is_best: boolean;
  }[];
  best_params: Record<string, any> | null;
  best_val_loss: number | null;
  error?: string | null;
}

export const getHealth = async () => (await api.get('/health')).data;
export const getDatasetList = async () => (await api.get<{ datasets: DatasetItem[]; active: string }>('/dataset/list')).data;
export const selectDataset = async (dataset_name: string) => (await api.post(`/dataset/select?dataset_name=${encodeURIComponent(dataset_name)}`)).data;
export const getDatasetSummary = async (dataset_name?: string) => (await api.get<DatasetSummary>(`/dataset/summary`, { params: { dataset_name } })).data;
export const getDatasetPreview = async (dataset_name?: string, limit = 50) => (await api.get<DatasetPreview>(`/dataset/preview`, { params: { dataset_name, limit } })).data;
export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return (await api.post('/dataset/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })).data;
};

export const startTraining = async (params: {
  dataset_name?: string;
  model_type: string;
  lookback: number;
  horizon: number;
  epochs: number;
  batch_size: number;
  learning_rate: number;
  lstm_units: number[];
  dropout: number;
}) => (await api.post('/model/train', params)).data;

export const getTrainingStatus = async (job_id: string) => (await api.get(`/model/status/${job_id}`)).data;
export const getModelMetrics = async (model_type?: string) => (await api.get<ModelMetricsResponse>('/model/metrics', { params: { model_type } })).data;
export const runForecast = async (params: {
  dataset_name?: string;
  horizon: number;
  lookback: number;
  model_type: string;
}) => (await api.post<ForecastResponse>('/forecast', params)).data;
export const getForecastHistory = async (limit = 20) => (await api.get('/forecast/history', { params: { limit } })).data;
export const getEnergyInsights = async (dataset_name?: string) => (await api.get<EnergyInsightsResponse>('/insights', { params: { dataset_name } })).data;
export const getExportCsvUrl = (forecast_id?: number) => `/api/forecast/export${forecast_id ? `?forecast_id=${forecast_id}` : ''}`;

export const getPcaAnalysis = async (dataset_name?: string) => (await api.get<PcaResponse>('/dataset/pca', { params: { dataset_name } })).data;
export const startTuning = async (params: { dataset_name?: string; model_type: string; n_trials: number; epochs_per_trial?: number }) => (await api.post('/model/tune', params)).data;
export const getTuningStatus = async (job_id: string) => (await api.get<TuningStatusResponse>(`/model/tune/status/${job_id}`)).data;
export const getBenchmark = async (dataset_name?: string) => (await api.get<BenchmarkResponse>('/model/benchmark', { params: { dataset_name } })).data;
export const getErrorAnalysis = async (dataset_name?: string) => (await api.get<ErrorAnalysisResponse>('/model/error-analysis', { params: { dataset_name } })).data;

export default api;
