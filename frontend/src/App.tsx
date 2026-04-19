import { useEffect, useMemo, useState } from "react";
import { Layout } from "./components/Layout";
import { PresetSelector } from "./components/Sidebar/PresetSelector";
import { TickerInput } from "./components/Sidebar/TickerInput";
import { ParameterSliders } from "./components/Sidebar/ParameterSliders";
import { RunButton } from "./components/Sidebar/RunButton";
import { CompanyCard } from "./components/CompanyCard";
import { MetricGrid } from "./components/MetricGrid";
import { LossHistogram } from "./components/LossHistogram";
import { TrancheChart } from "./components/TrancheChart";
import { CorrelationSensitivity } from "./components/CorrelationSensitivity";
import { JointDefaultHeatmap } from "./components/JointDefaultHeatmap";
import { StressTable } from "./components/StressTable";
import { SystemLog } from "./components/SystemLog";
import { useDebouncedValue } from "./hooks/useDebouncedValue";
import {
  analyzePortfolio,
  buildCorrelationSeries,
  extractErrorMessage,
  fetchMerton,
  fetchPreset,
  priceTranches,
  runStress,
} from "./lib/api";
import { formatCurrency } from "./lib/format";
import type {
  CompanyResult,
  CorrelationPoint,
  MertonResponse,
  PortfolioName,
  PortfolioResponse,
  StressResponse,
  TranchePoint,
  TrancheResponse,
} from "./types/api";

const defaultTranches: TranchePoint[] = [
  { attachment: 0, detachment: 0.03 },
  { attachment: 0.03, detachment: 0.07 },
  { attachment: 0.07, detachment: 1 },
];

