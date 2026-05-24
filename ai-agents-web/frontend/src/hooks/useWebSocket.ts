"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type WsStatus = "disconnected" | "connecting" | "connected" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  pending?: boolean;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "";

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WsStatus>("disconnected");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const pendingIdRef = useRef<string | null>(null);

  const connect = useCallback(() => {
    if (ws.current && ws.current.readyState < WebSocket.CLOSING) return;

    setStatus("connecting");
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => setStatus("connected");

    socket.onclose = () => {
      setStatus("disconnected");
      ws.current = null;
    };

    socket.onerror = () => setStatus("error");

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as {
          type: "message" | "done" | "error";
          content?: string;
          message?: string;
        };

        // capture before any async state update so React's deferred callback reads the right value
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
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      ws.current.send(JSON.stringify({ prompt }));
      return true;
    },
    []
  );

  // auto-connect on mount
  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { status, messages, sendPrompt, connect, disconnect, clearMessages };
}
