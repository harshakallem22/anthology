export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
}

export interface Tag {
  id: string;
  name: string;
}

export interface Article {
  id: string;
  url: string;
  title: string | null;
  byline: string | null;
  lead_image_url: string | null;
  excerpt: string | null;
  word_count: number | null;
  reading_minutes: number | null;
  saved_at: string | null;
  is_archived: boolean;
  is_favorite: boolean;
  extraction_status: "pending" | "extracted" | "failed";
  created_at: string;
  tags: Tag[];
}

export interface ArticleDetail extends Article {
  content_html: string | null;
  content_text: string | null;
}

export interface Highlight {
  id: string;
  article_id: string;
  quote: string;
  note: string | null;
  position: { start?: number; end?: number } | null;
  created_at: string;
}

export interface ImportJob {
  id: string;
  source: string;
  filename: string | null;
  total_count: number;
  processed_count: number;
  status: "pending" | "processing" | "complete" | "failed";
  created_at: string;
}

export interface SearchHit {
  id: string;
  url: string;
  title: string | null;
  excerpt: string | null;
  lead_image_url: string | null;
  reading_minutes: number | null;
  snippet: string | null;
  rank: number;
  tags: string[];
}

export interface SearchResults {
  query: string;
  total: number;
  results: SearchHit[];
}
