"use client";

import { useEffect, useState } from "react";
import { listSessions, removeSession, SessionMeta } from "@/lib/sessionStore";

interface Props {
  currentSessionId: string;
  sessionVersion: number;
  onSelect: (sessionId: string) => void;
  onNew: () => void;
  onRemove: (sessionId: string) => void;
}

function relativeTime(ms: number): string {
  const diff = Date.now() - ms;
  const min = Math.floor(diff / 60_000);
  if (min < 1) return "今";
  if (min < 60) return `${min}分前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}時間前`;
  return `${Math.floor(hr / 24)}日前`;
}

export function SessionSidebar({
  currentSessionId,
  sessionVersion,
  onSelect,
  onNew,
  onRemove,
}: Props) {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);

  useEffect(() => {
    setSessions(listSessions());
  }, [sessionVersion]);

  const handleRemove = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    removeSession(sessionId);
    onRemove(sessionId);
  };

  return (
    <aside className="flex flex-col w-60 shrink-0 border-r border-border bg-surface-sunken h-full overflow-hidden">
      {/* 新しい会話ボタン */}
      <div className="px-3 py-3 border-b border-border">
        <button
          onClick={onNew}
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-body hover:bg-surface-hover transition-colors text-left flex items-center gap-2"
        >
          <span className="text-lg leading-none">＋</span>
          <span>新しい会話</span>
        </button>
      </div>

      {/* セッション一覧 */}
      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-xs text-faint px-2 py-3 text-center">
            会話履歴はありません
          </p>
        )}
        {sessions.map((s) => (
          <div
            key={s.sessionId}
            className={`group flex items-center gap-1 rounded-lg px-2 py-2 cursor-pointer transition-colors ${
              s.sessionId === currentSessionId
                ? "bg-primary-soft"
                : "hover:bg-surface-hover"
            }`}
            onClick={() => onSelect(s.sessionId)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && onSelect(s.sessionId)}
          >
            <div className="flex-1 min-w-0">
              <p
                className={`text-sm truncate ${
                  s.sessionId === currentSessionId
                    ? "text-primary font-medium"
                    : "text-body"
                }`}
              >
                {s.title || "無題の会話"}
              </p>
              <p className="text-xs text-faint mt-0.5">
                {relativeTime(s.updatedAt)}
              </p>
            </div>
            {/* 削除ボタン — hover 時のみ表示 */}
            <button
              className="opacity-0 group-hover:opacity-100 shrink-0 text-faint hover:text-danger transition-opacity text-xs px-1"
              onClick={(e) => handleRemove(e, s.sessionId)}
              title="履歴を削除"
              aria-label="履歴を削除"
            >
              ✕
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
