const WIKI_API = process.env.NEXT_PUBLIC_INGEST_API_URL ?? "";

// ------------------------------------------------------------------ //
// 型定義
// ------------------------------------------------------------------ //

export interface WikiFacets {
  folders: string[];
  tags: { tag: string; count: number }[];
}

export interface WikiPagePointer {
  slug: string;
  title: string;
  type: string;
  folder: string;
}

export interface WikiPageDetail {
  slug: string;
  frontmatter: {
    title?: string;
    type?: string;
    entityType?: string;
    tags?: string[];
  };
  /** frontmatter を除いた本文 markdown */
  markdown: string;
  /** wikilink の raw ターゲット → 解決済み slug（解決不能は空文字列） */
  linkMap: Record<string, string>;
}

export interface WikiBacklink {
  sourceSlug: string;
  sourceTitle: string;
}

export interface PaginatedResult<T> {
  items: T[];
  cursor: string | null;
}

// ------------------------------------------------------------------ //
// API クライアント
// ------------------------------------------------------------------ //

export async function fetchFacets(): Promise<WikiFacets> {
  const res = await fetch(`${WIKI_API}/wiki/facets`);
  if (!res.ok) throw new Error(`fetchFacets: ${res.status}`);
  return res.json() as Promise<WikiFacets>;
}

export async function fetchPages(opts: {
  folder?: string;
  tag?: string;
  cursor?: string;
  limit?: number;
}): Promise<PaginatedResult<WikiPagePointer>> {
  const qs = new URLSearchParams();
  if (opts.folder) qs.set("folder", opts.folder);
  if (opts.tag) qs.set("tag", opts.tag);
  if (opts.cursor) qs.set("cursor", opts.cursor);
  if (opts.limit) qs.set("limit", String(opts.limit));
  const res = await fetch(`${WIKI_API}/wiki/pages?${qs.toString()}`);
  if (!res.ok) throw new Error(`fetchPages: ${res.status}`);
  const data = (await res.json()) as { pages: WikiPagePointer[]; cursor: string | null };
  return { items: data.pages, cursor: data.cursor ?? null };
}

export async function fetchPage(slug: string): Promise<WikiPageDetail> {
  const res = await fetch(`${WIKI_API}/wiki/page/${slug}`);
  if (!res.ok) throw new Error(`fetchPage ${slug}: ${res.status}`);
  return res.json() as Promise<WikiPageDetail>;
}

export async function fetchBacklinks(
  slug: string,
  cursor?: string
): Promise<PaginatedResult<WikiBacklink>> {
  const qs = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  const res = await fetch(`${WIKI_API}/wiki/backlinks/${slug}${qs}`);
  if (!res.ok) throw new Error(`fetchBacklinks ${slug}: ${res.status}`);
  const data = (await res.json()) as {
    backlinks: WikiBacklink[];
    cursor: string | null;
  };
  return { items: data.backlinks, cursor: data.cursor ?? null };
}
