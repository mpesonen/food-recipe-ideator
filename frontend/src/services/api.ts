import axios from 'axios';
import type { SearchResponse, RecipeResult } from '../types';

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
