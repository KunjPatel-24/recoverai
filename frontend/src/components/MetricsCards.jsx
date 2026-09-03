import { TrendingUp, IndianRupee, Percent, Layers } from 'lucide-react'
import { inr } from '../api'

const TONES = {
  warning: {
    text: 'text-warning-300',
    chip: 'bg-warning-500/10 border-warning-500/25 text-warning-300',
    bar: 'from-warning-400 to-warning-600',
  },
  brand: {
    text: 'text-brand-300',
    chip: 'bg-brand-500/10 border-brand-500/25 text-brand-300',
    bar: 'from-brand-400 to-brand-600',
  },
  accent: {
    text: 'text-accent-300',
    chip: 'bg-accent-500/10 border-accent-500/25 text-accent-300',
    bar: 'from-accent-400 to-accent-600',
  },
  neutral: {
    text: 'text-gray-200',
    chip: 'bg-white/[0.06] border-white/10 text-gray-300',
    bar: 'from-gray-500 to-gray-700',
  },
}

export default function MetricsCards({ metrics }) {
  const m = metrics || {}
  const cards = [
    { label: 'At Risk', value: inr(m.total_at_risk), icon: IndianRupee, tone: 'warning' },
    { label: 'Recovered', value: inr(m.total_recovered), icon: TrendingUp, tone: 'brand' },
    { label: 'Recovery Rate', value: `${m.recovery_rate ?? 0}%`, icon: Percent, tone: 'accent' },
    { label: 'Active Cases', value: m.active_cases ?? 0, icon: Layers, tone: 'neutral' },
  ]
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => {
        const t = TONES[c.tone]
        return (
          <div key={c.label} className="card card-hover overflow-hidden">
            <div className={`absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r ${t.bar}`} />
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">{c.label}</p>
              <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${t.chip}`}>
                <c.icon className="w-4 h-4" />
              </div>
            </div>
            <p className={`mt-3 text-2xl font-bold tracking-tight ${t.text}`}>{c.value}</p>
          </div>
        )
      })}
    </div>
  )
}
