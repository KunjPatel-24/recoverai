import { TrendingUp, IndianRupee, Percent, Layers } from 'lucide-react'
import { inr } from '../api'

export default function MetricsCards({ metrics }) {
  const m = metrics || {}
  const cards = [
    { label: 'At Risk', value: inr(m.total_at_risk), icon: IndianRupee, tone: 'text-warning-400' },
    { label: 'Recovered', value: inr(m.total_recovered), icon: TrendingUp, tone: 'text-brand-400' },
    { label: 'Recovery Rate', value: `${m.recovery_rate ?? 0}%`, icon: Percent, tone: 'text-brand-400' },
    { label: 'Active Cases', value: m.active_cases ?? 0, icon: Layers, tone: 'text-gray-200' },
  ]
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="card">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-gray-500">{c.label}</p>
            <c.icon className={`w-4 h-4 ${c.tone}`} />
          </div>
          <p className={`mt-3 text-2xl font-bold ${c.tone}`}>{c.value}</p>
        </div>
      ))}
    </div>
  )
}
