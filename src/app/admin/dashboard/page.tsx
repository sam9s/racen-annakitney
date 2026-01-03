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
} from 'recharts';

interface DashboardStats {
  totalConversations: number;
  totalSessions: number;
  avgResponseTime: number;
  positiveRating: number;
  conversationsByDay: { date: string; count: number }[];
  topQueries: { query: string; count: number }[];
  channelDistribution: { channel: string; count: number }[];
}

interface ChatSession {
  sessionId: string;
  userName: string;
  userEmail: string | null;
  channel: string;
  messageCount: number;
  firstMessage: string;
  createdAt: string;
  lastActivity: string;
}

interface ChatMessage {
  id: number;
  userQuestion: string;
  botAnswer: string;
  timestamp: string;
  safetyFlagged: boolean;
  responseTimeMs: number | null;
}

interface ConversationDetail {
  session: {
    sessionId: string;
    userName: string;
    userEmail: string | null;
    channel: string;
    createdAt: string;
    lastActivity: string;
  };
  messages: ChatMessage[];
}

interface AdminUser {
  email: string;
  name: string;
}

const COLORS = ['#03a9f4', '#4fc3f7', '#81d4fa', '#b3e5fc'];

export default function AdminDashboard() {
  const { status } = useSession();
  const [activeTab, setActiveTab] = useState<'analytics' | 'conversations' | 'monitoring' | 'transcription'>('analytics');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');
  const [authError, setAuthError] = useState(false);
  
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [conversationDetail, setConversationDetail] = useState<ConversationDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  useEffect(() => {
    checkAuth();
  }, [status]);

  useEffect(() => {
    if (isAuthenticated) {
      if (activeTab === 'analytics') {
        fetchStats();
      } else {
        fetchSessions();
      }
    }
  }, [timeRange, activeTab, isAuthenticated]);

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
    setAuthError(false);
    try {
      const res = await fetch(`/api/admin/stats?range=${timeRange}`);
      if (res.status === 401 || res.status === 403) {
        setAuthError(true);
        setLoading(false);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
    setLoading(false);
  };

  const fetchSessions = async () => {
    setSessionsLoading(true);
    setAuthError(false);
    try {
      const res = await fetch(`/api/admin/conversations?range=${timeRange}`);
      if (res.status === 401 || res.status === 403) {
        setAuthError(true);
        setSessionsLoading(false);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
    setSessionsLoading(false);
  };

  const fetchConversationDetail = async (sessionId: string) => {
    setDetailLoading(true);
    setSelectedSession(sessionId);
    try {
      const res = await fetch(`/api/admin/conversations/${encodeURIComponent(sessionId)}`);
      if (res.ok) {
        const data = await res.json();
        setConversationDetail(data);
      }
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
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

  const getChannelBadgeColor = (channel: string) => {
    switch (channel.toLowerCase()) {
      case 'widget':
        return 'bg-purple-500/20 text-purple-400';
      case 'whatsapp':
        return 'bg-green-500/20 text-green-400';
      case 'instagram':
        return 'bg-pink-500/20 text-pink-400';
      default:
        return 'bg-cyan-500/20 text-cyan-400';
    }
  };

  if (authChecking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50 max-w-md w-full">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-cyan-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Anna Analytics</h1>
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
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
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
                className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
            {loginError && (
              <p className="text-red-400 text-sm">{loginError}</p>
            )}
            <button
              type="submit"
              disabled={loginLoading}
              className="w-full bg-cyan-500 hover:bg-cyan-600 disabled:bg-cyan-500/50 text-white font-medium py-3 px-6 rounded-xl transition-colors"
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

  if (authError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Access Denied</h1>
          <p className="text-gray-400 mb-4">You don&apos;t have permission to access this dashboard.</p>
          <p className="text-gray-500 text-sm">Contact the administrator to request access.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Anna Analytics</h1>
            <p className="text-gray-400 mt-1">Real-time chatbot performance dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              {['24h', '7d', '30d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    timeRange === range
                      ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
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
              href="/admin/anna"
              className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 hover:text-purple-300 rounded-lg text-sm transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              Anna Voice
            </a>
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'analytics'
                ? 'bg-cyan-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Analytics
          </button>
          <button
            onClick={() => setActiveTab('conversations')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'conversations'
                ? 'bg-cyan-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Conversations
          </button>
          <button
            onClick={() => setActiveTab('monitoring')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'monitoring'
                ? 'bg-cyan-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Monitoring
          </button>
          <button
            onClick={() => setActiveTab('transcription')}
            className={`px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
              activeTab === 'transcription'
                ? 'bg-cyan-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            Transcription
          </button>
        </div>

        {activeTab === 'analytics' ? (
          <AnalyticsView stats={stats} loading={loading} />
        ) : activeTab === 'conversations' ? (
          <ConversationsView
            sessions={sessions}
            sessionsLoading={sessionsLoading}
            selectedSession={selectedSession}
            conversationDetail={conversationDetail}
            detailLoading={detailLoading}
            onSelectSession={fetchConversationDetail}
            formatDate={formatDate}
            getChannelBadgeColor={getChannelBadgeColor}
          />
        ) : activeTab === 'monitoring' ? (
          <MonitoringView />
        ) : (
          <TranscriptionView />
        )}
      </div>
    </div>
  );
}

function AnalyticsView({ stats, loading }: { stats: DashboardStats | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  const hasData = stats && (stats.totalConversations > 0 || stats.totalSessions > 0);

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Conversations"
          value={stats?.totalConversations?.toLocaleString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          }
        />
        <StatCard
          title="Unique Sessions"
          value={stats?.totalSessions?.toLocaleString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        />
        <StatCard
          title="Avg Response Time"
          value={`${stats?.avgResponseTime?.toFixed(1) || '0'}s`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Satisfaction Rate"
          value={stats?.positiveRating ? `${stats.positiveRating}%` : 'N/A'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {!hasData ? (
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="text-xl font-semibold text-white mb-2">No Data Yet</h3>
          <p className="text-gray-400">Start chatting with Anna to see analytics here.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
              <h2 className="text-xl font-semibold text-white mb-4">Conversation Trends</h2>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stats?.conversationsByDay || []}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#03a9f4" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#03a9f4" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                    <YAxis stroke="#9ca3af" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#fff',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="#03a9f4"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorCount)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
              <h2 className="text-xl font-semibold text-white mb-4">Channel Distribution</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats?.channelDistribution || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="count"
                    >
                      {stats?.channelDistribution?.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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
              <div className="flex justify-center gap-4 mt-4 flex-wrap">
                {stats?.channelDistribution?.map((item, index) => (
                  <div key={item.channel} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm text-gray-400">{item.channel} ({item.count})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function ConversationsView({
  sessions,
  sessionsLoading,
  selectedSession,
  conversationDetail,
  detailLoading,
  onSelectSession,
  formatDate,
  getChannelBadgeColor,
}: {
  sessions: ChatSession[];
  sessionsLoading: boolean;
  selectedSession: string | null;
  conversationDetail: ConversationDetail | null;
  detailLoading: boolean;
  onSelectSession: (sessionId: string) => void;
  formatDate: (date: string) => string;
  getChannelBadgeColor: (channel: string) => string;
}) {
  if (sessionsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
        <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <h3 className="text-xl font-semibold text-white mb-2">No Conversations Yet</h3>
        <p className="text-gray-400">Conversations will appear here once users start chatting with Anna.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 overflow-hidden">
        <div className="p-4 border-b border-gray-700/50">
          <h2 className="text-lg font-semibold text-white">Chat Sessions ({sessions.length})</h2>
        </div>
        <div className="max-h-[600px] overflow-y-auto">
          {sessions.map((session) => (
            <button
              key={session.sessionId}
              onClick={() => onSelectSession(session.sessionId)}
              className={`w-full p-4 text-left border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors ${
                selectedSession === session.sessionId ? 'bg-cyan-500/10 border-l-2 border-l-cyan-500' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white text-sm font-medium">
                    {session.userName.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-white font-medium text-sm">{session.userName}</p>
                    {session.userEmail && (
                      <p className="text-gray-500 text-xs">{session.userEmail}</p>
                    )}
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getChannelBadgeColor(session.channel)}`}>
                  {session.channel}
                </span>
              </div>
              <p className="text-gray-400 text-sm line-clamp-2 mb-2">{session.firstMessage || 'No messages'}</p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{session.messageCount} messages</span>
                <span>{formatDate(session.lastActivity)}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 overflow-hidden">
        {!selectedSession ? (
          <div className="h-full flex items-center justify-center p-12 text-center">
            <div>
              <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
              <p className="text-gray-400">Select a conversation to view details</p>
            </div>
          </div>
        ) : detailLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
          </div>
        ) : conversationDetail ? (
          <>
            <div className="p-4 border-b border-gray-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">{conversationDetail.session.userName}</h2>
                  <p className="text-sm text-gray-400">
                    {conversationDetail.session.userEmail || 'Anonymous user'} • {conversationDetail.session.channel}
                  </p>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>Started: {formatDate(conversationDetail.session.createdAt)}</p>
                  <p>Last active: {formatDate(conversationDetail.session.lastActivity)}</p>
                </div>
              </div>
            </div>
            <div className="p-4 max-h-[520px] overflow-y-auto space-y-4">
              {conversationDetail.messages.map((msg) => (
                <div key={msg.id} className="space-y-3">
                  <div className="flex justify-end">
                    <div className="max-w-[80%] bg-cyan-500/20 rounded-2xl rounded-tr-sm px-4 py-3">
                      <p className="text-white text-sm">{msg.userQuestion}</p>
                      <p className="text-xs text-gray-500 mt-1 text-right">{formatDate(msg.timestamp)}</p>
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="max-w-[80%] bg-gray-700/50 rounded-2xl rounded-tl-sm px-4 py-3">
                      <p className="text-gray-200 text-sm whitespace-pre-wrap">{msg.botAnswer}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {msg.safetyFlagged && (
                          <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded">Safety flagged</span>
                        )}
                        {msg.responseTimeMs && (
                          <span className="text-xs text-gray-500">{(msg.responseTimeMs / 1000).toFixed(1)}s</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50 hover:border-cyan-500/30 transition-all hover:shadow-lg hover:shadow-cyan-500/5">
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-cyan-500/10 rounded-xl text-cyan-400">{icon}</div>
      </div>
      <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
      <p className="text-3xl font-bold text-white mt-1">{value}</p>
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

function TranscriptionView() {
  const [file, setFile] = useState<File | null>(null);
  const [outputName, setOutputName] = useState('');
  const [transcribing, setTranscribing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setOutputName(selectedFile.name.replace(/\.[^/.]+$/, ''));
      setError('');
    }
  };

  const handleTranscribe = async () => {
    if (!file) return;

    setTranscribing(true);
    setProgress(10);
    setError('');
    setTranscript('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('outputName', outputName);

      setProgress(30);

      const response = await fetch('/api/admin/transcription', {
        method: 'POST',
        body: formData,
      });

      setProgress(80);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Transcription failed');
      }

      const result = await response.json();
      setTranscript(result.transcript);
      setProgress(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transcription failed');
    } finally {
      setTranscribing(false);
    }
  };

  const handleDownload = () => {
    if (!transcript) return;
    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${outputName}_transcript.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = async () => {
    if (!transcript) return;
    await navigator.clipboard.writeText(transcript);
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
        <h2 className="text-xl font-semibold text-white mb-4">Video/Audio Transcription</h2>
        <p className="text-gray-400 mb-6">
          Upload a video or audio file to transcribe it using OpenAI Whisper. 
          Supported formats: MP4, MOV, AVI, MKV, MP3, WAV, M4A, OGG, WebM
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Select File</label>
            <input
              type="file"
              accept=".mp4,.mov,.avi,.mkv,.mp3,.wav,.m4a,.ogg,.webm"
              onChange={handleFileChange}
              className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-cyan-500 file:text-white file:cursor-pointer hover:file:bg-cyan-600"
            />
          </div>

          {file && (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Output Name</label>
                <input
                  type="text"
                  value={outputName}
                  onChange={(e) => setOutputName(e.target.value)}
                  placeholder="transcript_name"
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center gap-4">
                <p className="text-gray-400 text-sm">
                  📁 {file.name} ({(file.size / (1024 * 1024)).toFixed(1)} MB)
                </p>
              </div>

              <button
                onClick={handleTranscribe}
                disabled={transcribing}
                className="w-full bg-cyan-500 hover:bg-cyan-600 disabled:bg-cyan-500/50 text-white font-medium py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {transcribing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                    Transcribing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    Transcribe
                  </>
                )}
              </button>
            </>
          )}

          {transcribing && (
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-cyan-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          )}

          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}
        </div>
      </div>

      {transcript && (
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Transcript</h3>
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </button>
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download
              </button>
            </div>
          </div>
          <textarea
            value={transcript}
            readOnly
            className="w-full h-96 bg-gray-900/50 border border-gray-700 rounded-lg p-4 text-gray-200 font-mono text-sm resize-none focus:outline-none"
          />
        </div>
      )}
    </div>
  );
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
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
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
          className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
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
          className="text-cyan-400 hover:text-cyan-300"
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
            No incidents recorded. All systems operational.
          </div>
        )}
      </div>
    </>
  );
}
