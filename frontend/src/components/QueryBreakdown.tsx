import type { ParsedIntent } from '../types';

interface QueryBreakdownProps {
  intent: ParsedIntent;
  sourceBreakdown: Record<string, number>;
}

export function QueryBreakdown({ intent, sourceBreakdown }: QueryBreakdownProps) {
  return (
    <div className="query-breakdown">
      <h4>Query Analysis</h4>

      <div className="breakdown-section">
        <h5>Extracted Filters</h5>
        <div className="filters-grid">
          {intent.cuisine && (
            <div className="filter-item">
              <span className="filter-label">Cuisine:</span>
              <span className="filter-value">{intent.cuisine}</span>
            </div>
          )}
          {intent.diet && (
            <div className="filter-item">
              <span className="filter-label">Diet:</span>
              <span className="filter-value">{intent.diet}</span>
            </div>
          )}
          {intent.course && (
            <div className="filter-item">
              <span className="filter-label">Course:</span>
              <span className="filter-value">{intent.course}</span>
            </div>
          )}
          {intent.max_prep_time_mins && (
            <div className="filter-item">
              <span className="filter-label">Max Prep:</span>
              <span className="filter-value">{intent.max_prep_time_mins} min</span>
            </div>
          )}
          {intent.ingredients_include && intent.ingredients_include.length > 0 && (
            <div className="filter-item">
              <span className="filter-label">Ingredients:</span>
              <span className="filter-value">{intent.ingredients_include.join(', ')}</span>
            </div>
          )}
          {intent.semantic_query && (
            <div className="filter-item">
              <span className="filter-label">Semantic:</span>
              <span className="filter-value">"{intent.semantic_query}"</span>
            </div>
          )}
        </div>
      </div>

      <div className="breakdown-section">
        <h5>Query Paths Used</h5>
        <div className="paths-grid">
          <div className={`path-item ${intent.use_kg ? 'active' : 'inactive'}`}>
            <span className="path-icon">🔗</span>
            <span className="path-name">Knowledge Graph</span>
            <span className="path-count">{sourceBreakdown['kg'] || 0}</span>
          </div>
          <div className={`path-item ${intent.use_sql ? 'active' : 'inactive'}`}>
            <span className="path-icon">📊</span>
            <span className="path-name">SQL</span>
            <span className="path-count">{sourceBreakdown['sql'] || 0}</span>
          </div>
          <div className={`path-item ${intent.use_vector ? 'active' : 'inactive'}`}>
            <span className="path-icon">🎯</span>
            <span className="path-name">Vector</span>
            <span className="path-count">{sourceBreakdown['vector'] || 0}</span>
          </div>
          <div className={`path-item ${intent.use_sql && intent.use_vector ? 'active' : 'inactive'}`}>
            <span className="path-icon">⚡</span>
            <span className="path-name">SQL+Vector</span>
            <span className="path-count">{sourceBreakdown['sql+vector'] || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
