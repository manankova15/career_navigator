interface Props { message: string; }

export default function ErrorBanner({ message }: Props) {
  return (
    <div style={{
      background: "#FEF2F2",
      color: "#DC2626",
      border: "1.5px solid #FECACA",
      borderRadius: 12,
      padding: "12px 16px",
      marginBottom: 16,
      fontSize: 14,
      fontWeight: 500,
      display: "flex",
      alignItems: "center",
      gap: 8,
    }}>
      <span style={{ flexShrink: 0 }}>⚠</span>
      {message}
    </div>
  );
}
