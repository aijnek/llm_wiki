"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";

type UploadStatus = "idle" | "presigning" | "uploading" | "done" | "error";

const INGEST_API_URL = process.env.NEXT_PUBLIC_INGEST_API_URL ?? "";

const ACCEPTED = ".md,.txt,.pdf";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const xhrRef = useRef<XMLHttpRequest | null>(null);

  const reset = () => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
    setErrorMsg("");
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setStatus("presigning");
    setProgress(0);
    setErrorMsg("");

    try {
      const res = await fetch(`${INGEST_API_URL}/presign-upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, content_type: file.type || "application/octet-stream" }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { error?: string }).error ?? `HTTP ${res.status}`);
      }
      const { url } = await res.json() as { url: string };

      setStatus("uploading");

      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhrRef.current = xhr;
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

      setStatus("done");
      setProgress(100);
    } catch (e) {
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="flex h-screen flex-col bg-white dark:bg-gray-900">
      <header className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-700 px-5 py-3">
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Ingest</h1>
        <Link
          href="/"
          className="ml-auto text-sm text-blue-500 hover:text-blue-700 underline"
        >
          ← チャットに戻る
        </Link>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4 gap-6">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="flex w-full max-w-lg cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-600 px-8 py-16 text-center transition hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800"
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
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{file.name}</p>
              <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
            </>
          ) : (
            <>
              <span className="text-2xl text-gray-300">⬆</span>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                ファイルをドロップ、またはクリックして選択
              </p>
              <p className="text-xs text-gray-400">.md / .txt / .pdf</p>
            </>
          )}
        </div>

        {status === "uploading" && (
          <div className="w-full max-w-lg">
            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-2 rounded-full bg-blue-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-1 text-right text-xs text-gray-400">{progress}%</p>
          </div>
        )}

        {status === "done" && (
          <p className="text-sm font-medium text-green-600">アップロード完了 ✓</p>
        )}
        {status === "error" && (
          <p className="text-sm text-red-500">{errorMsg}</p>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleUpload}
            disabled={!file || status === "presigning" || status === "uploading"}
            className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {status === "presigning" ? "準備中..." : status === "uploading" ? "アップロード中..." : "アップロード"}
          </button>
          {(file || status !== "idle") && (
            <button
              onClick={reset}
              className="rounded-xl border border-gray-300 dark:border-gray-600 px-6 py-2.5 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              リセット
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
