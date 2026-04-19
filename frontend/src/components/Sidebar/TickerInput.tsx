import { useState } from "react";

interface TickerInputProps {
  onAdd: (ticker: string) => Promise<void> | void;
}

export function TickerInput({ onAdd }: TickerInputProps) {
  const [ticker, setTicker] = useState("");

  async function submitTicker() {
    const value = ticker.trim().toUpperCase();
    if (!value) {
      return;
    }
    await onAdd(value);
    setTicker("");
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <p className="eyebrow">// custom mode</p>
        <h3>Add Ticker</h3>
      </div>
      <div className="ticker-row">
        <input
          value={ticker}
          onChange={(event) => setTicker(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              void submitTicker();
            }
          }}
          placeholder="AAPL"
        />
        <button type="button" className="primary-button" onClick={() => void submitTicker()}>
          Add
        </button>
      </div>
    </section>
  );
}
