import type { RecipeResult } from '../types';

interface RecipeCardProps {
  recipe: RecipeResult;
}

function getSourceBadgeColor(source: string): string {
  switch (source) {
    case 'kg':
      return '#4CAF50'; // Green
    case 'sql':
      return '#2196F3'; // Blue
    case 'vector':
      return '#9C27B0'; // Purple
    case 'sql+vector':
      return '#FF9800'; // Orange
    default:
      return '#757575'; // Gray
  }
}

function formatTime(mins: number | null): string {
  if (!mins) return '-';
  if (mins < 60) return `${mins} min`;
  const hours = Math.floor(mins / 60);
  const remainingMins = mins % 60;
  return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  return (
    <div className="recipe-card">
      <div className="recipe-header">
        <h3 className="recipe-title">{recipe.title}</h3>
        <div className="recipe-sources">
          {recipe.sources.map((source) => (
            <span
              key={source}
              className="source-badge"
              style={{ backgroundColor: getSourceBadgeColor(source) }}
            >
              {source.toUpperCase()}
            </span>
          ))}
        </div>
      </div>

      <p className="recipe-description">
        {recipe.description.length > 200
          ? `${recipe.description.substring(0, 200)}...`
          : recipe.description}
      </p>

      <div className="recipe-meta">
        <div className="meta-item">
          <span className="meta-label">Cuisine:</span>
          <span className="meta-value">{recipe.cuisine || '-'}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Diet:</span>
          <span className="meta-value">{recipe.diet || '-'}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Course:</span>
          <span className="meta-value">{recipe.course || '-'}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Prep:</span>
          <span className="meta-value">{formatTime(recipe.prep_time_mins)}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Cook:</span>
          <span className="meta-value">{formatTime(recipe.cook_time_mins)}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Rating:</span>
          <span className="meta-value">
            {'★'.repeat(Math.round(recipe.rating))}
            {' '}
            ({recipe.rating.toFixed(1)})
          </span>
        </div>
      </div>

      <div className="recipe-ingredients">
        <span className="ingredients-label">Ingredients:</span>
        <span className="ingredients-list">
          {recipe.ingredients.slice(0, 5).join(', ')}
          {recipe.ingredients.length > 5 && ` +${recipe.ingredients.length - 5} more`}
        </span>
      </div>

      <div className="recipe-footer">
        <span className="relevance-score">
          Relevance: {(recipe.final_score * 100).toFixed(0)}%
        </span>
        <a href={recipe.url} target="_blank" rel="noopener noreferrer" className="view-recipe">
          View Recipe →
        </a>
      </div>
    </div>
  );
}
