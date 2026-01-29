import { useMemo, useState } from 'react';
import type { ParsedIntent } from '../types';

interface QueryBreakdownProps {
  intent: ParsedIntent;
  sourceBreakdown: Record<string, number>;
}

type PathKey = 'kg' | 'sql' | 'vector' | 'sql+vector';

export function QueryBreakdown({ intent, sourceBreakdown }: QueryBreakdownProps) {
  const [expandedPath, setExpandedPath] = useState<PathKey | null>(null);

  const filters = useMemo(() => {
    const items: string[] = [];
    if (intent.cuisine) items.push(`cuisine=${intent.cuisine}`);
    if (intent.diet) items.push(`diet=${intent.diet}`);
    if (intent.course) items.push(`course=${intent.course}`);
    if (intent.max_prep_time_mins) items.push(`prep ≤ ${intent.max_prep_time_mins}m`);
    if (intent.ingredients_include?.length) items.push(`ingredients include ${intent.ingredients_include.join(', ')}`);
    return items;
  }, [intent]);

  const pathConfigs = useMemo(
    () => [
      {
        key: 'kg' as PathKey,
        label: 'Knowledge Graph',
        icon: '🔗',
        active: intent.use_kg || Boolean(intent.ingredients_include?.length),
        detailTitle: 'Ingredient graph traversal',
        detailBody:
          intent.ingredients_include?.length
            ? `Matched recipes sharing ingredients: ${intent.ingredients_include.join(', ')}.`
            : 'Connected ingredient graph was consulted for similar recipes.',
      },
      {
        key: 'sql' as PathKey,
        label: 'SQL',
        icon: '📊',
        active: intent.use_sql,
        detailTitle: 'Structured filtering in PostgreSQL',
        detailBody: filters.length
          ? `Applied filters → ${filters.join(' · ')}`
          : 'No explicit structured filters were extracted for this query.',
      },
      {
        key: 'vector' as PathKey,
        label: 'Vector',
        icon: '🎯',
        active: intent.use_vector,
        detailTitle: 'Semantic similarity search',
        detailBody: intent.semantic_query
          ? `Embedded semantic query: “${intent.semantic_query}”.`
          : 'Fallback semantic embedding based on cuisine/theme.',
      },
      {
        key: 'sql+vector' as PathKey,
        label: 'SQL+Vector',
        icon: '⚡',
        active: intent.use_sql && intent.use_vector,
        detailTitle: 'Hybrid filter + semantic ranking',
        detailBody: 'Results were filtered via SQL constraints then re-ranked using vector distance.',
      },
    ],
    [filters, intent]
  );

  const activeDetail = pathConfigs.find((path) => path.key === expandedPath && path.active);

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
          {pathConfigs.map((path) => (
            <button
              key={path.key}
              type="button"
              className={`path-item ${path.active ? 'active' : 'inactive'} ${expandedPath === path.key ? 'expanded' : ''}`}
              onClick={() => path.active && setExpandedPath(expandedPath === path.key ? null : path.key)}
              aria-expanded={expandedPath === path.key}
              disabled={!path.active}
            >
              <span className="path-icon" aria-hidden>
                {path.icon}
              </span>
              <span className="path-name">{path.label}</span>
              <span className="path-count">{sourceBreakdown[path.key] || 0}</span>
            </button>
          ))}
        </div>

        {activeDetail && (
          <div className="path-detail">
            <div className="path-detail-title">{activeDetail.detailTitle}</div>
            <p className="path-detail-body">{activeDetail.detailBody}</p>
          </div>
        )}
      </div>
    </div>
  );
}
