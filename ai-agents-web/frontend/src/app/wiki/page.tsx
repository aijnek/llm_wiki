"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { fetchPage, type WikiPageDetail } from "@/lib/wikiApi";
import { preprocessWikiMarkdown } from "@/lib/wikiLinks";
import Link from "next/link";

export default function WikiLandingPage() {
  const [page, setPage] = useState<WikiPageDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // overview → index の順にフォールバック
    fetchPage("overview")
      .catch(() => fetchPage("index"))
      .then(setPage)
      .catch(() => setError("Wiki のトップページが見つかりません。"));
  }, []);

  if (error) {
    return (
      <div className="px-8 py-12">
        <p className="text-sm text-danger">{error}</p>
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
      <h1 className="text-2xl font-semibold text-strong mb-2">
        {page.frontmatter.title ?? "Wiki"}
      </h1>

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
                <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                  {children}
                </a>
              );
            },
          }}
        >
          {processedMd}
        </ReactMarkdown>
      </div>
    </article>
  );
}
