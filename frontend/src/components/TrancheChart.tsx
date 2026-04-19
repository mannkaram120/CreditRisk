import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrancheResult } from "../types/api";
import { formatCurrency, formatPercent } from "../lib/format";

interface TrancheChartProps {
  tranches: TrancheResult[];
}

const colors = ["#cb4b3f", "#cf8a2e", "#6bbf3e", "#111110"];

export function TrancheChart({ tranches }: TrancheChartProps) {
  return (
    <section className="chart-panel">
      <div className="panel-head">
        <p className="eyebrow">// tranches</p>
        <h3>Expected Loss by CDO Slice</h3>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart layout="vertical" data={tranches} margin={{ left: 12, right: 12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(17,17,16,0.08)" />
            <XAxis type="number" stroke="#888780" tickFormatter={(value) => formatCurrency(value)} />
            <YAxis type="category" dataKey="label" stroke="#888780" width={90} />
            <Tooltip
              formatter={(value: number, name) =>
                name === "expected_loss_pct"
                  ? [formatPercent(value), "Loss %"]
                  : [formatCurrency(value), "Expected Loss"]
              }
            />
            <Bar dataKey="expected_loss_usd" radius={[0, 6, 6, 0]}>
              {tranches.map((tranche, index) => (
                <Cell key={tranche.label} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
