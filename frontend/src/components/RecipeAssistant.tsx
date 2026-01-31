import { useEffect, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import type { ConversationMessage } from '../types';

const EXAMPLE_QUERIES = [
  { text: "comfort food for a rainy day", label: "Semantic" },
  { text: "healthy lunch under 30 minutes", label: "Time + Health" },
  { text: "something with chicken and rice", label: "Ingredients" },
  { text: "Indian vegetarian dinner", label: "Cuisine + Diet" },
  { text: "easy impressive dessert for guests", label: "Occasion" },
];

interface RecipeAssistantProps {
  messages: ConversationMessage[];
  isLoading: boolean;
  onSend: (message: string) => void;
  assistantTyping: boolean;
}

export function RecipeAssistant({ messages, isLoading, onSend, assistantTyping }: RecipeAssistantProps) {
  const [draft, setDraft] = useState('');
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const submitDraft = () => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setDraft('');
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submitDraft();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !isLoading) {
      event.preventDefault();
      submitDraft();
    }
  };

  return (
    <section className="assistant-shell">
      <div className="assistant-thread" ref={threadRef}>
        {messages.map((message) => (
          <div key={message.id} className={`assistant-bubble ${message.role}`}>
            {message.text}
          </div>
        ))}
        {assistantTyping && (
          <div className="assistant-bubble assistant typing" aria-live="polite">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}
      </div>

      <form className="assistant-input" onSubmit={handleSubmit}>
        <label htmlFor="assistant-prompt" className="sr-only">Describe the recipes you want</label>
        <textarea
          id="assistant-prompt"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Describe cravings, ingredients, dietary needs, time limits…"
          rows={3}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <div className="assistant-actions">
          <button type="submit" disabled={isLoading || !draft.trim()}>
            {isLoading ? 'Searching…' : 'Send' }
          </button>
        </div>
      </form>

      <div className="example-queries">
        <span className="example-label">Try asking:</span>
        <div className="example-buttons">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example.text}
              type="button"
              className="example-button"
              onClick={() => onSend(example.text)}
              disabled={isLoading}
            >
              <span className="example-text">{example.text}</span>
              <span className="example-tag">{example.label}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
