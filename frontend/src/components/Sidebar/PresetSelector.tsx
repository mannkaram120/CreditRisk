interface PresetSelectorProps {
  activePreset: string;
  onSelect: (preset: string) => void;
}

const presets = [
  { key: "ig", label: "Investment Grade" },
  { key: "hy", label: "High Yield" },
  { key: "mixed", label: "Mixed Book" },
  { key: "crisis", label: "Crisis Banks" },
];

export function PresetSelector({
  activePreset,
  onSelect,
}: PresetSelectorProps) {
  return (
    <section className="panel">
      <div className="panel-head">
        <p className="eyebrow">// preset mode</p>
        <h3>Portfolio Seed</h3>
      </div>
      <div className="preset-grid">
        {presets.map((preset) => (
          <button
            key={preset.key}
            type="button"
            className={activePreset === preset.key ? "preset-chip active" : "preset-chip"}
            onClick={() => onSelect(preset.key)}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </section>
  );
}
