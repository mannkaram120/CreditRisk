interface RunButtonProps {
  disabled: boolean;
  loading: boolean;
  onClick: () => void;
}

export function RunButton({ disabled, loading, onClick }: RunButtonProps) {
  return (
    <button
      type="button"
      className="primary-button run-button"
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? "Running simulations..." : "Run Engine"}
    </button>
  );
}
