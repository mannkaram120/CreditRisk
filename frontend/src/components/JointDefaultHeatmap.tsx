import { interpolateYlGn } from "d3-scale-chromatic";
import { useMemo } from "react";
import type { CompanyResult } from "../types/api";
import { formatPercent } from "../lib/format";

interface JointDefaultHeatmapProps {
  companies: CompanyResult[];
  rho: number;
}

function generateJointDefaultMatrix(companies: CompanyResult[], rho: number) {
  const n = companies.length;
  const nSim = 4000;
  const matrix = Array.from({ length: n }, () => Array.from({ length: n }, () => 0));

  for (let sim = 0; sim < nSim; sim += 1) {
    const z = boxMuller();
    const defaults = companies.map((company) => {
      const epsilon = boxMuller();
      const asset = Math.sqrt(rho) * z + Math.sqrt(1 - rho) * epsilon;
      return asset < inverseNormal(company.pd);
    });

    for (let i = 0; i < n; i += 1) {
      for (let j = 0; j < n; j += 1) {
        if (defaults[i] && defaults[j]) {
          matrix[i][j] += 1;
        }
      }
    }
  }

  return matrix.map((row) => row.map((value) => value / nSim));
}

function boxMuller() {
  let u = 0;
  let v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function inverseNormal(p: number) {
  const clipped = Math.min(Math.max(p, 1e-8), 1 - 1e-8);
  const a = [
    -39.69683028665376,
    220.9460984245205,
    -275.9285104469687,
    138.357751867269,
    -30.66479806614716,
    2.506628277459239,
  ];
  const b = [
    -54.47609879822406,
    161.5858368580409,
    -155.6989798598866,
    66.80131188771972,
    -13.28068155288572,
  ];
  const c = [
    -0.007784894002430293,
    -0.3223964580411365,
    -2.400758277161838,
    -2.549732539343734,
    4.374664141464968,
    2.938163982698783,
  ];
  const d = [
    0.007784695709041462,
    0.3224671290700398,
    2.445134137142996,
    3.754408661907416,
  ];
  const plow = 0.02425;
  const phigh = 1 - plow;
  let q;
  let r;

  if (clipped < plow) {
    q = Math.sqrt(-2 * Math.log(clipped));
    return (
      (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    );
  }
  if (clipped > phigh) {
    q = Math.sqrt(-2 * Math.log(1 - clipped));
    return -(
      (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    );
  }
  q = clipped - 0.5;
  r = q * q;
  return (
    (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
    (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
  );
}

export function JointDefaultHeatmap({
  companies,
  rho,
}: JointDefaultHeatmapProps) {
  if (companies.length === 0 || companies.length > 10) {
    return null;
  }

  const matrix = useMemo(
    () => generateJointDefaultMatrix(companies, rho),
    [companies, rho],
  );

  return (
    <section className="chart-panel">
      <div className="panel-head">
        <p className="eyebrow">// joint default</p>
        <h3>Pairwise Default Intensity</h3>
      </div>
      <div className="heatmap-grid">
        <div className="heatmap-axis">
          <span />
          {companies.map((company) => (
            <span key={`${company.ticker}-x`}>{company.ticker}</span>
          ))}
        </div>
        {companies.map((rowCompany, rowIndex) => (
          <div className="heatmap-row" key={rowCompany.ticker}>
            <span className="heatmap-label">{rowCompany.ticker}</span>
            {matrix[rowIndex].map((value, colIndex) => (
              <div
                key={`${rowCompany.ticker}-${companies[colIndex].ticker}`}
                className="heatmap-cell"
                style={{ background: interpolateYlGn(Math.min(value * 18, 1)) }}
                title={`${rowCompany.ticker}/${companies[colIndex].ticker}: ${formatPercent(value, 3)}`}
              >
                {formatPercent(value, 2)}
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
