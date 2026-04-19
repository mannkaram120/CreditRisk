import axios from "axios";
import type {
  CorrelationPoint,
  MertonResponse,
  PortfolioName,
  PortfolioRequest,
  PortfolioResponse,
  PresetResponse,
  StressRequest,
  StressResponse,
  TrancheRequest,
  TrancheResponse,
} from "../types/api";

const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const client = axios.create({
  baseURL,
  timeout: 60000,
});

function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return (
      error.response?.data?.detail ??
      error.message ??
      "Unexpected API error"
    );
  }
  return error instanceof Error ? error.message : "Unexpected API error";
}

export async function fetchPreset(name: string): Promise<PresetResponse> {
  const { data } = await client.get<PresetResponse>(`/portfolio/preset/${name}`);
  return data;
}

export async function analyzePortfolio(
  payload: PortfolioRequest,
): Promise<PortfolioResponse> {
  const { data } = await client.post<PortfolioResponse>("/portfolio/analyze", payload);
  return data;
}

export async function priceTranches(
  payload: TrancheRequest,
): Promise<TrancheResponse> {
  const { data } = await client.post<TrancheResponse>("/tranche/price", payload);
  return data;
}

export async function runStress(
  payload: StressRequest,
): Promise<StressResponse> {
  const { data } = await client.post<StressResponse>("/stress/run", payload);
  return data;
}

export async function fetchMerton(ticker: string): Promise<MertonResponse> {
  const { data } = await client.get<MertonResponse>(`/merton/${ticker}`);
  return data;
}

export async function buildCorrelationSeries(
  companies: PortfolioName[],
  confidence: number,
  nSim: number,
): Promise<CorrelationPoint[]> {
  const rhoValues = [0, 0.2, 0.4, 0.6, 0.8];
  const responses: PortfolioResponse[] = [];

  for (const rho of rhoValues) {
    const response = await analyzePortfolio({
      companies,
      rho,
      confidence,
      n_sim: Math.min(nSim, 25_000),
    });
    responses.push(response);
  }

  return responses.map((response) => ({
    rho: response.rho,
    expectedShortfall: response.expected_shortfall,
    creditVar: response.credit_var,
  }));
}

export { baseURL, extractErrorMessage };
