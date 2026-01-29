import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { ConversationMessage } from '../types';

interface RecipeAssistantProps {
  messages: ConversationMessage[];
  isLoading: boolean;
  onSend: (message: string) => void;
}

export function RecipeAssistant({ messages, isLoading, onSend }: RecipeAssistantProps) {
  const [draft, setDraft] = useState('');
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setDraft('');
  };

  return (
    <section className="assistant-shell">
      <div className="assistant-thread" ref={threadRef}>
        {messages.map((message) => (
          <div key={message.id} className={`assistant-bubble ${message.role}`}>
            {message.text}
          </div>
        ))}
      </div>

      <form className="assistant-input" onSubmit={handleSubmit}>
        <label htmlFor="assistant-prompt" className="sr-only">Describe the recipes you want</label>
        <textarea
          id="assistant-prompt"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Describe cravings, ingredients, dietary needs, time limits…"
          rows={3}
          disabled={isLoading}
        />
        <div className="assistant-actions">
          <button type="submit" disabled={isLoading || !draft.trim()}>
            {isLoading ? 'Searching…' : 'Send' }
          </button>
        </div>
      </form>
    </section>
  );
}
