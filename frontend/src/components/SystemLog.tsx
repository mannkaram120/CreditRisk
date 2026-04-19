interface SystemLogProps {
  entries: string[];
}

export function SystemLog({ entries }: SystemLogProps) {
  return (
    <section className="log-panel">
      <div className="panel-head">
        <p className="eyebrow">// system log</p>
        <h3>Execution Trace</h3>
      </div>
      <div className="log-body">
        {entries.slice(-10).map((entry, index) => (
          <p key={`${entry}-${index}`}>{entry}</p>
        ))}
      </div>
    </section>
  );
}
