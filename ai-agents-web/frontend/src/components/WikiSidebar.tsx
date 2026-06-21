"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  fetchFacets,
  fetchPages,
  type WikiFacets,
  type WikiPagePointer,
} from "@/lib/wikiApi";

// フォルダ展開ノードの状態
interface FolderNode {
  pages: WikiPagePointer[];
  cursor: string | null;
  loading: boolean;
  open: boolean;
}

const FOLDER_LABELS: Record<string, string> = {
  concepts: "コンセプト",
  entities: "エンティティ",
  sources: "ソース",
  root: "その他",
};

export function WikiSidebar() {
  const params = useParams<{ slug?: string[] }>();
  const currentSlug = params?.slug?.join("/") ?? "";

  const [facets, setFacets] = useState<WikiFacets | null>(null);
  const [facetsError, setFacetsError] = useState(false);
  const [folderNodes, setFolderNodes] = useState<Record<string, FolderNode>>({});
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [tagPages, setTagPages] = useState<WikiPagePointer[]>([]);
  const [tagCursor, setTagCursor] = useState<string | null>(null);
  const [tagLoading, setTagLoading] = useState(false);

  useEffect(() => {
    fetchFacets()
      .then(setFacets)
      .catch(() => setFacetsError(true));
  }, []);

  const toggleFolder = async (folder: string) => {
    const node = folderNodes[folder];
    if (node) {
      // 既にロード済み → 開閉切り替えのみ
      setFolderNodes((prev) => ({
        ...prev,
        [folder]: { ...prev[folder], open: !prev[folder].open },
      }));
      return;
    }
    // 初回展開 → ページを遅延ロード
    setFolderNodes((prev) => ({
      ...prev,
      [folder]: { pages: [], cursor: null, loading: true, open: true },
    }));
    try {
      const result = await fetchPages({ folder, limit: 50 });
      setFolderNodes((prev) => ({
        ...prev,
        [folder]: {
          pages: result.items,
          cursor: result.cursor,
          loading: false,
          open: true,
        },
      }));
    } catch {
      setFolderNodes((prev) => ({
        ...prev,
        [folder]: { pages: [], cursor: null, loading: false, open: true },
      }));
    }
  };

  const loadMoreFolder = async (folder: string) => {
    const node = folderNodes[folder];
    if (!node?.cursor) return;
    setFolderNodes((prev) => ({
      ...prev,
      [folder]: { ...prev[folder], loading: true },
    }));
    try {
      const result = await fetchPages({ folder, cursor: node.cursor!, limit: 50 });
      setFolderNodes((prev) => ({
        ...prev,
        [folder]: {
          ...prev[folder],
          pages: [...prev[folder].pages, ...result.items],
          cursor: result.cursor,
          loading: false,
        },
      }));
    } catch {
      setFolderNodes((prev) => ({
        ...prev,
        [folder]: { ...prev[folder], loading: false },
      }));
    }
  };

  const selectTag = async (tag: string) => {
    if (activeTag === tag) {
      setActiveTag(null);
      setTagPages([]);
      setTagCursor(null);
      return;
    }
    setActiveTag(tag);
    setTagLoading(true);
    try {
      const result = await fetchPages({ tag, limit: 100 });
      setTagPages(result.items);
      setTagCursor(result.cursor);
    } catch {
      setTagPages([]);
    } finally {
      setTagLoading(false);
    }
  };

  const loadMoreTagPages = async () => {
    if (!activeTag || !tagCursor) return;
    const result = await fetchPages({ tag: activeTag, cursor: tagCursor, limit: 100 });
    setTagPages((prev) => [...prev, ...result.items]);
    setTagCursor(result.cursor);
  };

  return (
    <aside className="flex flex-col w-64 shrink-0 border-r border-border bg-surface-sunken h-full overflow-hidden">
      {/* Wiki タイトルリンク */}
      <div className="px-4 py-3 border-b border-border shrink-0">
        <Link
          href="/wiki"
          className="text-sm font-semibold text-strong hover:text-primary transition-colors"
        >
          AI Agents Wiki
        </Link>
      </div>

      {/* タグフィルタ — max-h + overflow-y-auto でフォルダツリーを圧迫しない */}
      {facets && facets.tags.length > 0 && (
        <div className="px-3 py-2 border-b border-border flex flex-wrap gap-1 max-h-28 overflow-y-auto shrink-0">
          {facets.tags.map(({ tag, count }) => (
            <button
              key={tag}
              onClick={() => selectTag(tag)}
              className={`rounded-full px-2 py-0.5 text-xs transition-colors ${
                activeTag === tag
                  ? "bg-primary text-on-primary"
                  : "bg-surface border border-border text-muted hover:border-primary hover:text-primary"
              }`}
            >
              {tag}
              <span className="ml-1 opacity-50">{count}</span>
            </button>
          ))}
        </div>
      )}

      {/* ツリー / タグ絞り込み結果 */}
      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
        {facetsError && (
          <p className="text-xs text-danger px-2 py-3 text-center">
            インデックス取得エラー
          </p>
        )}

        {activeTag ? (
          /* タグ絞り込みビュー */
          <div>
            {tagLoading && (
              <p className="text-xs text-faint px-2 py-1 animate-pulse">読み込み中...</p>
            )}
            {tagPages.map((p) => (
              <PageItem key={p.slug} page={p} currentSlug={currentSlug} />
            ))}
            {tagCursor && (
              <button
                className="w-full text-left text-xs text-link px-2 py-1 hover:underline"
                onClick={loadMoreTagPages}
              >
                さらに読み込む
              </button>
            )}
          </div>
        ) : (
          /* フォルダツリー */
          facets?.folders.map((folder) => {
            const node = folderNodes[folder];
            const label = FOLDER_LABELS[folder] ?? folder;
            return (
              <div key={folder}>
                <button
                  onClick={() => toggleFolder(folder)}
                  className="w-full flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-semibold text-muted uppercase tracking-wide hover:bg-surface-hover transition-colors text-left"
                >
                  <span className="shrink-0 text-faint">
                    {node?.open ? "▾" : "▸"}
                  </span>
                  {label}
                </button>
                {node?.open && (
                  <div className="ml-2 space-y-0.5 mb-1">
                    {node.pages.map((p) => (
                      <PageItem key={p.slug} page={p} currentSlug={currentSlug} />
                    ))}
                    {node.loading && (
                      <p className="text-xs text-faint px-2 py-1 animate-pulse">
                        読み込み中...
                      </p>
                    )}
                    {!node.loading && node.cursor && (
                      <button
                        className="w-full text-left text-xs text-link px-2 py-1 hover:underline"
                        onClick={() => loadMoreFolder(folder)}
                      >
                        さらに読み込む
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </nav>
    </aside>
  );
}

function PageItem({
  page,
  currentSlug,
}: {
  page: WikiPagePointer;
  currentSlug: string;
}) {
  const isActive = page.slug === currentSlug;
  return (
    <Link
      href={`/wiki/${page.slug}`}
      className={`flex items-center rounded-lg px-2 py-1.5 text-sm transition-colors ${
        isActive
          ? "bg-primary-soft text-primary font-medium"
          : "text-body hover:bg-surface-hover"
      }`}
    >
      <span className="truncate">{page.title}</span>
    </Link>
  );
}
