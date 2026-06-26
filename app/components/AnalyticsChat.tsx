'use client';

import { useState, useRef, useEffect } from 'react';

interface DashboardData {
  timestamp: string;
  daily: {
    total_posts: number;
    total_reach: number;
    total_revenue: number;
    platforms: Array<{
      platform: string;
      posts: number;
      reach: number;
      revenue: number;
      engagement_rate: number;
    }>;
  };
  summary: {
    average_revenue_per_post: number;
    revenue_per_platform: Record<string, number>;
  };
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function AnalyticsChat({ data }: { data: DashboardData }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your ProfitEngine AI Assistant. Ask me anything about your analytics, revenue, platform performance, or optimization strategies. I can analyze trends, provide insights, and make recommendations.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch('/api/chat/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          context: data,
          conversationHistory: messages,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: result.response },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'I encountered an error processing your request. Please try again.',
          },
        ]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Connection error. Please check your connection and try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl border border-slate-700/50 backdrop-blur-sm overflow-hidden flex flex-col h-[600px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-slate-700/50 px-6 py-4">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <span className="text-2xl">🤖</span> AI Analytics Assistant
        </h2>
        <p className="text-xs text-gray-400 mt-1">Powered by Claude AI</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600/30 border border-blue-500/50 text-white'
                  : 'bg-slate-700/50 border border-slate-600/50 text-gray-100'
              }`}
            >
              <p className="text-sm leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-700/50 p-4 bg-slate-900/50">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about revenue, platforms, trends..."
            className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded-lg text-white text-sm font-semibold transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
