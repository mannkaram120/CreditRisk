export interface PortfolioName {
  ticker: string;
  notional: number;
}

export interface MertonResponse {
  ticker: string;
  company_name: string;
  market_cap: number;
  total_debt: number;
  equity_volatility: number;
  asset_value: number;
  asset_volatility: number;
  distance_to_default: number;
  probability_of_default: number;
  risk_label: string;
  lgd: number;
  sector: string;
}

export interface CompanyResult {
  ticker: string;
  company_name: string;
  pd: number;
  dd: number;
  asset_volatility: number;
  market_cap: number;
  total_debt: number;
  lgd: number;
  notional: number;
  risk_label: string;
  sector: string;
}

export interface PortfolioRequest {
  companies: PortfolioName[];
  rho: number;
  confidence: number;
  n_sim: number;
}

export interface PortfolioResponse {
  companies: CompanyResult[];
  expected_loss: number;
  unexpected_loss: number;
  credit_var: number;
  expected_shortfall: number;
  total_notional: number;
  rho: number;
  confidence: number;
  n_sim: number;
  loss_distribution: number[];
}

export interface TranchePoint {
  attachment: number;
  detachment: number;
}

export interface TrancheResult {
  label: string;
  attachment: number;
  detachment: number;
  expected_loss_usd: number;
  expected_loss_pct: number;
  tranche_notional: number;
}

export interface TrancheRequest {
  companies: PortfolioName[];
  rho: number;
  n_sim: number;
  tranches: TranchePoint[];
}

export interface TrancheResponse {
  tranches: TrancheResult[];
  total_notional: number;
  loss_distribution: number[];
}

export interface StressRequest {
  companies: PortfolioName[];
  base_rho: number;
  stressed_rho: number;
  pd_multiplier: number;
  confidence: number;
  n_sim: number;
  tranches?: TranchePoint[];
}

export interface StressScenario {
  label: string;
  rho: number;
  expected_loss: number;
  unexpected_loss: number;
  credit_var: number;
  expected_shortfall: number;
  tranche_results?: TrancheResult[] | null;
}

export interface StressResponse {
  base: StressScenario;
  stressed: StressScenario;
  el_delta_pct: number;
  var_delta_pct: number;
  es_delta_pct: number;
}

export interface PresetResponse {
  preset: string;
  companies: PortfolioName[];
}

export interface CorrelationPoint {
  rho: number;
  expectedShortfall: number;
  creditVar: number;
}
