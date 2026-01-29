import { useState } from 'react';
import { SearchBar, RecipeCard, QueryBreakdown } from './components';
import { searchRecipes } from './services/api';
import type { SearchResponse } from './types';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await searchRecipes(query);
      setSearchResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setSearchResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Recipe Ideator</h1>
        <p className="subtitle">
          LLM-powered recipe search using Knowledge Graph + Vector Database
        </p>
      </header>

      <main className="app-main">
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {searchResult && (
          <>
            <QueryBreakdown
              intent={searchResult.parsed_intent}
              sourceBreakdown={searchResult.source_breakdown}
            />

            <div className="results-header">
              <h2>Results for "{searchResult.query}"</h2>
              <span className="results-count">
                {searchResult.results.length} recipes found
              </span>
            </div>

            <div className="results-grid">
              {searchResult.results.map((recipe) => (
                <RecipeCard key={recipe.id} recipe={recipe} />
              ))}
            </div>

            {searchResult.results.length === 0 && (
              <div className="no-results">
                No recipes found. Try a different search query.
              </div>
            )}
          </>
        )}

        {!searchResult && !error && !isLoading && (
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
