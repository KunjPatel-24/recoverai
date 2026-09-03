import { useState, useEffect } from 'react'
import { Search, Filter } from 'lucide-react'
import { inr } from '../api'

const API_BASE = '/api'

const agentColors = {
  RISK_DETECTOR: 'text-accent-300 bg-accent-500/10 border-accent-500/25',
  ROOT_CAUSE_ANALYST: 'text-sky-300 bg-sky-500/10 border-sky-500/25',
  RECOVERY_STRATEGIST: 'text-brand-300 bg-brand-500/10 border-brand-500/25',
  SAFETY_GUARDIAN: 'text-warning-300 bg-warning-500/10 border-warning-500/25',
  EXECUTOR: 'text-cyan-300 bg-cyan-500/10 border-cyan-500/25',
  OUTCOME_MONITOR: 'text-brand-300 bg-brand-500/10 border-brand-500/25',
  WEBHOOK_HANDLER: 'text-pink-300 bg-pink-500/10 border-pink-500/25',
}

export default function AuditTrail() {
  const [logs, setLogs] = useState([])
  const [search, setSearch] = useState('')
  const [agentFilter, setAgentFilter] = useState('ALL')

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard/audit-trail?limit=300`)
      setLogs(await res.json())
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 3000)
    return () => clearInterval(interval)
  }, [])

  const agents = ['ALL', ...Array.from(new Set(logs.map((l) => l.agent)))]
  const filtered = logs.filter((l) => {
    const s = search.toLowerCase()
    const matchesSearch =
      (l.case_id || '').toLowerCase().includes(s) ||
      (l.action || '').toLowerCase().includes(s)
    const matchesAgent = agentFilter === 'ALL' || l.agent === agentFilter
    return matchesSearch && matchesAgent
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Audit Trail</h2>
        <p className="text-gray-400 mt-1">Complete immutable log of every agent decision</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by case ID or action…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white/[0.04] border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/20 transition-all"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/20 transition-all"
          >
            {agents.map((a) => (
              <option key={a} value={a} className="bg-surface-900">{(a || '').replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-gray-500 text-left bg-white/[0.02]">
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider">Time</th>
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider">Case</th>
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider">Agent</th>
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider">Action</th>
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider">Details</th>
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider">Status</th>
                <th className="px-6 py-3 font-medium uppercase text-[11px] tracking-wider text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.05]">
              {filtered.map((log, i) => (
                <tr key={i} className="hover:bg-white/[0.04] transition-colors">
                  <td className="px-6 py-3 text-gray-500 whitespace-nowrap">
                    {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
                  </td>
                  <td className="px-6 py-3 font-mono text-gray-300">{log.case_id}</td>
                  <td className="px-6 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${agentColors[log.agent] || 'text-gray-400 bg-gray-800 border-gray-700'}`}>
                      {(log.agent || '').replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-gray-300 font-medium">{(log.action || '').replace(/_/g, ' ')}</td>
                  <td className="px-6 py-3 text-gray-400 max-w-xs truncate">{log.details}</td>
                  <td className="px-6 py-3">
                    <span className={`text-xs font-semibold ${
                      log.status === 'SUCCESS' || log.status === 'APPROVED' ? 'text-brand-400'
                        : log.status === 'REJECTED' || log.status === 'FAILED' ? 'text-danger-400' : 'text-gray-400'
                    }`}>{log.status}</span>
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-brand-400">
                    {log.amount ? inr(log.amount) : '—'}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={7} className="px-6 py-10 text-center text-gray-500">No audit entries yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
