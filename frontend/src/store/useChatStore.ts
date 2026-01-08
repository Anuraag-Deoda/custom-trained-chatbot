import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage } from '../types';
import { sendChatMessage } from '../lib/api';
import { generateId } from '../lib/utils';

interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setError: (error: string | null) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      loading: false,
      error: null,

      sendMessage: async (content) => {
        const userMessage: ChatMessage = {
          id: generateId(),
          content,
          role: 'user',
          timestamp: new Date(),
        };

        set({
          messages: [...get().messages, userMessage],
          loading: true,
          error: null,
        });

        try {
          const result = await sendChatMessage(content);

          const assistantMessage: ChatMessage = {
            id: generateId(),
            content: result.response,
            role: 'assistant',
            timestamp: new Date(),
            analysis: result.analysis,
            matchedJob: result.matched_job,
            similarJobs: result.similar_jobs,
            followUpSuggestions: result.follow_up_suggestions,
          };

          set({
            messages: [...get().messages, assistantMessage],
            loading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to send message',
            loading: false,
          });
        }
      },

      clearMessages: () => set({ messages: [], error: null }),

      setError: (error) => set({ error }),
    }),
    {
      name: 'chat-store',
      partialize: (state) => ({ messages: state.messages }),
    }
  )
);
