import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Brain, Target, Shield, CheckCircle, XCircle, Loader } from 'lucide-react'
import StrategyComparison from '../components/StrategyComparison'
import { inr } from '../api'

const API_BASE = '/api'

export default function DecisionView() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)

  const fetchCase = async () => {
    try {
      const res = await fetch(`${API_BASE}/recovery/cases/${caseId}`)
      setData(await res.json())
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const execute = async () => {
    setExecuting(true)
    try {
      await fetch(`${API_BASE}/recovery/cases/${caseId}/execute`, { method: 'POST' })
      await fetchCase()
    } catch (e) {
      console.error(e)
    }
    setExecuting(false)
  }

  useEffect(() => { fetchCase() }, [caseId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    )
  }
  if (!data || !data.case) return <div className="text-gray-500">Case not found</div>

  const c = data.case
  const tx = data.transaction
  const audit = data.audit_trail || []

  // Illustrative strategy set (the strategist ranks these by expected value).
  const amt = c.amount_at_risk || 0
  const strategies = [
    { type: 'SMART_RETRY', success_probability: 0.72, expected_recovery: amt * 0.72 },
    { type: 'PAYMENT_LINK', success_probability: 0.84, expected_recovery: amt * 0.84 },
    { type: 'REMINDER', success_probability: 0.58, expected_recovery: amt * 0.58 },
    { type: 'HUMAN_ESCALATION', success_probability: 0.4, expected_recovery: amt * 0.4 },
  ]

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/cases')} className="flex items-center gap-2 text-gray-400 hover:text-white">
        <ArrowLeft className="w-4 h-4" /> Back to Cases
      </button>

      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Case {c.id}</h2>
          <p className="text-gray-400 mt-1">Transaction: {c.transaction_id}</p>
        </div>
        {c.status === 'APPROVED' && (
          <button onClick={execute} disabled={executing} className="btn-primary flex items-center gap-2 disabled:opacity-50">
            <CheckCircle className="w-4 h-4" />
            {executing ? 'Executing…' : 'Execute Recovery'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6 lg:col-span-2">
          <div className="card">
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-400">Amount At Risk</p>
                <p className="text-2xl font-bold text-white">{inr(c.amount_at_risk)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Expected Recovery</p>
                <p className="text-2xl font-bold text-brand-400">{inr(c.expected_recovery)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Status</p>
                <span className={`badge ${
                  c.status === 'SUCCESS' || c.status === 'APPROVED' ? 'badge-success'
                    : c.status === 'REJECTED' || c.status === 'FAILED' ? 'badge-danger'
                    : 'badge-warning'
                }`}>{c.status}</span>
              </div>
            </div>
            {c.escalation_reason && (
              <p className="mt-4 text-sm text-warning-400">⚠ {c.escalation_reason}</p>
            )}
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-5 h-5 text-accent-400" />
              <h3 className="text-lg font-semibold text-white">Root Cause Analysis</h3>
            </div>
            <div className="bg-white/[0.03] rounded-lg p-4 border border-white/[0.08]">
              <div className="flex items-center justify-between gap-3">
                <p className="text-white font-medium">{c.root_cause || 'Analyzing…'}</p>
                {c.explanation_source && (
                  <span className={`badge ${c.explanation_source.startsWith('llm') ? 'badge-success' : ''}`}
                        style={c.explanation_source.startsWith('llm') ? {} : { color: '#9ca3af', borderColor: '#374151' }}>
                    {c.explanation_source.startsWith('llm')
                      ? `⚡ Generated live · ${c.explanation_source.split(':')[1]}`
                      : 'rule-based'}
                  </span>
                )}
              </div>
              {c.root_cause_explanation && (
                <p className="text-sm text-gray-300 mt-2 leading-relaxed">{c.root_cause_explanation}</p>
              )}
              <div className="flex items-center gap-6 mt-3">
                <div>
                  <span className="text-xs text-gray-500">Confidence</span>
                  <p className="text-lg font-bold text-brand-400">
                    {c.root_cause_confidence ? `${(c.root_cause_confidence * 100).toFixed(0)}%` : '—'}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Customer Intent</span>
                  <p className={`text-lg font-bold ${
                    c.customer_intent === 'HIGH' ? 'text-brand-400'
                      : c.customer_intent === 'LOW' ? 'text-danger-400' : 'text-warning-400'
                  }`}>{c.customer_intent || '—'}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-sky-400" />
              <h3 className="text-lg font-semibold text-white">Recovery Strategy</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-brand-500/[0.06] rounded-lg p-4 border border-brand-500/25">
                <p className="text-xs text-gray-400">Selected Strategy</p>
                <p className="text-xl font-bold text-brand-400">{(c.selected_strategy || '—').replace(/_/g, ' ')}</p>
              </div>
              <div className="bg-white/[0.03] rounded-lg p-4 border border-white/[0.08]">
                <p className="text-xs text-gray-400">Recovery Probability</p>
                <p className="text-xl font-bold text-white">
                  {c.recovery_probability ? `${(c.recovery_probability * 100).toFixed(0)}%` : '—'}
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-brand-400" />
              <h3 className="text-lg font-semibold text-white">Safety Evaluation</h3>
            </div>
            <div className="space-y-2">
              {[
                { name: 'Intervention Budget', check: (c.interventions_tried ?? 0) < 2 },
                { name: 'Agent Authority (≤ ₹50,000)', check: c.amount_at_risk <= 50000 },
                { name: 'Duplicate Risk', check: !(c.actual_recovered > 0) || c.status === 'SUCCESS' },
                { name: 'Customer Opt-out', check: !(tx && tx.customer_opted_out) },
                { name: 'Fraud Signal', check: !(tx && tx.fraud_signal === 'high') },
                { name: 'Diagnosis Confidence (≥ 40%)', check: (c.root_cause_confidence || 0) >= 0.4 },
              ].map((item) => (
                <div key={item.name} className="flex items-center justify-between py-2 border-b border-white/[0.06] last:border-0">
                  <span className="text-gray-300">{item.name}</span>
                  {item.check
                    ? <CheckCircle className="w-5 h-5 text-brand-400" />
                    : <XCircle className="w-5 h-5 text-danger-400" />}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <StrategyComparison strategies={strategies} selected={c.selected_strategy} />
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Transaction</h3>
            <div className="space-y-2 text-sm">
              <Row k="ID" v={tx?.id} mono />
              <Row k="Method" v={tx?.payment_method} />
              <Row k="Status" v={tx?.status} />
              <Row k="Failure" v={tx?.failure_reason || '—'} />
              <Row k="Attempts" v={tx?.previous_attempts} />
              <Row k="Fraud" v={tx?.fraud_signal} />
              <Row k="Opted out" v={tx?.customer_opted_out ? 'yes' : 'no'} />
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Case Audit Trail</h3>
        <div className="space-y-2">
          {audit.map((log, i) => (
            <div key={i} className="flex items-center gap-3 text-sm py-2 border-b border-white/[0.06] last:border-0">
              <span className="text-gray-500 font-mono text-xs w-20">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
              </span>
              <span className="font-medium text-gray-300 w-44">{(log.agent || '').replace(/_/g, ' ')}</span>
              <span className="text-gray-400 flex-1">{(log.action || '').replace(/_/g, ' ')}</span>
              <span className={`text-xs ${
                log.status === 'SUCCESS' || log.status === 'APPROVED' ? 'text-brand-400'
                  : log.status === 'REJECTED' || log.status === 'FAILED' ? 'text-danger-400' : 'text-gray-500'
              }`}>{log.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Row({ k, v, mono }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{k}</span>
      <span className={`text-gray-300 ${mono ? 'font-mono' : 'capitalize'}`}>{v ?? '—'}</span>
    </div>
  )
}
