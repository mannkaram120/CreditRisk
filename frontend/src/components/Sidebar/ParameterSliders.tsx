interface ParameterSlidersProps {
  rho: number;
  confidence: number;
  nSim: number;
  stressedRho: number;
  pdMultiplier: number;
  onRhoChange: (value: number) => void;
  onConfidenceChange: (value: number) => void;
  onNSimChange: (value: number) => void;
  onStressedRhoChange: (value: number) => void;
  onPdMultiplierChange: (value: number) => void;
}

export function ParameterSliders(props: ParameterSlidersProps) {
  const {
    rho,
    confidence,
    nSim,
    stressedRho,
    pdMultiplier,
    onRhoChange,
    onConfidenceChange,
    onNSimChange,
    onStressedRhoChange,
    onPdMultiplierChange,
  } = props;

  return (
    <section className="panel">
      <div className="panel-head">
        <p className="eyebrow">// scenario controls</p>
        <h3>Simulation Inputs</h3>
      </div>

      <label className="control">
        <span>Correlation rho: {rho.toFixed(2)}</span>
        <input
          type="range"
          min="0"
          max="0.9"
          step="0.05"
          value={rho}
          onChange={(event) => onRhoChange(Number(event.target.value))}
        />
      </label>

      <label className="control">
        <span>Confidence</span>
        <select
          value={confidence}
          onChange={(event) => onConfidenceChange(Number(event.target.value))}
        >
          <option value={0.9}>90.0%</option>
          <option value={0.95}>95.0%</option>
          <option value={0.99}>99.0%</option>
          <option value={0.999}>99.9%</option>
        </select>
      </label>

      <label className="control">
        <span>Simulations</span>
        <select value={nSim} onChange={(event) => onNSimChange(Number(event.target.value))}>
          <option value={10000}>10,000</option>
          <option value={25000}>25,000</option>
          <option value={50000}>50,000</option>
          <option value={100000}>100,000</option>
        </select>
      </label>

      <label className="control">
        <span>Stress rho: {stressedRho.toFixed(2)}</span>
        <input
          type="range"
          min="0.1"
          max="0.95"
          step="0.05"
          value={stressedRho}
          onChange={(event) => onStressedRhoChange(Number(event.target.value))}
        />
      </label>

      <label className="control">
        <span>PD multiplier: {pdMultiplier.toFixed(1)}x</span>
        <input
          type="range"
          min="1"
          max="5"
          step="0.25"
          value={pdMultiplier}
          onChange={(event) => onPdMultiplierChange(Number(event.target.value))}
        />
      </label>
    </section>
  );
}
