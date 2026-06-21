"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useWebSocket } from "@/hooks/useWebSocket";

type UploadStatus = "idle" | "presigning" | "uploading" | "uploaded" | "error";

const INGEST_API_URL = process.env.NEXT_PUBLIC_INGEST_API_URL ?? "";
const ACCEPTED = ".md,.txt,.pdf";

export default function IngestPage() {
  const { status: wsStatus, messages, sendPrompt, clearMessages } = useWebSocket();
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const ingestTriggeredRef = useRef(false);

  useEffect(() => {
    if (
      uploadStatus === "uploaded" &&
      file &&
      wsStatus === "connected" &&
      !ingestTriggeredRef.current
    ) {
      if (sendPrompt(`/ingest ${file.name}`)) {
        ingestTriggeredRef.current = true;
      }
    }
  }, [uploadStatus, file, wsStatus, sendPrompt]);

  const assistantMessages = messages.filter((m) => m.role === "assistant");
  const ingestMsg = assistantMessages[assistantMessages.length - 1] ?? null;
  const isIngesting = ingestMsg?.pending === true;
  const isIngested = ingestMsg !== null && !ingestMsg.pending;

  const reset = () => {
    setFile(null);
    setUploadStatus("idle");
    setProgress(0);
    setErrorMsg("");
    ingestTriggeredRef.current = false;
    clearMessages();
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploadStatus("presigning");
    setProgress(0);
    setErrorMsg("");
    ingestTriggeredRef.current = false;
    clearMessages();

    try {
      const res = await fetch(`${INGEST_API_URL}/presign-upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type || "application/octet-stream",
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { error?: string }).error ?? `HTTP ${res.status}`);
      }
      const { url } = (await res.json()) as { url: string };

      setUploadStatus("uploading");

      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("PUT", url);
        xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100));
        };
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) resolve();
          else reject(new Error(`S3 upload failed: ${xhr.status}`));
        };
        xhr.onerror = () => reject(new Error("ネットワークエラー"));
        xhr.send(file);
      });

      setUploadStatus("uploaded");
      setProgress(100);
    } catch (e) {
      setUploadStatus("error");
      setErrorMsg(e instanceof Error ? e.message : String(e));
    }
  };

  const isProcessing =
    uploadStatus === "presigning" || uploadStatus === "uploading" || isIngesting;

  return (
    <div className="flex h-screen flex-col bg-canvas">
      <header className="flex items-center gap-3 border-b border-border px-5 py-3 bg-surface">
        <h1 className="text-lg font-semibold text-strong">Ingest</h1>
        <span className="ml-auto text-xs text-faint font-mono">WS: {wsStatus}</span>
        <Link
          href="/"
          className="text-sm text-link hover:underline"
        >
          ← チャットに戻る
        </Link>
      </header>

      <main className="flex flex-1 flex-col items-center px-4 gap-6 overflow-y-auto py-10">
        {/* ファイル選択エリア */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !isProcessing && inputRef.current?.click()}
          className={`flex w-full max-w-lg cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-8 py-16 text-center transition-colors ${
            isProcessing
              ? "border-border cursor-not-allowed opacity-60"
              : "border-border hover:border-primary hover:bg-surface-sunken"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <>
              <span className="text-2xl">📄</span>
              <p className="text-sm font-medium text-strong">{file.name}</p>
              <p className="text-xs text-faint">{(file.size / 1024).toFixed(1)} KB</p>
            </>
          ) : (
            <>
              <span className="text-2xl text-faint">⬆</span>
              <p className="text-sm text-muted">
                ファイルをドロップ、またはクリックして選択
              </p>
              <p className="text-xs text-faint">.md / .txt / .pdf</p>
            </>
          )}
        </div>

        {/* アップロード進捗 */}
        {(uploadStatus === "uploading" || uploadStatus === "uploaded") && (
          <div className="w-full max-w-lg">
            <div className="flex justify-between text-xs text-muted mb-1">
              <span>S3 アップロード</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-surface-sunken">
              <div
                className="h-2 rounded-full bg-primary transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Ingest ステータス & エージェント応答 */}
        {uploadStatus === "uploaded" && (
          <div className="w-full max-w-lg rounded-xl border border-border p-4 bg-surface">
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-body">
              {isIngested ? (
                <span className="text-success">✓</span>
              ) : ingestTriggeredRef.current ? (
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-warning" />
              ) : (
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-faint" />
              )}
              <span>
                {isIngested
                  ? "Ingest 完了"
                  : ingestTriggeredRef.current
                  ? "Ingest 処理中..."
                  : `WS 接続待機中 (${wsStatus})...`}
              </span>
            </div>
            {ingestMsg?.content && (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {ingestMsg.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        )}

        {uploadStatus === "error" && (
          <p className="text-sm text-danger">{errorMsg}</p>
        )}

        {/* ボタン */}
        <div className="flex gap-3">
          <button
            onClick={handleUpload}
            disabled={!file || isProcessing}
            className="rounded-xl bg-primary px-6 py-2.5 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {uploadStatus === "presigning"
              ? "準備中..."
              : uploadStatus === "uploading"
              ? "アップロード中..."
              : isIngesting
              ? "Ingest 中..."
              : "アップロード"}
          </button>
          {(file || uploadStatus !== "idle") && !isProcessing && (
            <button
              onClick={reset}
              className="rounded-xl border border-border px-6 py-2.5 text-sm text-body hover:bg-surface-hover transition-colors"
            >
              リセット
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
