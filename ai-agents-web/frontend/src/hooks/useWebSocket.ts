"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  listSessions,
  removeSession,
  upsertSession,
} from "@/lib/sessionStore";

export type WsStatus = "disconnected" | "connecting" | "connected" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  pending?: boolean;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "";
const HTTP_API_URL = process.env.NEXT_PUBLIC_INGEST_API_URL ?? "";

/** DynamoDB から返った {role, content} を ChatMessage に変換する */
function toChat(msg: { role: string; content: string }): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: msg.role as "user" | "assistant",
    content: msg.content,
  };
}

/** localStorage の最新セッション ID があればそれを使い、なければ新規発番する */
function initialSessionId(): string {
  const sessions = listSessions();
  return sessions.length > 0 ? sessions[0].sessionId : crypto.randomUUID();
}

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WsStatus>("disconnected");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const pendingIdRef = useRef<string | null>(null);
  const [reconnectSignal, setReconnectSignal] = useState(0);
  // マルチターン会話のセッション ID — 「新しい会話」で再発番する
  const sessionIdRef = useRef<string>(initialSessionId());

  // サイドバーのアクティブ表示用に sessionId を state として公開する
  const [currentSessionId, setCurrentSessionId] = useState<string>(
    sessionIdRef.current
  );

  // セッションメタの変更をサイドバーに反映するためのカウンター
  const [sessionVersion, setSessionVersion] = useState(0);
  const bumpVersion = useCallback(() => setSessionVersion((n) => n + 1), []);

  const connect = useCallback(() => {
    if (ws.current && ws.current.readyState < WebSocket.CLOSING) return;

    setStatus("connecting");
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => setStatus("connected");

    socket.onclose = () => {
      setStatus("disconnected");
      ws.current = null;
      // 2秒後に自動再接続（ingest 待機中に切断しても再トリガーできるよう）
      setTimeout(() => setReconnectSignal((n) => n + 1), 2000);
    };

    socket.onerror = () => setStatus("error");

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as {
          type: "message" | "done" | "error";
          content?: string;
          message?: string;
        };

        const pendingId = pendingIdRef.current;

        if (data.type === "message" && data.content !== undefined) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingId
                ? { ...m, content: m.content + data.content!, pending: true }
                : m
            )
          );
        } else if (data.type === "done") {
          pendingIdRef.current = null;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingId ? { ...m, pending: false } : m
            )
          );
        } else if (data.type === "error") {
          pendingIdRef.current = null;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingId
                ? { ...m, content: `エラー: ${data.message ?? "不明"}`, pending: false }
                : m
            )
          );
        }
      } catch {
        // ignore malformed frames
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    ws.current?.close();
  }, []);

  const sendPrompt = useCallback(
    (prompt: string) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return false;

      const sid = sessionIdRef.current;
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: prompt,
      };
      const assistantId = crypto.randomUUID();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        pending: true,
      };

      pendingIdRef.current = assistantId;
      setMessages((prev) => {
        // 最初のユーザー発話のときだけタイトルを確定してレジストリに登録する
        const isFirst = prev.filter((m) => m.role === "user").length === 0;
        const title = isFirst
          ? prompt.slice(0, 30) + (prompt.length > 30 ? "…" : "")
          : listSessions().find((s) => s.sessionId === sid)?.title ?? prompt.slice(0, 30);
        upsertSession({ sessionId: sid, title, updatedAt: Date.now() });
        return [...prev, userMsg, assistantMsg];
      });
      ws.current.send(JSON.stringify({ prompt, sessionId: sid }));
      // サイドバーを更新（upsertSession 後）
      bumpVersion();
      return true;
    },
    [bumpVersion]
  );

  // auto-connect on mount
  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  // reconnect when reconnectSignal increments
  useEffect(() => {
    if (reconnectSignal === 0) return;
    connect();
  }, [reconnectSignal, connect]);

  /** 新しい会話を開始する — localStorage には保存しない（未送信のため） */
  const clearMessages = useCallback(() => {
    setMessages([]);
    const newId = crypto.randomUUID();
    sessionIdRef.current = newId;
    setCurrentSessionId(newId);
    bumpVersion();
  }, [bumpVersion]);

  /**
   * 過去セッションを選択して messages を復元する。
   * DynamoDB から取得できなかった（TTL 切れ）場合は localStorage から除去してエラー通知を返す。
   */
  const loadSession = useCallback(
    async (sessionId: string): Promise<"ok" | "expired"> => {
      if (!HTTP_API_URL) return "expired";
      try {
        const res = await fetch(`${HTTP_API_URL}/sessions/${sessionId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { messages: { role: string; content: string }[] };
        if (data.messages.length === 0) {
          // TTL 切れ: レジストリから除去
          removeSession(sessionId);
          bumpVersion();
          return "expired";
        }
        sessionIdRef.current = sessionId;
        setCurrentSessionId(sessionId);
        setMessages(data.messages.map(toChat));
        return "ok";
      } catch {
        return "expired";
      }
    },
    [bumpVersion]
  );

  // ページリロード時: localStorage に最新セッションがあれば messages を自動復元する
  const loadSessionRef = useRef(loadSession);
  loadSessionRef.current = loadSession;
  useEffect(() => {
    const sessions = listSessions();
    if (sessions.length > 0) {
      loadSessionRef.current(sessions[0].sessionId);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    status,
    messages,
    sendPrompt,
    connect,
    disconnect,
    clearMessages,
    loadSession,
    currentSessionId,
    sessionVersion,
  };
}
