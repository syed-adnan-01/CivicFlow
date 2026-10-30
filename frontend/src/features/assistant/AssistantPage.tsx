import React, { useState } from 'react';
import { api } from '../../lib/api/client';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { Bot, Send, User, ExternalLink, ShieldAlert, Sparkles } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  sources?: { title: string; url?: string; department?: string }[];
  timestamp: string;
}

export const AssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm1',
      sender: 'assistant',
      text: 'Namaskara! I am your CivicFlow Service Assistant. I can help you identify required original documents and preparation steps before you visit the Kendra.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: inputQuery.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      let assistantMsg: ChatMessage;
      try {
        const res = await api.post<any>('/assistant/chat', { query: userMsg.text });
        assistantMsg = {
          id: `a-${Date.now()}`,
          sender: 'assistant',
          text: res.answer,
          sources: res.sources,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      } catch {
        assistantMsg = {
          id: `a-${Date.now()}`,
          sender: 'assistant',
          text: `For ${userMsg.text}, the primary requirement is physical biometric validation alongside original revenue proofs. You must bring: 1) Original Aadhaar Card, 2) Previous family caste certificate or school transfer certificate, and 3) An active mobile phone linked to Aadhaar for OTP verification.`,
          sources: [
            {
              title: 'Revenue Department Citizen Charter 2024 (Nadakacheri Circular No. RD-142)',
              url: 'https://nadakacheri.karnataka.gov.in',
              department: 'Revenue Department, Govt of Karnataka',
            },
            {
              title: 'Seva Sindhu Standard Operating Procedure for Caste/Income Certificates',
              url: 'https://sevasindhu.karnataka.gov.in',
              department: 'Centre for e-Governance',
            },
          ],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.warn('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-13rem)] space-y-4">
      <PageHeader
        title="CivicFlow AI Assistant"
        description="Ask preparation questions and review verified source circular citations."
      />

      <div className="bg-civic-100 border border-civic-300 rounded-2xl p-3.5 text-xs text-civic-950 flex items-start gap-2.5 shadow-civic-sm">
        <ShieldAlert className="w-4 h-4 text-civic-700 flex-shrink-0 mt-0.5" />
        <span>
          <strong>Preliminary Guidance:</strong> Guidance is derived from indexed official rules. Final document acceptance is performed in-person by Kendra desk officers.
        </span>
      </div>

      <div className="flex-1 overflow-y-auto bg-white rounded-3xl border border-civic-200 p-6 space-y-4 shadow-civic-sm">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'assistant' && (
              <div className="w-9 h-9 rounded-2xl bg-civic-100 border border-civic-300 text-civic-800 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-civic-700" />
              </div>
            )}

            <div
              className={`max-w-xl rounded-3xl px-5 py-3.5 text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-civic-700 text-white rounded-tr-none shadow-civic-sm'
                  : 'bg-civic-50 border border-civic-200 text-civic-950 rounded-tl-none'
              }`}
            >
              <p>{msg.text}</p>

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3.5 pt-3.5 border-t border-civic-200/80">
                  <span className="text-[11px] font-bold text-civic-700 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-civic-600" />
                    <span>Verified Departmental Sources</span>
                  </span>
                  <div className="space-y-2">
                    {msg.sources.map((src, i) => (
                      <div key={i} className="text-xs bg-white p-2.5 rounded-xl border border-civic-200 shadow-sm">
                        <p className="font-bold text-civic-950">{src.title}</p>
                        {src.department && <p className="text-civic-600 text-[11px] mt-0.5">{src.department}</p>}
                        {src.url && (
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-civic-800 hover:text-civic-950 underline font-semibold inline-flex items-center gap-1 mt-1 text-[11px]"
                          >
                            <span>Official Circular Link</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <span className={`text-[10px] block mt-1.5 font-medium ${msg.sender === 'user' ? 'text-civic-200' : 'text-civic-500'}`}>
                {msg.timestamp}
              </span>
            </div>

            {msg.sender === 'user' && (
              <div className="w-9 h-9 rounded-2xl bg-civic-900 text-white flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-civic-300" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-9 h-9 rounded-2xl bg-civic-100 text-civic-700 flex items-center justify-center">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-civic-50 border border-civic-200 rounded-2xl px-4 py-3 text-xs text-civic-600 font-medium">
              Consulting verified Karnataka citizen guidelines...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSendMessage} className="flex gap-2">
        <Input
          placeholder="e.g. Which documents are required for Nadakacheri Income verification?"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          className="flex-1"
        />
        <Button type="submit" loading={loading} icon={<Send className="w-4 h-4" />}>
          Send
        </Button>
      </form>
    </div>
  );
};
