/**
 * sessionStore.ts — ブラウザの localStorage に会話セッションのメタ情報を保持するユーティリティ。
 *
 * 設計方針:
 * - 認証なしのため「このブラウザが使った sessionId 一覧」をローカルのみで管理する。
 * - サーバー側（DynamoDB）には sessionId ごとの messages が 7 日 TTL で保存されている。
 *   期限切れのエントリを踏んだ場合は呼び出し元が除去する。
 * - SSR 安全: window が存在しない環境ではすべての操作をノーオペレーションにする。
 */

const STORAGE_KEY = "aiw.sessions";

export interface SessionMeta {
  sessionId: string;
  /** 会話の最初のユーザー発話を先頭 30 文字で切り詰めたタイトル */
  title: string;
  /** 最終更新の UNIX ミリ秒 */
  updatedAt: number;
}

function isClient(): boolean {
  return typeof window !== "undefined";
}

function readAll(): SessionMeta[] {
  if (!isClient()) return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as SessionMeta[];
  } catch {
    return [];
  }
}

function writeAll(sessions: SessionMeta[]): void {
  if (!isClient()) return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    // ストレージが満杯などの場合は握りつぶす
  }
}

/** 保存済みセッション一覧を updatedAt 降順で返す */
export function listSessions(): SessionMeta[] {
  return readAll().sort((a, b) => b.updatedAt - a.updatedAt);
}

/** sessionId が既存なら updatedAt / title を更新、なければ先頭に追加する */
export function upsertSession(meta: SessionMeta): void {
  const all = readAll();
  const idx = all.findIndex((s) => s.sessionId === meta.sessionId);
  if (idx >= 0) {
    all[idx] = { ...all[idx], ...meta };
  } else {
    all.unshift(meta);
  }
  writeAll(all);
}

/** localStorage からエントリを削除する（DynamoDB 側は変更しない）*/
export function removeSession(sessionId: string): void {
  const all = readAll().filter((s) => s.sessionId !== sessionId);
  writeAll(all);
}