function App() {
  const [activePreset, setActivePreset] = useState("ig");
  const [portfolio, setPortfolio] = useState<PortfolioName[]>([]);
  const [rho, setRho] = useState(0.2);
  const [confidence, setConfidence] = useState(0.99);
  const [nSim, setNSim] = useState(50000);
  const [stressedRho, setStressedRho] = useState(0.5);
  const [pdMultiplier, setPdMultiplier] = useState(2);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioResponse | null>(null);
  const [trancheResult, setTrancheResult] = useState<TrancheResponse | null>(null);
  const [stressResult, setStressResult] = useState<StressResponse | null>(null);
  const [correlationSeries, setCorrelationSeries] = useState<CorrelationPoint[]>([]);
  const [mertonPreview, setMertonPreview] = useState<MertonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    "[boot] credit risk engine ready",
    "[boot] awaiting portfolio selection",
  ]);
  const [error, setError] = useState<string | null>(null);
  const debouncedRho = useDebouncedValue(rho, 300);

  function pushLog(message: string) {
    setLogs((current) => [...current, `${new Date().toLocaleTimeString()} ${message}`]);
  }

  useEffect(() => {
    void loadPreset(activePreset);
  }, [activePreset]);

  useEffect(() => {
    if (!portfolio.length || !portfolioResult) {
      return;
    }
    void runAnalysis(false);
  }, [debouncedRho]);

  async function loadPreset(name: string) {
    try {
      pushLog(`[preset] loading ${name}`);
      const preset = await fetchPreset(name);
      setPortfolio(preset.companies);
      setError(null);
      pushLog(`[preset] ${preset.companies.length} names loaded`);
    } catch (err) {
      setError(extractErrorMessage(err));
      pushLog(`[error] failed to load preset ${name}`);
    }
  }

  async function handleAddTicker(ticker: string) {
    try {
      pushLog(`[merton] probing ${ticker}`);
      const response = await fetchMerton(ticker);
      setMertonPreview(response);
      setPortfolio((current) => {
        if (current.some((entry) => entry.ticker === ticker)) {
          return current;
        }
        return [...current, { ticker, notional: 5_000_000 }];
      });
      setError(null);
      pushLog(`[merton] ${ticker} added with PD ${response.probability_of_default.toExponential(2)}`);
    } catch (err) {
      setError(extractErrorMessage(err));
      pushLog(`[error] could not add ${ticker}`);
    }
  }

  async function runAnalysis(manual = true) {
    if (!portfolio.length) {
      return;
    }

    setLoading(true);
    setError(null);
    if (manual) {
      pushLog("[run] launching portfolio, tranche, and stress workflows");
    } else {
      pushLog(`[rerun] rho debounced to ${debouncedRho.toFixed(2)}`);
    }

    try {
      const [portfolioData, trancheData, stressData] = await Promise.all([
        analyzePortfolio({ companies: portfolio, rho: debouncedRho, confidence, n_sim: nSim }),
        priceTranches({ companies: portfolio, rho: debouncedRho, n_sim: nSim, tranches: defaultTranches }),
        runStress({
          companies: portfolio,
          base_rho: debouncedRho,
          stressed_rho: stressedRho,
          pd_multiplier: pdMultiplier,
          confidence,
          n_sim: nSim,
          tranches: defaultTranches,
        }),
      ]);

      let sensitivityData = correlationSeries;
      if (manual || correlationSeries.length === 0) {
        pushLog("[sensitivity] building reduced rho sweep");
        sensitivityData = await buildCorrelationSeries(portfolio, confidence, nSim);
      }

      setPortfolioResult(portfolioData);
      setTrancheResult(trancheData);
      setStressResult(stressData);
      setCorrelationSeries(sensitivityData);
      pushLog(`[portfolio] EL ${formatCurrency(portfolioData.expected_loss)} across ${portfolioData.companies.length} names`);
      pushLog(`[stress] ES delta ${stressData.es_delta_pct.toFixed(1)}% under stress`);
    } catch (err) {
      const message = extractErrorMessage(err);
      setError(message);
      pushLog(`[error] ${message}`);
    } finally {
      setLoading(false);
    }
  }

  const companyCards = useMemo<CompanyResult[]>(() => portfolioResult?.companies ?? [], [portfolioResult]);

  return (
    <Layout
      sidebar={
        <>
          <PresetSelector activePreset={activePreset} onSelect={setActivePreset} />
          <TickerInput onAdd={handleAddTicker} />
          <ParameterSliders
            rho={rho}
            confidence={confidence}
            nSim={nSim}
            stressedRho={stressedRho}
            pdMultiplier={pdMultiplier}
            onRhoChange={setRho}
            onConfidenceChange={setConfidence}
            onNSimChange={setNSim}
            onStressedRhoChange={setStressedRho}
            onPdMultiplierChange={setPdMultiplier}
          />
          <section className="panel">
            <div className="panel-head">
              <p className="eyebrow">// live book</p>
              <h3>Current Portfolio</h3>
            </div>
            <div className="portfolio-list">
              {portfolio.map((entry) => (
                <label key={entry.ticker} className="portfolio-row">
                  <span>{entry.ticker}</span>
                  <input
                    type="number"
                    min={100000}
                    step={100000}
                    value={entry.notional}
                    onChange={(event) => {
                      const value = Number(event.target.value);
                      const sanitizedValue = Number.isFinite(value) && value > 0 ? value : 100000;
                      setPortfolio((current) =>
                        current.map((item) =>
                          item.ticker === entry.ticker ? { ...item, notional: sanitizedValue } : item,
                        ),
                      );
                    }}
                  />
                </label>
              ))}
            </div>
          </section>
          {mertonPreview ? (
            <section className="panel accent-panel">
              <div className="panel-head">
                <p className="eyebrow">// latest probe</p>
                <h3>{mertonPreview.ticker}</h3>
              </div>
              <p className="preview-copy">
                {mertonPreview.company_name} · {mertonPreview.sector}
              </p>
              <p className="preview-copy">
                PD {mertonPreview.probability_of_default.toExponential(2)} · DD{" "}
                {mertonPreview.distance_to_default.toFixed(2)}
              </p>
            </section>
          ) : null}
          <RunButton disabled={!portfolio.length} loading={loading} onClick={() => void runAnalysis()} />
        </>
      }
    >
      <section className="hero-card">
        <p className="eyebrow">// overview</p>
        <div className="hero-grid">
          <div>
            <h2>Structural + portfolio credit analytics in one terminal.</h2>
            <p>
              Live Merton PDs feed the Vasicek engine, which feeds tranche and
              stress outputs. Tune rho, simulate tail loss, and inspect where the
              book breaks first.
            </p>
          </div>
          <div className="hero-stat">
            <span>Backend status</span>
            <strong>FastAPI live</strong>
            <small>{portfolio.length} names loaded into the portfolio builder</small>
          </div>
        </div>
        {error ? <p className="error-banner">{error}</p> : null}
      </section>

      {portfolioResult ? (
        <>
          <MetricGrid
            expectedLoss={portfolioResult.expected_loss}
            unexpectedLoss={portfolioResult.unexpected_loss}
            creditVar={portfolioResult.credit_var}
            expectedShortfall={portfolioResult.expected_shortfall}
            totalNotional={portfolioResult.total_notional}
          />

          <section className="section-grid">
            <LossHistogram
              losses={portfolioResult.loss_distribution}
              expectedLoss={portfolioResult.expected_loss}
              creditVar={portfolioResult.credit_var}
            />
            {trancheResult ? <TrancheChart tranches={trancheResult.tranches} /> : null}
          </section>

          <section className="company-section">
            <div className="panel-head">
              <p className="eyebrow">// obligors</p>
              <h3>Merton Company Cards</h3>
            </div>
            <div className="company-list">
              {companyCards.map((company) => (
                <CompanyCard key={company.ticker} company={company} />
              ))}
            </div>
          </section>

          <section className="section-grid">
            <CorrelationSensitivity points={correlationSeries} />
            {stressResult ? <StressTable stress={stressResult} /> : null}
          </section>

          <section className="section-grid">
            <JointDefaultHeatmap companies={companyCards} rho={portfolioResult.rho} />
            <SystemLog entries={logs} />
          </section>
        </>
      ) : (
        <section className="empty-state">
          <h3>Run the engine to generate the first portfolio view.</h3>
          <p>
            Presets are already available in the sidebar. Once you run the book,
            the dashboard will populate company cards, risk metrics, tranche
            losses, and stress deltas.
          </p>
        </section>
      )}
    </Layout>
  );
}

export default App;
