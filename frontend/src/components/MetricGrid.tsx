import { formatCurrency, formatPercent } from "../lib/format";

interface MetricGridProps {
  expectedLoss: number;
  unexpectedLoss: number;
  creditVar: number;
  expectedShortfall: number;
  totalNotional: number;
}

export function MetricGrid({
  expectedLoss,
  unexpectedLoss,
  creditVar,
  expectedShortfall,
  totalNotional,
}: MetricGridProps) {
  const metrics = [
    { label: "Expected Loss", value: formatCurrency(expectedLoss) },
    { label: "Unexpected Loss", value: formatCurrency(unexpectedLoss) },
    { label: "Credit VaR", value: formatCurrency(creditVar) },
    { label: "Expected Shortfall", value: formatCurrency(expectedShortfall) },
    { label: "Portfolio Notional", value: formatCurrency(totalNotional) },
    {
      label: "EL / Notional",
      value: totalNotional > 0 ? formatPercent(expectedLoss / totalNotional) : "0.00%",
    },
  ];

  return (
    <section className="metric-grid">
      {metrics.map((metric) => (
        <article className="metric-card" key={metric.label}>
          <p>{metric.label}</p>
          <strong>{metric.value}</strong>
        </article>
      ))}
    </section>
  );
}
