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
  image_url?: string | null;
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

export interface ThinkingData {
  reasoning: string | null;
  routing_explanation: string[];
}

export interface SearchResponse {
  query: string;
  parsed_intent: ParsedIntent;
  results: RecipeResult[];
  source_breakdown: Record<string, number>;
  thinking: ThinkingData;
}

// Streaming types
export type SearchPhase = 'reasoning' | 'parsing' | 'querying' | 'complete' | null;

export interface StreamEvent {
  type: 'phase' | 'reasoning_chunk' | 'intent' | 'results';
  data: {
    phase?: SearchPhase;
    text?: string;
    parsed_intent?: ParsedIntent;
    routing_explanation?: string[];
    query?: string;
    results?: RecipeResult[];
    source_breakdown?: Record<string, number>;
  };
}

export interface StreamingState {
  phase: SearchPhase;
  reasoning: string;
  routingExplanation: string[];
  parsedIntent: ParsedIntent | null;
  results: RecipeResult[];
  sourceBreakdown: Record<string, number>;
}

export interface ConversationMessage {
  id: string;
  role: 'assistant' | 'user';
  text: string;
}
