import { useEffect, useRef, useState } from 'react';
import type { RecipeResult } from '../types';
import { fetchRecipePreview } from '../services/api';

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

function buildFallbackImage(): string {
  return 'https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=600&q=80';
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const placeholder = buildFallbackImage();
  const [previewUrl, setPreviewUrl] = useState<string | null>(recipe.image_url ?? null);
  const [previewError, setPreviewError] = useState(false);
  const [shouldLoad, setShouldLoad] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageSrc = (previewUrl ?? recipe.image_url) || placeholder;

  useEffect(() => {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      setShouldLoad(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting) {
          setShouldLoad(true);
          observer.disconnect();
        }
      },
      { rootMargin: '200px', threshold: 0.1 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!shouldLoad || previewUrl || previewError || !recipe.url) {
      return;
    }

    let cancelled = false;

    fetchRecipePreview(recipe.url)
      .then((url) => {
        if (!cancelled && url) {
          setPreviewUrl(url);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPreviewError(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [shouldLoad, previewUrl, previewError, recipe.url]);

  return (
    <div className="recipe-card">
      <div
        className={`recipe-image ${isLoaded ? 'loaded' : ''}`}
        ref={containerRef}
      >
        {shouldLoad && (
          <img
            src={imageSrc}
            alt={recipe.title}
            loading="lazy"
            onLoad={() => setIsLoaded(true)}
            onError={(event) => {
              if (event.currentTarget.src !== placeholder) {
                event.currentTarget.src = placeholder;
              }
            }}
          />
        )}
      </div>

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
