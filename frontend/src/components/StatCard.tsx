interface Props {
  label: string
  value: string
  color?: string
}

export function StatCard({ label, value, color }: Props) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>
        {value}
      </div>
    </div>
  )
}
