import { useState } from 'react';
import { RecipeAssistant, RecipeCard, QueryBreakdown, ThinkingPanel } from './components';
import { searchRecipesStream } from './services/api';
import type {
  StreamingState,
  ParsedIntent,
  RecipeResult,
  SearchPhase,
  ConversationMessage,
} from './types';
import './App.css';

const initialStreamingState: StreamingState = {
  phase: null,
  reasoning: '',
  routingExplanation: [],
  parsedIntent: null,
  results: [],
  sourceBreakdown: {},
};

type PhaseKey = Exclude<SearchPhase, null> | 'initial';

const phaseMessages: Record<PhaseKey, { title: string; subtitle: string }> = {
  initial: {
    title: 'Starting your search',
    subtitle: 'Preparing LLM reasoning and query planning',
  },
  reasoning: {
    title: 'Analyzing your request',
    subtitle: 'Breaking down intent and understanding context',
  },
  parsing: {
    title: 'Extracting filters and constraints',
    subtitle: 'Identifying cuisines, diets, time limits, and ingredients',
  },
  querying: {
    title: 'Querying data sources',
    subtitle: 'Combining Knowledge Graph, SQL, and vector search',
  },
  complete: {
    title: 'Finalizing results',
    subtitle: 'Scoring and fusing the best matches',
  },
};

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<string>('');
  const [streaming, setStreaming] = useState<StreamingState>(initialStreamingState);
  const [conversation, setConversation] = useState<ConversationMessage[]>([
    {
      id: 'assistant-greeting-1',
      role: 'assistant',
      text: 'Hey there, I’m your personal flavor scout. I comb through our knowledge graph, SQL pantry, and semantic lab to find recipes that match your mood.',
    },
    {
      id: 'assistant-greeting-2',
      role: 'assistant',
      text: 'Tell me what you’re craving—ingredients on hand, dietary needs, time limits, or the vibe you want—and I’ll go figure out the best plan.',
    },
  ]);

  const handleSearch = async (searchQuery: string) => {
    setIsLoading(true);
    setError(null);
    setQuery(searchQuery);
    setStreaming(initialStreamingState);

    try {
      await searchRecipesStream(searchQuery, (event) => {
        switch (event.type) {
          case 'phase':
            setStreaming(s => ({ ...s, phase: event.data.phase ?? null }));
            break;
          case 'reasoning_chunk':
            setStreaming(s => ({ ...s, reasoning: s.reasoning + (event.data.text || '') }));
            break;
          case 'intent':
            setStreaming(s => ({
              ...s,
              parsedIntent: event.data.parsed_intent as ParsedIntent,
              routingExplanation: event.data.routing_explanation || [],
            }));
            break;
          case 'results':
            setStreaming(s => ({
              ...s,
              results: event.data.results as RecipeResult[],
              sourceBreakdown: event.data.source_breakdown || {},
            }));
            setIsLoading(false);
            break;
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setStreaming(initialStreamingState);
      setIsLoading(false);
    }
  };

  const createMessage = (role: ConversationMessage['role'], text: string): ConversationMessage => ({
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    role,
    text,
  });

  const handleAssistantSubmit = (userText: string) => {
    const trimmed = userText.trim();
    if (!trimmed) return;
    setConversation((prev) => [...prev, createMessage('user', trimmed)]);
    const acknowledgment = `Got it. I’ll sift through the recipe graph and report back with ideas for “${trimmed}”.`;
    setConversation((prev) => [...prev, createMessage('assistant', acknowledgment)]);
    handleSearch(trimmed);
  };

  const hasResults = streaming.results.length > 0 || streaming.phase !== null;
  const isStreaming = isLoading && streaming.phase !== 'complete';
  const currentPhaseKey = (streaming.phase ?? 'initial') as PhaseKey;
  const currentPhase = phaseMessages[currentPhaseKey];
  const showSkeleton = isLoading && streaming.results.length === 0;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Recipe Ideator</h1>
        <p className="subtitle">
          LLM-powered recipe search using Knowledge Graph + Vector Database
        </p>
      </header>

      <main className="app-main">
        <RecipeAssistant
          messages={conversation}
          isLoading={isLoading}
          onSend={handleAssistantSubmit}
        />

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {(streaming.phase || streaming.reasoning) && (
          <ThinkingPanel
            reasoning={streaming.reasoning}
            routingExplanation={streaming.routingExplanation}
            phase={streaming.phase}
            isStreaming={isStreaming}
          />
        )}

        {streaming.parsedIntent && (
          <QueryBreakdown
            intent={streaming.parsedIntent}
            sourceBreakdown={streaming.sourceBreakdown}
          />
        )}

        {isLoading && (
          <div className="results-status">
            <div className="loading-spinner" aria-hidden />
            <div>
              <div className="status-title">{currentPhase.title}</div>
              <div className="status-subtitle">{currentPhase.subtitle}</div>
            </div>
          </div>
        )}

        {showSkeleton && (
          <div className="results-skeleton" aria-hidden>
            {[0, 1, 2].map((index) => (
              <div className="skeleton-card" key={`skeleton-${index}`}>
                <div className="skeleton-thumb" />
                <span className="skeleton-line long" />
                <span className="skeleton-line" />
                <span className="skeleton-line short" />
                <span className="skeleton-line extra-short" />
              </div>
            ))}
          </div>
        )}

        {streaming.results.length > 0 && (
          <>
            <div className="results-header">
              <h2>Results for "{query}"</h2>
              <span className="results-count">
                {streaming.results.length} recipes found
              </span>
            </div>

            <div className="results-grid">
              {streaming.results.map((recipe) => (
                <RecipeCard key={recipe.id} recipe={recipe} />
              ))}
            </div>
          </>
        )}

        {streaming.phase === 'complete' && streaming.results.length === 0 && (
          <div className="no-results">
            No recipes found. Try a different search query.
          </div>
        )}

        {!hasResults && !error && !isLoading && (
          <div className="welcome-message">
            <h2>Welcome to Recipe Ideator!</h2>
            <p>
              Search for recipes using natural language. The system combines:
            </p>
            <ul>
              <li><strong>Knowledge Graph (Neo4j)</strong> - for ingredient relationships</li>
              <li><strong>SQL (PostgreSQL)</strong> - for structured filters</li>
              <li><strong>Vector Search (pgvector)</strong> - for semantic similarity</li>
            </ul>
            <p>Try queries like "Indian vegetarian quick" or "comfort food for dinner"</p>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Recipe Ideator - CV Demo Project</p>
      </footer>
    </div>
  );
}

export default App;
