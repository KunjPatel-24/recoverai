import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, ListChecks, ShieldCheck, ScrollText, Activity } from 'lucide-react'

import Dashboard from './pages/Dashboard'
import RecoveryCases from './pages/RecoveryCases'
import DecisionView from './pages/DecisionView'
import Safety from './pages/Safety'
import AuditTrail from './pages/AuditTrail'

const nav = [
  { to: '/', label: 'Command Center', icon: LayoutDashboard, end: true },
  { to: '/cases', label: 'Recovery Cases', icon: ListChecks },
  { to: '/safety', label: 'Policy & Safety', icon: ShieldCheck },
  { to: '/audit', label: 'Audit Trail', icon: ScrollText },
]

export default function App() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-white/[0.06] bg-surface-950/60 backdrop-blur-sm p-4 hidden md:flex md:flex-col">
        <div className="flex items-center gap-2.5 px-2 mb-8">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow">
            <Activity className="w-5 h-5 text-surface-950" />
          </div>
          <div>
            <p className="font-bold text-white leading-tight tracking-tight">RecoverAI</p>
            <p className="text-[11px] text-gray-500 leading-tight">Revenue Recovery</p>
          </div>
        </div>
        <nav className="space-y-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-500/15 to-accent-500/10 text-brand-300 border border-brand-500/25 shadow-glow'
                    : 'text-gray-400 border border-transparent hover:text-white hover:bg-white/[0.05]'
                }`
              }
            >
              <n.icon className="w-4 h-4" />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-2 pt-6 text-[11px] text-gray-600">
          Track 03 · Bounded agent · Offline demo
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 min-w-0 overflow-x-hidden p-6 lg:p-8 max-w-[1400px] mx-auto w-full">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cases" element={<RecoveryCases />} />
          <Route path="/cases/:caseId" element={<DecisionView />} />
          <Route path="/safety" element={<Safety />} />
          <Route path="/audit" element={<AuditTrail />} />
        </Routes>
      </main>
    </div>
  )
}
