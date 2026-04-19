import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CorrelationPoint } from "../types/api";
import { formatCurrency } from "../lib/format";

interface CorrelationSensitivityProps {
  points: CorrelationPoint[];
}

export function CorrelationSensitivity({
  points,
}: CorrelationSensitivityProps) {
  return (
    <section className="chart-panel">
      <div className="panel-head">
        <p className="eyebrow">// rho sensitivity</p>
        <h3>Tail Risk vs Correlation</h3>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={points}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(17,17,16,0.08)" />
            <XAxis dataKey="rho" stroke="#888780" />
            <YAxis stroke="#888780" tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Line
              type="monotone"
              dataKey="expectedShortfall"
              stroke="#111110"
              strokeWidth={3}
              dot={{ r: 3 }}
              name="Expected Shortfall"
            />
            <Line
              type="monotone"
              dataKey="creditVar"
              stroke="#6bbf3e"
              strokeWidth={2}
              dot={{ r: 2 }}
              name="Credit VaR"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
