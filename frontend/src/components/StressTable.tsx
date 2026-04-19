import type { StressResponse } from "../types/api";
import { formatCurrency, formatSignedPercent } from "../lib/format";

interface StressTableProps {
  stress: StressResponse;
}

export function StressTable({ stress }: StressTableProps) {
  const rows = [
    {
      label: "Expected Loss",
      base: stress.base.expected_loss,
      stressed: stress.stressed.expected_loss,
      delta: stress.el_delta_pct,
    },
    {
      label: "Credit VaR",
      base: stress.base.credit_var,
      stressed: stress.stressed.credit_var,
      delta: stress.var_delta_pct,
    },
    {
      label: "Expected Shortfall",
      base: stress.base.expected_shortfall,
      stressed: stress.stressed.expected_shortfall,
      delta: stress.es_delta_pct,
    },
  ];

  return (
    <section className="chart-panel">
      <div className="panel-head">
        <p className="eyebrow">// stress test</p>
        <h3>Base vs Stressed Scenario</h3>
      </div>
      <div className="table-wrap">
        <table className="stress-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Base</th>
              <th>Stressed</th>
              <th>Delta</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <td>{row.label}</td>
                <td>{formatCurrency(row.base)}</td>
                <td>{formatCurrency(row.stressed)}</td>
                <td className={row.delta >= 0 ? "delta-up" : "delta-down"}>
                  {formatSignedPercent(row.delta)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
