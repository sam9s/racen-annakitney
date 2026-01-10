'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Users, Clock, ChevronLeft, RefreshCw, Lock } from 'lucide-react';

interface DashboardStats {
  totalConversations: number;
  totalSessions: number;
  avgResponseTime: number;
  positiveRating: number;
  conversationsByDay: { date: string; count: number }[];
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

export default function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [conversationDetail, setConversationDetail] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');
  const [checkingAuth, setCheckingAuth] = useState(true);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setIsAuthenticated(true);
      } else {
        setLoginError(data.error || 'Invalid password');
      }
    } catch {
      setLoginError('Login failed');
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/admin/session', { credentials: 'include' });
        const data = await res.json();
        setIsAuthenticated(data.authenticated);
      } catch {
        setIsAuthenticated(false);
      }
      setCheckingAuth(false);
    };
    checkAuth();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated, timeRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, sessionsRes] = await Promise.all([
        fetch(`${FLASK_API}/api/admin/stats?range=${timeRange}`),
        fetch(`${FLASK_API}/api/admin/conversations?range=${timeRange}&limit=100`)
      ]);
      
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
      
      if (sessionsRes.ok) {
        const sessionsData = await sessionsRes.json();
        setSessions(sessionsData.sessions || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  const fetchConversationDetail = async (sessionId: string) => {
    setSelectedSession(sessionId);
    try {
      const res = await fetch(`${FLASK_API}/api/admin/conversations/${encodeURIComponent(sessionId)}`);
      if (res.ok) {
        const data = await res.json();
        setConversationDetail(data);
      }
    } catch (error) {
      console.error('Error fetching conversation:', error);
    }
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

  const handleLogout = async () => {
    await fetch('/api/admin/login', { method: 'DELETE', credentials: 'include' });
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#F5F1E8] flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-[#D4AF37]/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-[#D4AF37]" />
            </div>
            <CardTitle className="text-2xl">Anna Admin Dashboard</CardTitle>
            <p className="text-muted-foreground">Enter password to access</p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <Input
                type="password"
                placeholder="Enter admin password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="text-center"
                data-testid="input-admin-password"
              />
              {loginError && (
                <p className="text-red-500 text-sm text-center">{loginError}</p>
              )}
              <Button type="submit" className="w-full bg-[#D4AF37] hover:bg-[#B8962E]" data-testid="button-admin-login">
                Sign In
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F1E8]">
      <header className="bg-white border-b border-[#D4AF37]/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Anna Analytics</h1>
            <p className="text-gray-500 text-sm">Conversation Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              {['24h', '7d', '30d'].map((range) => (
                <Button
                  key={range}
                  variant={timeRange === range ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTimeRange(range)}
                  className={timeRange === range ? 'bg-[#D4AF37] hover:bg-[#B8962E]' : ''}
                  data-testid={`button-range-${range}`}
                >
                  {range === '24h' ? '24h' : range === '7d' ? '7 days' : '30 days'}
                </Button>
              ))}
            </div>
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading} data-testid="button-refresh">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="ghost" size="sm" onClick={handleLogout} data-testid="button-logout">
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-[#D4AF37]/10 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-[#D4AF37]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.totalConversations || 0}</p>
                  <p className="text-sm text-muted-foreground">Total Messages</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-500/10 rounded-lg">
                  <Users className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.totalSessions || 0}</p>
                  <p className="text-sm text-muted-foreground">Sessions</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-500/10 rounded-lg">
                  <Clock className="w-6 h-6 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.avgResponseTime?.toFixed(1) || 0}s</p>
                  <p className="text-sm text-muted-foreground">Avg Response</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-500/10 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-purple-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{sessions.length}</p>
                  <p className="text-sm text-muted-foreground">Recent Sessions</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-lg">Sessions</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[600px]">
                {sessions.length === 0 ? (
                  <div className="p-6 text-center text-muted-foreground">
                    No sessions found
                  </div>
                ) : (
                  <div className="divide-y">
                    {sessions.map((session) => (
                      <button
                        key={session.sessionId}
                        onClick={() => fetchConversationDetail(session.sessionId)}
                        className={`w-full p-4 text-left hover:bg-[#D4AF37]/5 transition-colors ${
                          selectedSession === session.sessionId ? 'bg-[#D4AF37]/10 border-l-4 border-[#D4AF37]' : ''
                        }`}
                        data-testid={`button-session-${session.sessionId}`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <span className="font-medium text-sm truncate">{session.userName}</span>
                          <Badge variant="outline" className="text-xs shrink-0">
                            {session.channel}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground truncate mb-1">
                          {session.firstMessage || 'No messages'}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>{session.messageCount} messages</span>
                          <span>{formatDate(session.lastActivity)}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {conversationDetail ? 'Conversation' : 'Select a session'}
                </CardTitle>
                {conversationDetail && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedSession(null);
                      setConversationDetail(null);
                    }}
                    data-testid="button-close-conversation"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Back
                  </Button>
                )}
              </div>
              {conversationDetail && (
                <div className="flex gap-2 mt-2">
                  <Badge variant="outline">{conversationDetail.session.channel}</Badge>
                  <Badge variant="outline">{conversationDetail.messages.length} messages</Badge>
                  <Badge variant="outline">{formatDate(conversationDetail.session.createdAt)}</Badge>
                </div>
              )}
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[550px]">
                {!conversationDetail ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <div className="text-center">
                      <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Select a session to view the conversation</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {conversationDetail.messages.map((message) => (
                      <div key={message.id} className="space-y-2">
                        <div className="flex justify-end">
                          <div className="bg-[#D4AF37] text-white rounded-2xl rounded-br-md px-4 py-2 max-w-[80%]">
                            <p className="text-sm">{message.userQuestion}</p>
                            <p className="text-xs opacity-70 mt-1">{formatDate(message.timestamp)}</p>
                          </div>
                        </div>
                        <div className="flex justify-start">
                          <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2 max-w-[80%]">
                            <p className="text-sm whitespace-pre-wrap">{message.botAnswer}</p>
                            {message.responseTimeMs && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {(message.responseTimeMs / 1000).toFixed(1)}s response
                              </p>
                            )}
                            {message.safetyFlagged && (
                              <Badge variant="destructive" className="mt-1">Safety Flagged</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
