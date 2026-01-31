import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import type { SearchPhase } from '../types';

interface ThinkingPanelProps {
  reasoning: string;
  routingExplanation: string[];
  phase: SearchPhase;
  isStreaming: boolean;
}

const phaseLabels: Record<string, string> = {
  reasoning: 'Analyzing query...',
  parsing: 'Extracting filters...',
  querying: 'Searching databases...',
  complete: 'Complete',
};

export function ThinkingPanel({ reasoning, routingExplanation, phase, isStreaming }: ThinkingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const reasoningEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to show latest reasoning text
  useEffect(() => {
    if (isStreaming && phase === 'reasoning') {
      reasoningEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [reasoning, isStreaming, phase]);

  return (
    <div className={`thinking-panel ${isStreaming ? 'streaming' : ''}`}>
      <div
        className="thinking-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className={`thinking-icon ${isStreaming ? 'animating' : ''}`}>🧠</span>
        <span className="thinking-title">LLM Thinking</span>
        {isStreaming && phase && (
          <span className="thinking-status">{phaseLabels[phase] || phase}</span>
        )}
        <span className="thinking-toggle">{isExpanded ? '▼' : '▶'}</span>
      </div>

      {isExpanded && (
        <div className="thinking-content">
          {phase && (
            <div className="thinking-phase-indicator">
              <div className={`phase-step ${phase === 'reasoning' || phase === 'parsing' || phase === 'querying' || phase === 'complete' ? 'active' : ''}`}>
                <span className="phase-dot"></span>
                <span>Reasoning</span>
              </div>
              <div className={`phase-step ${phase === 'parsing' || phase === 'querying' || phase === 'complete' ? 'active' : ''}`}>
                <span className="phase-dot"></span>
                <span>Parsing</span>
              </div>
              <div className={`phase-step ${phase === 'querying' || phase === 'complete' ? 'active' : ''}`}>
                <span className="phase-dot"></span>
                <span>Querying</span>
              </div>
              <div className={`phase-step ${phase === 'complete' ? 'active' : ''}`}>
                <span className="phase-dot"></span>
                <span>Results</span>
              </div>
            </div>
          )}

          {reasoning && (
            <div className="thinking-section">
              <div className="thinking-label">Understanding:</div>
              <div className="thinking-reasoning">
                <ReactMarkdown>{reasoning}</ReactMarkdown>
                {isStreaming && phase === 'reasoning' && <span className="cursor">▌</span>}
                <div ref={reasoningEndRef} />
              </div>
            </div>
          )}

          {routingExplanation.length > 0 && (
            <div className="thinking-section">
              <div className="thinking-label">Query Routing:</div>
              <ul className="routing-list">
                {routingExplanation.map((explanation, index) => (
                  <li key={index} className="routing-item">
                    {explanation}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
