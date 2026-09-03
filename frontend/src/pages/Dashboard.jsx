import { useState, useEffect, useCallback } from 'react'
import { Play, Loader, TrendingUp, Search, Zap } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import MetricsCards from '../components/MetricsCards'
import AgentTimeline from '../components/AgentTimeline'
import { getJSON, postJSON, inr } from '../api'

const CAT_COLORS = ['#10b981', '#fbbf24', '#f87171', '#60a5fa', '#a78bfa']

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [logs, setLogs] = useState([])
  const [running, setRunning] = useState(false)
  const [diagnosing, setDiagnosing] = useState(false)
  const [executing, setExecuting] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [m, a] = await Promise.all([
        getJSON('/dashboard/metrics'),
        getJSON('/dashboard/audit-trail?limit=40'),
      ])
      setMetrics(m)
      setLogs(a)
    } catch (e) {
      console.error(e)
    }
  }, [])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 3000)
    return () => clearInterval(t)
  }, [refresh])

  const runRecovery = async () => {
    setRunning(true)
    try {
      await postJSON('/recovery/run')
      await refresh()
    } catch (e) {
      console.error(e)
    }
    setRunning(false)
  }

  const diagnoseOnly = async () => {
    setDiagnosing(true)
    try {
      await postJSON('/recovery/diagnose')
      await refresh()
    } catch (e) {
      console.error(e)
    }
    setDiagnosing(false)
  }

  const executeApproved = async () => {
    setExecuting(true)
    try {
      await postJSON('/recovery/execute-approved')
      await refresh()
    } catch (e) {
      console.error(e)
    }
    setExecuting(false)
  }

  const catData = metrics
    ? Object.entries(metrics.category_breakdown || {}).map(([k, v]) => ({
        name: k.replace(/_/g, ' '),
        amount: v.amount,
      }))
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Recovery Command Center</h2>
          <p className="text-gray-400 mt-1">Autonomous, bounded revenue recovery</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap shrink-0">
          <button
            onClick={diagnoseOnly}
            disabled={diagnosing || running || executing}
            title="Reset, seed, and diagnose every case — stops before execution so Active Cases reflects pending work."
            className="btn-secondary flex items-center gap-2 disabled:opacity-50 whitespace-nowrap"
          >
            {diagnosing ? <Loader className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {diagnosing ? 'Diagnosing…' : '1. Diagnose Only'}
          </button>
          <button
            onClick={executeApproved}
            disabled={executing || running || diagnosing || !metrics?.active_cases}
            title="Execute every currently APPROVED case."
            className="btn-secondary flex items-center gap-2 disabled:opacity-50 whitespace-nowrap"
          >
            {executing ? <Loader className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {executing ? 'Executing…' : '2. Execute Approved'}
          </button>
          <button onClick={runRecovery} disabled={running || diagnosing || executing} className="btn-primary flex items-center gap-2 disabled:opacity-50 whitespace-nowrap">
            {running ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {running ? 'Running agents…' : 'Run Recovery (one-click)'}
          </button>
        </div>
      </div>

      <MetricsCards metrics={metrics} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Expected vs actual + chart */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-brand-400" />
            <h3 className="text-lg font-semibold text-white">At-Risk by Category</h3>
          </div>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={catData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} interval={0} angle={-12} textAnchor="end" height={50} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6' }}
                  formatter={(v) => [inr(v), 'At risk']}
                />
                <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                  {catData.map((_, i) => (
                    <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          {metrics && (
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-500 text-xs">Expected recovery</p>
                <p className="text-lg font-bold text-gray-200">{inr(metrics.expected_recovery)}</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-500 text-xs">Actual recovered</p>
                <p className="text-lg font-bold text-brand-400">{inr(metrics.total_recovered)}</p>
              </div>
            </div>
          )}
        </div>

        <AgentTimeline logs={logs} />
      </div>
    </div>
  )
}
