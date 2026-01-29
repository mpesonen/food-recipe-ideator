import axios from 'axios';
import type { SearchResponse, RecipeResult, StreamEvent } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function searchRecipes(query: string, limit: number = 20): Promise<SearchResponse> {
  const response = await api.post<SearchResponse>('/search', { query, limit });
  return response.data;
}

export async function getRecipe(id: number): Promise<RecipeResult> {
  const response = await api.get<RecipeResult>(`/recipes/${id}`);
  return response.data;
}

export async function healthCheck(): Promise<{ status: string; message: string }> {
  const response = await api.get('/health');
  return response.data;
}

export async function fetchRecipePreview(recipeUrl: string): Promise<string> {
  const response = await api.get<{ image_url: string }>('/recipes/preview', {
    params: { url: recipeUrl },
  });
  return response.data.image_url;
}

export async function searchRecipesStream(
  query: string,
  onEvent: (event: StreamEvent) => void,
  limit: number = 20
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/search-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit }),
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const eventStr of events) {
        if (!eventStr.trim()) continue;

        const lines = eventStr.split('\n');
        let eventType = '';
        let eventData = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7);
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6);
          }
        }

        if (eventType && eventData) {
          try {
            onEvent({ type: eventType as StreamEvent['type'], data: JSON.parse(eventData) });
          } catch {
            console.error('Failed to parse SSE data:', eventData);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
