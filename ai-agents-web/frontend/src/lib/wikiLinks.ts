/**
 * Obsidian スタイルの [[target]] / [[target|label]] を
 * 通常の markdown リンクへ変換する前処理。
 *
 * - リンクマップに slug が存在する → [label](/wiki/slug) に置換
 * - 解決不能（空文字列または map にない）→ プレーンテキスト label にフォールバック
 * - 末尾の "— 説明" テキストはリンク化の範囲外なのでそのまま保持される
 */
export function preprocessWikiMarkdown(
  markdown: string,
  linkMap: Record<string, string>
): string {
  return markdown.replace(
    /\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]/g,
    (_match: string, rawTarget: string, rawLabel?: string) => {
      const target = rawTarget.trim();
      // label: 明示されていればそれを、なければ slug の末尾セグメント
      const label =
        rawLabel?.trim() ??
        target
          .split("/")
          .pop()
          ?.replace(/-/g, " ") ??
        target;
      const slug = linkMap[target];
      if (!slug) {
        // 解決不能 → プレーンテキスト
        return label;
      }
      return `[${label}](/wiki/${slug})`;
    }
  );
}
