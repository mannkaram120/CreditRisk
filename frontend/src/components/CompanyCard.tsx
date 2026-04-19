import type { CompanyResult } from "../types/api";
import { formatCurrency, formatPercent } from "../lib/format";

interface CompanyCardProps {
  company: CompanyResult;
}

export function CompanyCard({ company }: CompanyCardProps) {
  return (
    <article className="company-card">
      <div className="company-card-top">
        <div>
          <p className="eyebrow">// {company.ticker}</p>
          <h3>{company.company_name}</h3>
        </div>
        <span className={`risk-badge ${company.risk_label.toLowerCase()}`}>
          {company.risk_label}
        </span>
      </div>
      <div className="company-grid">
        <div>
          <span>PD</span>
          <strong>{formatPercent(company.pd, 4)}</strong>
        </div>
        <div>
          <span>DD</span>
          <strong>{company.dd.toFixed(2)}</strong>
        </div>
        <div>
          <span>Asset Vol</span>
          <strong>{formatPercent(company.asset_volatility)}</strong>
        </div>
        <div>
          <span>Notional</span>
          <strong>{formatCurrency(company.notional)}</strong>
        </div>
      </div>
      <p className="company-meta">
        {company.sector} · Debt {formatCurrency(company.total_debt)} · LGD{" "}
        {formatPercent(company.lgd)}
      </p>
    </article>
  );
}
