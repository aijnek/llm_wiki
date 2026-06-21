"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  fetchBacklinks,
  fetchPage,
  type WikiBacklink,
  type WikiPageDetail,
} from "@/lib/wikiApi";
import { preprocessWikiMarkdown } from "@/lib/wikiLinks";

export default function WikiSlugPage() {
  // Next.js 16: useParams() で slug 配列を取得（Client Component の場合はフック経由）
  const params = useParams<{ slug: string[] }>();
  const slug = (params?.slug ?? []).join("/");

  const [page, setPage] = useState<WikiPageDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backlinks, setBacklinks] = useState<WikiBacklink[]>([]);
  const [backlinkCursor, setBacklinkCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    if (!slug) return;
    setPage(null);
    setError(null);
    setBacklinks([]);
    setBacklinkCursor(null);

    fetchPage(slug)
      .then(setPage)
      .catch(() => setError(`ページが見つかりません: ${slug}`));

    fetchBacklinks(slug)
      .then((result) => {
        setBacklinks(result.items);
        setBacklinkCursor(result.cursor);
      })
      .catch(() => {/* バックリンクは取得できなくても致命的でない */});
  }, [slug]);

  const loadMoreBacklinks = async () => {
    if (!backlinkCursor) return;
    setLoadingMore(true);
    try {
      const result = await fetchBacklinks(slug, backlinkCursor);
      setBacklinks((prev) => [...prev, ...result.items]);
      setBacklinkCursor(result.cursor);
    } finally {
      setLoadingMore(false);
    }
  };

  if (error) {
    return (
      <div className="px-8 py-12">
        <p className="text-sm text-danger">{error}</p>
        <Link href="/wiki" className="mt-4 inline-block text-sm text-link hover:underline">
          ← Wiki トップへ
        </Link>
      </div>
    );
  }

  if (!page) {
    return (
      <div className="px-8 py-12">
        <p className="text-sm text-faint animate-pulse">読み込み中...</p>
      </div>
    );
  }

  const processedMd = preprocessWikiMarkdown(page.markdown, page.linkMap);
  const tags: string[] = page.frontmatter.tags ?? [];

  return (
    <article
      className="px-8 py-10 mx-auto"
      style={{ maxWidth: "var(--container-prose, 720px)" }}
    >
      {/* タイトル */}
      <h1 className="text-2xl font-semibold text-strong mb-2">
        {page.frontmatter.title ?? slug.split("/").pop()}
      </h1>

      {/* タグチップ */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-6">
          {tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-primary-soft text-primary px-2.5 py-0.5 text-xs font-medium"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* 本文 */}
      <div className="prose max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children, ...props }) => {
              if (href?.startsWith("/wiki/")) {
                return (
                  <Link href={href} {...props}>
                    {children}
                  </Link>
                );
              }
              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  {...props}
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {processedMd}
        </ReactMarkdown>
      </div>

      {/* バックリンク */}
      {(backlinks.length > 0 || backlinkCursor) && (
        <section className="mt-12 pt-6 border-t border-border">
          <h2 className="text-xs font-semibold text-muted uppercase tracking-widest mb-3">
            参照元{backlinkCursor ? "（一部）" : ""}
          </h2>
          <ul className="space-y-1">
            {backlinks.map((bl) => (
              <li key={bl.sourceSlug}>
                <Link
                  href={`/wiki/${bl.sourceSlug}`}
                  className="text-sm text-link hover:underline"
                >
                  {bl.sourceTitle || bl.sourceSlug}
                </Link>
              </li>
            ))}
          </ul>
          {backlinkCursor && (
            <button
              onClick={loadMoreBacklinks}
              disabled={loadingMore}
              className="mt-3 text-xs text-link hover:underline disabled:opacity-40"
            >
              {loadingMore ? "読み込み中..." : "さらに読み込む"}
            </button>
          )}
        </section>
      )}
    </article>
  );
}
