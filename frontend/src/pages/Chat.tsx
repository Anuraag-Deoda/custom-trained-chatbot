import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Trash2, User, Bot, Sparkles, ArrowRight, GitCompare, Lightbulb, TrendingUp, Users, Target } from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { useChatStore } from '../store/useChatStore';
import type { FollowUpSuggestion } from '../types';

const initialSuggestions = [
  'Tell me about Data Scientist roles',
  'What skills do Financial Managers need?',
  'Compare Software Developer and Data Analyst',
  'What are the key abilities for Project Managers?',
];

// Helper function to get icon for suggestion type
const getSuggestionIcon = (type: FollowUpSuggestion['type']) => {
  switch (type) {
    case 'compare':
      return <GitCompare className="w-3.5 h-3.5" />;
    case 'skills':
      return <Lightbulb className="w-3.5 h-3.5" />;
    case 'career':
      return <TrendingUp className="w-3.5 h-3.5" />;
    case 'similar':
      return <Users className="w-3.5 h-3.5" />;
    case 'gap_analysis':
      return <Target className="w-3.5 h-3.5" />;
    default:
      return <ArrowRight className="w-3.5 h-3.5" />;
  }
};

export default function Chat() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { messages, loading, sendMessage, clearMessages } = useChatStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const message = input.trim();
    setInput('');
    await sendMessage(message);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  const handleFollowUpClick = async (suggestion: FollowUpSuggestion) => {
    // For gap analysis, we could navigate to a different page or show a modal
    // For now, we'll send the action as a new message
    if (suggestion.type === 'gap_analysis') {
      // Could navigate to skill mapper page with pre-selected job
      setInput(suggestion.text);
      inputRef.current?.focus();
    } else {
      // Send the action as a new message
      await sendMessage(suggestion.action);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            AI Chat Assistant
          </h1>
          <p className="text-gray-500 mt-1">
            Ask questions about any job role or competency
          </p>
        </div>
        {messages.length > 0 && (
          <Button variant="outline" onClick={clearMessages}>
            <Trash2 className="w-4 h-4" />
            Clear Chat
          </Button>
        )}
      </div>

      {/* Chat Container */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Welcome to Competency Chat
              </h3>
              <p className="text-gray-500 max-w-md mb-6">
                Ask me anything about job roles, skills, competencies, or career paths.
                I can help you understand what it takes to succeed in any role.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {initialSuggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-700 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg flex items-center justify-center shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div className="flex flex-col gap-2 max-w-[80%]">
                    <div
                      className={`px-4 py-3 rounded-2xl ${
                        message.role === 'user'
                          ? 'bg-primary-600 text-white rounded-br-md'
                          : 'bg-gray-100 text-gray-900 rounded-bl-md'
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">
                        {message.content}
                      </p>
                      <p
                        className={`text-xs mt-2 ${
                          message.role === 'user' ? 'text-white/60' : 'text-gray-400'
                        }`}
                      >
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                    </div>

                    {/* Follow-up Suggestions - Only show for assistant messages */}
                    {message.role === 'assistant' && message.followUpSuggestions && message.followUpSuggestions.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="flex flex-wrap gap-2 mt-1"
                      >
                        {message.followUpSuggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleFollowUpClick(suggestion)}
                            disabled={loading}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 hover:border-primary-300 hover:bg-primary-50 rounded-full text-xs font-medium text-gray-700 hover:text-primary-700 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {getSuggestionIcon(suggestion.type)}
                            {suggestion.text}
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </div>
                  {message.role === 'user' && (
                    <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center shrink-0">
                      <User className="w-5 h-5 text-gray-600" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          )}

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  />
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input */}
        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about any job role or skill..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              disabled={loading}
            />
            <Button type="submit" disabled={!input.trim() || loading} loading={loading}>
              <Send className="w-5 h-5" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
