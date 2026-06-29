// Thin typed client over the REST API.

export const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000/api";

export interface Paginated<T> {
  count: number;
  results: T[];
}

export interface Supplier {
  id: number;
  name: string;
  inn: string;
  currency: string;
}

export interface CatalogProduct {
  id: number;
  article: string;
  name: string;
  unit: string;
  group: number | null;
  group_name: string | null;
}

export interface ProductGroup {
  id: number;
  name: string;
}

export interface Project {
  id: number;
  name: string;
  estimates_count: number;
}

export interface ImportJob {
  id: number;
  source_filename: string;
  status: string;
  progress: number;
  total_rows: number;
  processed_rows: number;
  error: string;
  row_errors: { row: number; message: string }[];
  uploaded_at: string;
  mapping: Record<string, number>;
}

export interface Estimate extends ImportJob {
  project: number;
  match_progress: number;
  items_count: number;
}

export interface EstimateItem {
  id: number;
  row_number: number;
  name: string;
  article: string;
  unit: string;
  quantity: string | null;
  material_price: string | null;
  installation_price: string | null;
  catalog_product: number | null;
  catalog_article: string | null;
  catalog_name: string | null;
  match_status: string;
  match_source: string;
  confidence: number | null;
  is_confident: boolean;
}

export interface PriceList extends ImportJob {
  supplier: number;
  match_progress: number;
  items_count: number;
}

export interface PriceListItem {
  id: number;
  row_number: number;
  article: string;
  name: string;
  unit: string;
  price: string | null;
  catalog_product: number | null;
  catalog_article: string | null;
  catalog_name: string | null;
}

export interface Preview {
  sheets: string[];
  sheet: string;
  header_row: number;
  columns: string[];
  rows: string[][];
}

export interface CandidateOption {
  id: number;
  article: string;
  name: string;
  score: number;
}

export interface ProductDraft {
  article: string;
  name: string;
  unit: string;
  suggested_group: number | null;
  groups: ProductGroup[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isForm = init?.body instanceof FormData;
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: isForm ? init?.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const apiGet = <T>(path: string) => request<T>(path);
export const apiPost = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });
export const apiPatch = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
export const apiDelete = (path: string) => request<void>(path, { method: "DELETE" });
export const apiUpload = <T>(path: string, form: FormData) =>
  request<T>(path, { method: "POST", body: form });
