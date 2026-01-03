'use client';

import { useState, useEffect } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

interface SomeraStats {
  totalCalls: number;
  totalMessages: number;
  avgLatency: number;
  peakReadiness: number;
  avgReadiness: number;
  bookingRate: number;
  latencyTrends: { date: string; min: number; avg: number; max: number }[];
  readinessDistribution: { explore: number; transition: number; guide: number };
}

interface VoiceCall {
  callId: string;
  startedAt: string;
  endedAt: string;
  messageCount: number;
  avgLatency: number | null;
  peakReadiness: number;
  hadBooking: boolean;
}

interface VoiceMessage {
  role: string;
  content: string;
  readinessScore: number | null;
  readinessRecommendation: string | null;
  latencyMs: number | null;
  closureType: string | null;
  timestamp: string;
  sources: { source: string; topic?: string; youtube_url?: string }[] | null;
}

interface CallDetail {
  callId: string;
  messages: VoiceMessage[];
}

interface AdminUser {
  email: string;
  name: string;
}

const PURPLE_COLORS = ['#a855f7', '#c084fc', '#d8b4fe'];

export default function SomeraAdminDashboard() {
  const { status } = useSession();
  const [activeTab, setActiveTab] = useState<'analytics' | 'transcripts' | 'insights' | 'status'>('analytics');
  const [stats, setStats] = useState<SomeraStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  
  const [calls, setCalls] = useState<VoiceCall[]>([]);
  const [callsLoading, setCallsLoading] = useState(false);
  const [selectedCall, setSelectedCall] = useState<string | null>(null);
  const [callDetail, setCallDetail] = useState<CallDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [newCallsCount, setNewCallsCount] = useState(0);

  useEffect(() => {
    checkAuth();
  }, [status]);

  useEffect(() => {
    if (isAuthenticated && calls.length > 0) {
      const lastViewed = localStorage.getItem('somera_last_viewed_calls');
      if (lastViewed) {
        const lastViewedDate = new Date(lastViewed);
        const newCalls = calls.filter(call => new Date(call.startedAt) > lastViewedDate);
        setNewCallsCount(newCalls.length);
      } else {
        setNewCallsCount(calls.length);
      }
    }
  }, [calls, isAuthenticated]);

  useEffect(() => {
    if (activeTab === 'transcripts' && calls.length > 0) {
      localStorage.setItem('somera_last_viewed_calls', new Date().toISOString());
      setNewCallsCount(0);
    }
  }, [activeTab, calls]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchCalls();
      if (activeTab === 'analytics' || activeTab === 'insights') {
        fetchStats();
      }
    }
  }, [timeRange, activeTab, isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    
    const pollInterval = setInterval(() => {
      fetch(`/api/admin/somera/calls?range=${timeRange}`)
        .then(res => res.ok ? res.json() : null)
        .then(data => data && setCalls(data.calls || []))
        .catch(() => {});
    }, 30000);
    
    return () => clearInterval(pollInterval);
  }, [isAuthenticated, timeRange]);

  const checkAuth = async () => {
    setAuthChecking(true);
    try {
      const res = await fetch('/api/admin/session');
      const data = await res.json();
      if (data.authenticated) {
        setIsAuthenticated(true);
        setAdminUser(data.user);
      } else {
        setIsAuthenticated(false);
        setAdminUser(null);
      }
    } catch {
      setIsAuthenticated(false);
    }
    setAuthChecking(false);
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError('');
    
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      
      const data = await res.json();
      
      if (res.ok && data.success) {
        setIsAuthenticated(true);
        setAdminUser(data.user);
        setLoginEmail('');
        setLoginPassword('');
      } else {
        setLoginError(data.error || 'Invalid credentials');
      }
    } catch {
      setLoginError('Login failed. Please try again.');
    }
    
    setLoginLoading(false);
  };

  const handleLogout = async () => {
    await fetch('/api/admin/login', { method: 'DELETE' });
    await signOut({ redirect: false });
    setIsAuthenticated(false);
    setAdminUser(null);
  };

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/admin/somera/stats?range=${timeRange}`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
    setLoading(false);
  };

  const fetchCalls = async () => {
    setCallsLoading(true);
    try {
      const res = await fetch(`/api/admin/somera/calls?range=${timeRange}`);
      if (res.ok) {
        const data = await res.json();
        setCalls(data.calls || []);
      }
    } catch (error) {
      console.error('Failed to fetch calls:', error);
    }
    setCallsLoading(false);
  };

  const fetchCallDetail = async (callId: string) => {
    setDetailLoading(true);
    setSelectedCall(callId);
    try {
      const res = await fetch(`/api/admin/somera/calls/${encodeURIComponent(callId)}`);
      if (res.ok) {
        const data = await res.json();
        setCallDetail(data);
      }
    } catch (error) {
      console.error('Failed to fetch call detail:', error);
    }
    setDetailLoading(false);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getReadinessBadge = (score: number | null) => {
    if (score === null) return null;
    const percent = Math.round(score * 100);
    let color = 'bg-blue-500/20 text-blue-400';
    let label = 'Explore';
    
    if (score >= 0.35) {
      color = 'bg-green-500/20 text-green-400';
      label = 'Guide';
    } else if (score >= 0.20) {
      color = 'bg-yellow-500/20 text-yellow-400';
      label = 'Transition';
    }
    
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs ${color}`}>
        {label} ({percent}%)
      </span>
    );
  };

  const formatLatency = (ms: number | null) => {
    if (ms === null) return '-';
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatDuration = (startedAt: string, endedAt: string) => {
    if (!startedAt || !endedAt) return '-';
    const start = new Date(startedAt);
    const end = new Date(endedAt);
    const durationMs = end.getTime() - start.getTime();
    if (durationMs < 0) return '-';
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
  };

  if (authChecking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 flex items-center justify-center p-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50 max-w-md w-full">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">SOMERA Voice Analytics</h1>
            <p className="text-gray-400">Sign in to access the dashboard</p>
          </div>

          <form onSubmit={handlePasswordLogin} className="space-y-4 mb-6">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                required
              />
            </div>
            {loginError && (
              <p className="text-red-400 text-sm">{loginError}</p>
            )}
            <button
              type="submit"
              disabled={loginLoading}
              className="w-full bg-purple-500 hover:bg-purple-600 disabled:bg-purple-500/50 text-white font-medium py-3 px-6 rounded-xl transition-colors"
            >
              {loginLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-700"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-gray-800/50 text-gray-500">or</span>
            </div>
          </div>

          <button
            onClick={() => signIn('google')}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-3"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">SOMERA Voice Analytics</h1>
              <p className="text-gray-400 mt-1">Voice coaching performance dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              {['24h', '7d', '30d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    timeRange === range
                      ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/30'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  {range === '24h' ? 'Last 24h' : range === '7d' ? 'Last 7 days' : 'Last 30 days'}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3 pl-4 border-l border-gray-700">
              <div className="text-right">
                <p className="text-sm text-white">{adminUser?.name || 'Admin'}</p>
                <p className="text-xs text-gray-500">{adminUser?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 bg-gray-800 hover:bg-red-500/20 text-gray-400 hover:text-red-400 rounded-lg transition-colors"
                title="Logout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
            <a
              href={`/api/admin/somera/export?range=${timeRange}`}
              className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 hover:text-green-300 rounded-lg text-sm transition-colors flex items-center gap-2"
              download
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export CSV
            </a>
            <a
              href="/admin/dashboard"
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white rounded-lg text-sm transition-colors"
            >
              Jovee Dashboard
            </a>
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'analytics'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Analytics
          </button>
          <button
            onClick={() => setActiveTab('transcripts')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 relative ${
              activeTab === 'transcripts'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Transcripts
            {newCallsCount > 0 && activeTab !== 'transcripts' && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 min-w-5 px-1 flex items-center justify-center animate-pulse">
                {newCallsCount > 9 ? '9+' : newCallsCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'insights'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Insights
          </button>
          <button
            onClick={() => setActiveTab('status')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'status'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Status
          </button>
        </div>

        {activeTab === 'analytics' && (
          <AnalyticsView stats={stats} loading={loading} formatLatency={formatLatency} />
        )}
        {activeTab === 'transcripts' && (
          <TranscriptsView
            calls={calls}
            callsLoading={callsLoading}
            selectedCall={selectedCall}
            callDetail={callDetail}
            detailLoading={detailLoading}
            onSelectCall={fetchCallDetail}
            formatDate={formatDate}
            getReadinessBadge={getReadinessBadge}
            formatLatency={formatLatency}
            formatDuration={formatDuration}
          />
        )}
        {activeTab === 'insights' && (
          <InsightsView stats={stats} loading={loading} />
        )}
        {activeTab === 'status' && (
          <MonitoringView />
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, color = 'purple' }: { 
  title: string; 
  value: string; 
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'purple' | 'green' | 'blue' | 'yellow';
}) {
  const colorClasses = {
    purple: 'bg-purple-500/20 text-purple-400',
    green: 'bg-green-500/20 text-green-400',
    blue: 'bg-blue-500/20 text-blue-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
  };
  
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
          {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function AnalyticsView({ stats, loading, formatLatency }: { 
  stats: SomeraStats | null; 
  loading: boolean;
  formatLatency: (ms: number | null) => string;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  const hasData = stats && stats.totalCalls > 0;

  const readinessData = stats ? [
    { name: 'Explore', value: stats.readinessDistribution.explore, color: '#3b82f6' },
    { name: 'Transition', value: stats.readinessDistribution.transition, color: '#eab308' },
    { name: 'Guide', value: stats.readinessDistribution.guide, color: '#22c55e' },
  ] : [];

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Calls"
          value={stats?.totalCalls?.toString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          }
        />
        <StatCard
          title="Total Messages"
          value={stats?.totalMessages?.toString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          }
          color="blue"
        />
        <StatCard
          title="Avg Response Time"
          value={formatLatency(stats?.avgLatency || 0)}
          subtitle="Target: < 3s"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="yellow"
        />
        <StatCard
          title="Booking Rate"
          value={`${stats?.bookingRate || 0}%`}
          subtitle="Discovery call requests"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
          color="green"
        />
      </div>

      {!hasData ? (
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
          <h3 className="text-xl font-semibold text-white mb-2">No Voice Calls Yet</h3>
          <p className="text-gray-400">Make some voice calls with SOMERA to see analytics here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
            <h2 className="text-xl font-semibold text-white mb-4">Response Latency Trends</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats?.latencyTrends || []}>
                  <defs>
                    <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                  <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `${(v/1000).toFixed(1)}s`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                    formatter={(value: number) => [`${(value/1000).toFixed(2)}s`, '']}
                  />
                  <Area
                    type="monotone"
                    dataKey="avg"
                    stroke="#a855f7"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorLatency)"
                    name="Avg Latency"
                  />
                  <Line type="monotone" dataKey="min" stroke="#22c55e" strokeWidth={1} dot={false} name="Min" />
                  <Line type="monotone" dataKey="max" stroke="#ef4444" strokeWidth={1} dot={false} name="Max" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
            <h2 className="text-xl font-semibold text-white mb-4">Readiness Distribution</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={readinessData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {readinessData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-4">
              {readinessData.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-gray-400">{item.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function TranscriptsView({
  calls,
  callsLoading,
  selectedCall,
  callDetail,
  detailLoading,
  onSelectCall,
  formatDate,
  getReadinessBadge,
  formatLatency,
  formatDuration,
}: {
  calls: VoiceCall[];
  callsLoading: boolean;
  selectedCall: string | null;
  callDetail: CallDetail | null;
  detailLoading: boolean;
  onSelectCall: (callId: string) => void;
  formatDate: (dateStr: string) => string;
  getReadinessBadge: (score: number | null) => React.ReactNode;
  formatLatency: (ms: number | null) => string;
  formatDuration: (startedAt: string, endedAt: string) => string;
}) {
  if (callsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  if (calls.length === 0) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
        <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <h3 className="text-xl font-semibold text-white mb-2">No Transcripts</h3>
        <p className="text-gray-400">Voice call transcripts will appear here.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-1 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 max-h-[calc(100vh-280px)] overflow-y-auto">
        <h2 className="text-lg font-semibold text-white mb-4 px-2">Call History</h2>
        <div className="space-y-2">
          {calls.map((call) => (
            <button
              key={call.callId}
              onClick={() => onSelectCall(call.callId)}
              className={`w-full text-left p-4 rounded-xl transition-all ${
                selectedCall === call.callId
                  ? 'bg-purple-500/20 border border-purple-500/50'
                  : 'bg-gray-700/30 hover:bg-gray-700/50 border border-transparent'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{formatDate(call.startedAt)}</span>
                {call.hadBooking && (
                  <span className="px-2 py-0.5 rounded-full text-xs bg-green-500/20 text-green-400">
                    Booking
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white font-medium">{call.messageCount} messages</span>
                <span className="text-sm text-gray-500">
                  Peak: {Math.round(call.peakReadiness * 100)}%
                </span>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
                <span>Duration: {formatDuration(call.startedAt, call.endedAt)}</span>
                {call.avgLatency && (
                  <span>Latency: {formatLatency(call.avgLatency)}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="lg:col-span-2 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50 max-h-[calc(100vh-280px)] overflow-y-auto">
        {!selectedCall ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a call to view the transcript
          </div>
        ) : detailLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-400"></div>
          </div>
        ) : callDetail ? (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white mb-4">Conversation Transcript</h2>
            {callDetail.messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl ${
                  msg.role === 'user'
                    ? 'bg-blue-500/10 border border-blue-500/20 ml-0 mr-12'
                    : 'bg-purple-500/10 border border-purple-500/20 ml-12 mr-0'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-medium ${
                    msg.role === 'user' ? 'text-blue-400' : 'text-purple-400'
                  }`}>
                    {msg.role === 'user' ? 'User' : 'SOMERA'}
                  </span>
                  <div className="flex items-center gap-2">
                    {msg.role === 'user' && getReadinessBadge(msg.readinessScore)}
                    {msg.role === 'assistant' && msg.latencyMs && (
                      <span className="text-xs text-gray-500">
                        {formatLatency(msg.latencyMs)}
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-gray-200 text-sm">{msg.content}</p>
                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-purple-500/20">
                    <span className="text-xs text-purple-400 font-medium">Inspired by:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {msg.sources.map((src, srcIdx) => (
                        <span key={srcIdx} className="text-xs text-purple-300/80 bg-purple-500/10 px-2 py-0.5 rounded">
                          {src.source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {msg.closureType && (
                  <span className="inline-block mt-2 px-2 py-0.5 rounded-full text-xs bg-gray-700 text-gray-400">
                    {msg.closureType}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function InsightsView({ stats, loading }: { stats: SomeraStats | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  const hasData = stats && stats.totalCalls > 0;

  if (!hasData) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
        <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h3 className="text-xl font-semibold text-white mb-2">No Insights Yet</h3>
        <p className="text-gray-400">Coaching insights will appear after more voice calls.</p>
      </div>
    );
  }

  const totalReadiness = (stats?.readinessDistribution.explore || 0) + 
                        (stats?.readinessDistribution.transition || 0) + 
                        (stats?.readinessDistribution.guide || 0);
  
  const explorePercent = totalReadiness > 0 ? Math.round((stats?.readinessDistribution.explore || 0) / totalReadiness * 100) : 0;
  const transitionPercent = totalReadiness > 0 ? Math.round((stats?.readinessDistribution.transition || 0) / totalReadiness * 100) : 0;
  const guidePercent = totalReadiness > 0 ? Math.round((stats?.readinessDistribution.guide || 0) / totalReadiness * 100) : 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
        <h2 className="text-xl font-semibold text-white mb-6">Coaching Metrics</h2>
        <div className="space-y-6">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Average Readiness Score</span>
              <span className="text-white font-semibold">{stats?.avgReadiness || 0}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-purple-500 rounded-full transition-all duration-500"
                style={{ width: `${stats?.avgReadiness || 0}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Peak Readiness Achieved</span>
              <span className="text-white font-semibold">{stats?.peakReadiness || 0}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500 rounded-full transition-all duration-500"
                style={{ width: `${stats?.peakReadiness || 0}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Booking Conversion Rate</span>
              <span className="text-white font-semibold">{stats?.bookingRate || 0}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-yellow-500 rounded-full transition-all duration-500"
                style={{ width: `${stats?.bookingRate || 0}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
        <h2 className="text-xl font-semibold text-white mb-6">Readiness Zone Analysis</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-blue-500/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl font-bold text-blue-400">{explorePercent}%</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Explore Zone (0-20%)</h3>
              <p className="text-gray-500 text-sm">Users still discovering their needs</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-yellow-500/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl font-bold text-yellow-400">{transitionPercent}%</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Transition Zone (20-35%)</h3>
              <p className="text-gray-500 text-sm">Building clarity and understanding</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-green-500/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl font-bold text-green-400">{guidePercent}%</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Guide Zone (35%+)</h3>
              <p className="text-gray-500 text-sm">Ready for actionable guidance</p>
            </div>
          </div>
        </div>
      </div>

      <div className="lg:col-span-2 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
        <h2 className="text-xl font-semibold text-white mb-4">Readiness Thresholds</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
            <p className="text-3xl font-bold text-blue-400">20%</p>
            <p className="text-gray-400 text-sm mt-1">Transition Threshold</p>
            <p className="text-gray-500 text-xs mt-2">Start blending questions with light guidance</p>
          </div>
          <div className="text-center p-4 bg-yellow-500/10 rounded-xl border border-yellow-500/20">
            <p className="text-3xl font-bold text-yellow-400">35%</p>
            <p className="text-gray-400 text-sm mt-1">Guidance Threshold</p>
            <p className="text-gray-500 text-xs mt-2">Shift to actionable recommendations</p>
          </div>
          <div className="text-center p-4 bg-green-500/10 rounded-xl border border-green-500/20">
            <p className="text-3xl font-bold text-green-400">50%+</p>
            <p className="text-gray-400 text-sm mt-1">High Readiness</p>
            <p className="text-gray-500 text-xs mt-2">Full coaching mode activated</p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface Monitor {
  id: number;
  friendly_name: string;
  url: string;
  status: number;
  custom_uptime_ratio: string;
  response_times: { value: number }[];
  logs: { type: number; datetime: number; duration: number }[];
}

interface MonitoringData {
  stat: string;
  monitors: Monitor[];
  error?: { message: string };
}

function MonitoringView() {
  const [data, setData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const statusMap: { [key: number]: string } = {
    0: 'Paused',
    1: 'Not checked',
    2: 'Up',
    8: 'Seems down',
    9: 'Down',
  };

  const fetchMonitoringData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/monitoring');
      const result = await res.json();
      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
      }
    } catch (err) {
      setError('Failed to fetch monitoring data');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-red-500/30 text-center">
        <svg className="w-12 h-12 mx-auto text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={fetchMonitoringData}
          className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const monitors = data?.monitors || [];

  if (monitors.length === 0) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
        <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <h3 className="text-xl font-semibold text-white mb-2">No Monitors Configured</h3>
        <p className="text-gray-400 mb-4">Set up UptimeRobot monitors to track your production services.</p>
        <a
          href="https://uptimerobot.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-purple-400 hover:text-purple-300"
        >
          Configure monitors at uptimerobot.com →
        </a>
      </div>
    );
  }

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-white">Production Uptime</h2>
        <button
          onClick={fetchMonitoringData}
          className="px-4 py-2 bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {monitors.map((monitor) => {
          const status = monitor.status;
          const uptimeRatios = monitor.custom_uptime_ratio?.split('-') || [];
          const avgResponse = monitor.response_times?.length
            ? Math.round(monitor.response_times.reduce((sum, rt) => sum + rt.value, 0) / monitor.response_times.length)
            : null;

          return (
            <div
              key={monitor.id}
              className={`bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border transition-all ${
                status === 2
                  ? 'border-green-500/30 hover:border-green-500/50'
                  : status === 9 || status === 8
                  ? 'border-red-500/30 hover:border-red-500/50'
                  : 'border-gray-700/50 hover:border-gray-600/50'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-medium truncate pr-2">{monitor.friendly_name}</h3>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    status === 2
                      ? 'bg-green-500/20 text-green-400'
                      : status === 9 || status === 8
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-gray-600/20 text-gray-400'
                  }`}
                >
                  {statusMap[status] || 'Unknown'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-gray-500 text-xs mb-1">24h Uptime</p>
                  <p className="text-2xl font-bold text-white">
                    {uptimeRatios[0] ? `${parseFloat(uptimeRatios[0]).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs mb-1">30d Uptime</p>
                  <p className="text-2xl font-bold text-white">
                    {uptimeRatios[2] ? `${parseFloat(uptimeRatios[2]).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
              </div>

              {avgResponse && (
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Avg response: {avgResponse}ms
                </div>
              )}

              <p className="text-gray-600 text-xs mt-3 truncate">{monitor.url}</p>
            </div>
          );
        })}
      </div>

      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Incidents</h3>
        {monitors.some((m) => m.logs?.some((l) => l.type === 1)) ? (
          <div className="space-y-3">
            {monitors.map((monitor) =>
              monitor.logs
                ?.filter((log) => log.type === 1)
                .slice(0, 3)
                .map((log, idx) => (
                  <div
                    key={`${monitor.id}-${idx}`}
                    className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg border border-red-500/20"
                  >
                    <div>
                      <p className="text-white text-sm">{monitor.friendly_name}</p>
                      <p className="text-gray-400 text-xs">
                        {new Date(log.datetime * 1000).toLocaleString()}
                      </p>
                    </div>
                    <span className="text-red-400 text-sm">
                      Down for {Math.round(log.duration / 60)} min
                    </span>
                  </div>
                ))
            )}
          </div>
        ) : (
          <div className="flex items-center gap-3 text-green-400">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>No incidents in the last 30 days</span>
          </div>
        )}
      </div>
    </>
  );
}
