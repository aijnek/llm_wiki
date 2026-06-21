"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage as ChatMessageType } from "@/hooks/useWebSocket";

interface Props {
  message: ChatMessageType;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? "bg-primary text-on-primary"
            : "bg-surface-sunken text-body"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : message.pending && !message.content ? (
          <div className="flex gap-1 py-1">
            <span className="h-2 w-2 rounded-full bg-muted animate-bounce [animation-delay:0ms]" />
            <span className="h-2 w-2 rounded-full bg-muted animate-bounce [animation-delay:150ms]" />
            <span className="h-2 w-2 rounded-full bg-muted animate-bounce [animation-delay:300ms]" />
          </div>
        ) : (
          <>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
            {message.pending && (
              <span className="inline-block h-4 w-0.5 animate-pulse bg-muted ml-0.5 align-middle" />
            )}
          </>
        )}
      </div>
    </div>
  );
}
