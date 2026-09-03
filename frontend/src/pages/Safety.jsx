import { useState, useEffect } from 'react'
import { Shield, XCircle, AlertTriangle, CheckCircle, Lock } from 'lucide-react'
import { getJSON } from '../api'

const policies = [
  { name: 'Maximum Retries', value: '3', icon: Lock },
  { name: 'Maximum Recovery Actions', value: '2', icon: Lock },
  { name: 'Maximum Transaction Amount', value: '₹50,000', icon: Lock },
  { name: 'Minimum Diagnosis Confidence', value: '40%', icon: AlertTriangle },
  { name: 'Duplicate Prevention', value: 'Enabled', icon: CheckCircle },
  { name: 'Fraud Escalation', value: 'Enabled', icon: CheckCircle },
]

const stoppingRules = [
  'Customer opted out of recovery contact',
  'Fraud signal is HIGH',
  'Previous action already succeeded (duplicate risk)',
  'Maximum intervention attempts reached',
  'Amount exceeds ₹50,000 agent authority → escalate',
  'Diagnosis confidence below 40% → escalate',
]

export default function Safety() {
  const [enf, setEnf] = useState(null)

  useEffect(() => {
    getJSON('/dashboard/metrics')
      .then((m) => setEnf(m.enforcement || null))
      .catch((e) => console.error(e))
  }, [])

  const stats = [
    { label: 'Cases Blocked', value: enf?.blocked_total ?? 0 },
    { label: 'Escalated to Human', value: enf?.escalations ?? 0 },
    { label: 'Fraud Blocks', value: enf?.fraud_blocks ?? 0 },
    { label: 'Opt-outs Respected', value: enf?.optout_blocks ?? 0 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Policy &amp; Safety</h2>
        <p className="text-gray-400 mt-1">Bounded recovery workflow — the agent never has unlimited control</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 rounded-lg bg-brand-500/10 border border-brand-500/25 flex items-center justify-center">
              <Shield className="w-4 h-4 text-brand-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Autonomous Action Policy</h3>
          </div>
          <div className="space-y-4">
            {policies.map((p) => (
              <div key={p.name} className="flex items-center justify-between py-3 border-b border-white/[0.06] last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-white/[0.05] border border-white/10 flex items-center justify-center">
                    <p.icon className="w-4 h-4 text-gray-400" />
                  </div>
                  <span className="text-gray-300">{p.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-white font-semibold">{p.value}</span>
                  <span className="badge badge-success text-[10px]">ACTIVE</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 rounded-lg bg-danger-500/10 border border-danger-500/25 flex items-center justify-center">
              <XCircle className="w-4 h-4 text-danger-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Stopping Rules</h3>
          </div>
          <p className="text-sm text-gray-400 mb-4">
            The agent will <span className="text-danger-400 font-semibold">block or escalate</span> — never act autonomously — when any of these hold:
          </p>
          <div className="space-y-3">
            {stoppingRules.map((rule, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-danger-500/[0.06] border border-danger-500/20 rounded-lg">
                <XCircle className="w-4 h-4 text-danger-400 flex-shrink-0" />
                <span className="text-sm text-gray-300">{rule}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-1">Policy Enforcement</h3>
        <p className="text-xs text-gray-500 mb-4">Live counts from the most recent run</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((s) => (
            <div key={s.label} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-center">
              <p className="text-3xl font-bold text-brand-400">{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
