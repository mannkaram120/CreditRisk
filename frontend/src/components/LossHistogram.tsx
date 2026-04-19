import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "../lib/format";

interface LossHistogramProps {
  losses: number[];
  expectedLoss: number;
  creditVar: number;
}

function buildHistogram(losses: number[]) {
  if (!losses.length) {
    return [];
  }

  const min = Math.min(...losses);
  const max = Math.max(...losses);
  const bins = 24;
  const width = max === min ? 1 : (max - min) / bins;
  const counts = new Array(bins).fill(0);

  losses.forEach((value) => {
    const rawIndex = Math.floor((value - min) / width);
    const index = Math.min(Math.max(rawIndex, 0), bins - 1);
    counts[index] += 1;
  });

  return counts.map((count, index) => {
    const center = min + width * index + width / 2;
    return {
      label: center,
      count,
      center,
    };
  });
}

export function LossHistogram({
  losses,
  expectedLoss,
  creditVar,
}: LossHistogramProps) {
  const histogram = buildHistogram(losses);
  const tailStart = expectedLoss + creditVar;
  const elMarker = histogram.reduce<number | null>((closest, entry) => {
    if (closest === null) {
      return entry.center;
    }
    return Math.abs(entry.center - expectedLoss) < Math.abs(closest - expectedLoss)
      ? entry.center
      : closest;
  }, null);

  return (
    <section className="chart-panel">
      <div className="panel-head">
        <p className="eyebrow">// loss dist.</p>
        <h3>Portfolio Loss Distribution</h3>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={histogram}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(17,17,16,0.08)" />
            <XAxis
              dataKey="label"
              tickFormatter={(value) => formatCurrency(Number(value))}
              minTickGap={30}
              stroke="#888780"
            />
            <YAxis stroke="#888780" />
            <Tooltip
              formatter={(value: number) => [value, "Scenarios"]}
              labelFormatter={(label) => formatCurrency(Number(label))}
            />
            {elMarker !== null ? (
              <ReferenceLine
                x={elMarker}
                stroke="#111110"
                strokeDasharray="6 6"
                label={{ value: "EL", position: "insideTopRight" }}
              />
            ) : null}
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {histogram.map((entry) => (
                <Cell
                  key={entry.center}
                  fill={entry.center > tailStart ? "var(--danger)" : "var(--green)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
