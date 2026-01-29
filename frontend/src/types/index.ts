export interface ParsedIntent {
  cuisine: string | null;
  diet: string | null;
  course: string | null;
  max_prep_time_mins: number | null;
  max_cook_time_mins: number | null;
  ingredients_include: string[] | null;
  ingredients_exclude: string[] | null;
  semantic_query: string | null;
  use_kg: boolean;
  use_sql: boolean;
  use_vector: boolean;
}

export interface RecipeResult {
  id: number;
  title: string;
  description: string;
  url: string;
  cuisine: string | null;
  course: string | null;
  diet: string | null;
  prep_time_mins: number | null;
  cook_time_mins: number | null;
  rating: number;
  vote_count: number;
  ingredients: string[];
  final_score: number;
  sources: string[];
}

export interface SearchResponse {
  query: string;
  parsed_intent: ParsedIntent;
  results: RecipeResult[];
  source_breakdown: Record<string, number>;
}
