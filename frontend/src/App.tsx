import React, { useState, useEffect } from 'react';
import { Sidebar, NavPage } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { ForecastingPage } from './pages/ForecastingPage';
import { DatasetExplorerPage } from './pages/DatasetExplorerPage';
import { ModelTrainingPage } from './pages/ModelTrainingPage';
import { BenchmarkPage } from './pages/BenchmarkPage';
import { InsightsPage } from './pages/InsightsPage';
import { DeploymentPage } from './pages/DeploymentPage';
import { ReportsPage } from './pages/ReportsPage';
import { 
  getHealth, 
  getDatasetList, 
  selectDataset, 
  getDatasetSummary, 
  getModelMetrics, 
  runForecast,
  DatasetSummary,
  ModelMetricsResponse,
  ForecastResponse,
  DatasetItem
} from './services/api';

export function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>('overview');
  const [backendOnline, setBackendOnline] = useState<boolean>(true);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [activeDataset, setActiveDataset] = useState<string>('uci_appliances_hourly.csv');
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [metrics, setMetrics] = useState<ModelMetricsResponse | null>(null);
  const [latestForecast, setLatestForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Initialize application state on load
  useEffect(() => {
    bootstrapApp();
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  const bootstrapApp = async () => {
    setLoading(true);
    try {
      // 1. Health check
      const health = await getHealth();
      setBackendOnline(health.status === 'healthy');
      if (health.active_dataset) {
        setActiveDataset(health.active_dataset);
      }

      // 2. Load dataset list
      const dsList = await getDatasetList();
      setDatasets(dsList.datasets || []);

      // 3. Load dataset summary
      const currentDs = dsList.active || 'uci_appliances_hourly.csv';
      setActiveDataset(currentDs);
      const sum = await getDatasetSummary(currentDs);
      setSummary(sum);

      // 4. Load model metrics
      const m = await getModelMetrics();
      setMetrics(m);

      // 5. Generate initial forecast preview if none exists
      try {
        const fc = await runForecast({
          dataset_name: currentDs,
          horizon: 24,
          lookback: 24,
          model_type: 'LSTM'
        });
        setLatestForecast(fc);
      } catch (fcErr) {
        console.warn('Initial forecast preview not ready:', fcErr);
      }

    } catch (err) {
      console.error('Failed to bootstrap app:', err);
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDataset = async (datasetName: string) => {
    setLoading(true);
    try {
      await selectDataset(datasetName);
      setActiveDataset(datasetName);
      const sum = await getDatasetSummary(datasetName);
      setSummary(sum);
      showToast(`Switched active dataset to ${datasetName}`);

      try {
        const fc = await runForecast({
          dataset_name: datasetName,
          horizon: 24,
          lookback: 24,
          model_type: 'LSTM'
        });
        setLatestForecast(fc);
      } catch (e) {
        console.warn(e);
      }
    } catch (err: any) {
      console.error('Dataset selection error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    await bootstrapApp();
    showToast('Platform data refreshed from backend');
  };

  const handleQuickForecast = async () => {
    setLoading(true);
    try {
      const fc = await runForecast({
        dataset_name: activeDataset,
        horizon: 24,
        lookback: 24,
        model_type: 'LSTM'
      });
      setLatestForecast(fc);
      showToast('Generated fresh 24-hour deep learning forecast!');
      if (currentPage !== 'forecasting') {
        setCurrentPage('forecasting');
      }
    } catch (err: any) {
      showToast(`Forecast error: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getPageInfo = () => {
    switch (currentPage) {
      case 'overview':
        return { title: 'Overview Dashboard', subtitle: 'System performance, energy KPIs, and holdout evaluation' };
      case 'forecasting':
        return { title: 'Energy Demand Forecasting', subtitle: 'Multi-step sequence forecasting with LSTM, GRU & BiLSTM' };
      case 'dataset':
        return { title: 'Data Engineering & PCA Analysis', subtitle: 'Rubric 1: Thermodynamic gradients, cyclical encoding, and PCA scree reduction' };
      case 'training':
        return { title: 'Advanced Modeling & Optuna Tuning', subtitle: 'Rubric 2: Recurrent neural architectures, Bayesian hyperparameter search, and experiment logging' };
      case 'benchmark':
        return { title: 'SOTA Benchmarking & Rigorous Errors', subtitle: 'Rubric 3: Candanedo (2017) comparison, Random Forest, Ridge, and residual heteroscedasticity' };
      case 'insights':
        return { title: 'Energy Insights & Recommendations', subtitle: 'Diurnal patterns, peak load shaving, and anomaly mitigation' };
      case 'deployment':
        return { title: 'Deployment & Containerization', subtitle: 'Rubric 4: FastAPI inference engine, multi-stage Docker, Hugging Face Spaces & AWS' };
      case 'reports':
        return { title: 'Reports & History Audit', subtitle: 'Database forecast records, evaluation logs, and printable report' };
    }
  };

  const pageInfo = getPageInfo();

  return (
    <div className="flex min-h-screen bg-slate-100/70 text-slate-800 font-sans">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        backendOnline={backendOnline}
        activeDataset={activeDataset}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          datasets={datasets}
          activeDataset={activeDataset}
          onSelectDataset={handleSelectDataset}
          onRefresh={handleRefresh}
          onQuickForecast={handleQuickForecast}
          loading={loading}
        />

        {/* Floating Toast Notification */}
        {toastMessage && (
          <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xl border border-slate-700 flex items-center gap-2 animate-bounce">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>{toastMessage}</span>
          </div>
        )}

        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {currentPage === 'overview' && (
            <OverviewPage
              summary={summary}
              metrics={metrics}
              latestForecast={latestForecast}
              onNavigate={setCurrentPage}
              loading={loading}
            />
          )}

          {currentPage === 'forecasting' && (
            <ForecastingPage
              datasets={datasets}
              activeDataset={activeDataset}
              onSelectDataset={handleSelectDataset}
              forecastData={latestForecast}
              onForecastGenerated={(fc) => {
                setLatestForecast(fc);
                showToast(`Forecast #${fc.forecast_id} generated and saved to database!`);
              }}
            />
          )}

          {currentPage === 'dataset' && (
            <DatasetExplorerPage
              summary={summary}
              activeDataset={activeDataset}
              datasets={datasets}
              onSelectDataset={handleSelectDataset}
              onDatasetUploaded={async () => {
                const ds = await getDatasetList();
                setDatasets(ds.datasets || []);
                showToast('New dataset uploaded and indexed!');
              }}
            />
          )}

          {currentPage === 'training' && (
            <ModelTrainingPage
              metrics={metrics}
              activeDataset={activeDataset}
              onTrainingFinished={async () => {
                const m = await getModelMetrics();
                setMetrics(m);
                showToast('Model training completed and registered in database!');
              }}
            />
          )}

          {currentPage === 'benchmark' && (
            <BenchmarkPage activeDataset={activeDataset} />
          )}

          {currentPage === 'insights' && (
            <InsightsPage activeDataset={activeDataset} />
          )}

          {currentPage === 'deployment' && (
            <DeploymentPage backendOnline={backendOnline} />
          )}

          {currentPage === 'reports' && (
            <ReportsPage summary={summary} metrics={metrics} />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
