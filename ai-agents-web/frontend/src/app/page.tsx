"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ChatMessage } from "@/components/ChatMessage";
import { SessionSidebar } from "@/components/SessionSidebar";
import { useWebSocket } from "@/hooks/useWebSocket";

const STATUS_LABEL: Record<string, string> = {
  disconnected: "切断",
  connecting: "接続中...",
  connected: "接続済み",
  error: "エラー",
};

const STATUS_COLOR: Record<string, string> = {
  disconnected: "bg-gray-400",
  connecting: "bg-yellow-400 animate-pulse",
  connected: "bg-green-500",
  error: "bg-red-500",
};

export default function ChatPage() {
  const {
    status,
    messages,
    sendPrompt,
    connect,
    clearMessages,
    loadSession,
    currentSessionId,
    sessionVersion,
  } = useWebSocket();
  const [input, setInput] = useState("");
  const [expiredNotice, setExpiredNotice] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isPending = messages.some((m) => m.pending);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const prompt = input.trim();
    if (!prompt || isPending || status !== "connected") return;
    const ok = sendPrompt(prompt);
    if (ok) {
      setInput("");
      setExpiredNotice(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    // messages が空の場合は同じ sessionId でも再ロードする（ページリロード後の復元）
    if (sessionId === currentSessionId && messages.length > 0) return;
    const result = await loadSession(sessionId);
    if (result === "expired") {
      setExpiredNotice(true);
    } else {
      setExpiredNotice(false);
    }
  };

  const handleNew = () => {
    clearMessages();
    setExpiredNotice(false);
  };

  const handleRemove = (sessionId: string) => {
    // 削除されたのが現在のセッションなら新しい会話へ
    if (sessionId === currentSessionId) {
      clearMessages();
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900">
      {/* 左サイドバー */}
      <SessionSidebar
        currentSessionId={currentSessionId}
        sessionVersion={sessionVersion}
        onSelect={handleSelectSession}
        onNew={handleNew}
        onRemove={handleRemove}
      />

      {/* メインチャット列 */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-700 px-5 py-3">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            AI Agents Wiki
          </h1>
          <Link
            href="/ingest"
            className="ml-4 text-sm text-blue-500 hover:text-blue-700 underline"
          >
            Ingest
          </Link>
          <div className="flex items-center gap-1.5 ml-auto text-xs text-gray-500 dark:text-gray-400">
            <span className={`h-2 w-2 rounded-full ${STATUS_COLOR[status]}`} />
            {STATUS_LABEL[status]}
            {status !== "connected" && (
              <button
                onClick={connect}
                className="ml-2 text-blue-500 underline hover:text-blue-700"
              >
                再接続
              </button>
            )}
          </div>
        </header>

        {/* Messages */}
        <main className="flex-1 overflow-y-auto px-4 py-4">
          {expiredNotice && (
            <p className="text-center text-sm text-red-400 mb-4">
              この会話の履歴は期限切れです（7日が経過しました）。
            </p>
          )}
          {messages.length === 0 && !expiredNotice && (
            <p className="text-center text-sm text-gray-400 mt-20">
              AI Agents Wiki に質問してください
            </p>
          )}
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} />
        </main>

        {/* Input */}
        <footer className="border-t border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <textarea
              className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="質問を入力 (Shift+Enter で改行)"
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isPending || status !== "connected"}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isPending || status !== "connected"}
              className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              送信
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
