"use client";

// Human refinement drawer: score (1~10) + defect tags → POST /api/score (writes report_batchXX.md).
import { useState } from "react";

const TAG_OPTIONS = ["口型错位", "抖动", "变脸", "手崩", "模糊", "肢体异常"];

export default function RefineDrawer({
  batch,
  refImg,
  seed,
  initialScore,
  initialTags,
}: {
  batch: string;
  refImg: string;
  seed: number;
  initialScore: number | null;
  initialTags: string;
}) {
  const [open, setOpen] = useState(false);
  const [score, setScore] = useState<number>(initialScore ?? 5);
  const [tags, setTags] = useState<string[]>(initialTags ? initialTags.split(",").map((t) => t.trim()).filter(Boolean) : []);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleTag = (t: string) =>
    setTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ batch, ref: refImg, seed, score, tags: tags.join(",") }),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? `HTTP ${res.status}`);
      setSaved(true);
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pt-1">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs px-3 py-1 rounded border border-(--border) hover:border-(--accent) text-(--muted) hover:text-(--foreground)"
      >
        {open ? "收起精评" : "✎ 人工精评"}
      </button>
      {saved ? <span className="text-xs text-emerald-400 ml-2">已写回 report</span> : null}

      {open ? (
        <div className="mt-3 p-3 rounded border border-(--border) bg-(--background) space-y-3">
          <div>
            <div className="text-xs text-(--muted) mb-1">评分：{score}/10</div>
            <input
              type="range" min={1} max={10} step={1} value={score}
              onChange={(e) => setScore(Number(e.target.value))}
              className="w-full accent-[#00d4aa]"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {TAG_OPTIONS.map((t) => (
              <button
                key={t}
                onClick={() => toggleTag(t)}
                className={`text-xs px-2 py-0.5 rounded border ${
                  tags.includes(t) ? "border-(--accent) text-(--accent)" : "border-(--border) text-(--muted)"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          {error ? <div className="text-xs text-red-400">{error}</div> : null}
          <button
            onClick={save}
            disabled={saving}
            className="w-full py-1.5 rounded text-sm font-semibold bg-(--accent) text-black disabled:opacity-50"
          >
            {saving ? "写回中…" : "保存并写回 report"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
