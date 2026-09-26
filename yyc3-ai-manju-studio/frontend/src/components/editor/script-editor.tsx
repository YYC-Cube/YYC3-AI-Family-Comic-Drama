"use client";

/**
 * 剧本编辑器：左栏小说原文输入，右栏结构化解析结果
 * 生成剧本 / 提取分镜均走真实 API，失败自动降级演示数据
 */
import { withFallback } from "@/api/client";
import { extractStoryboard, generateScript, type ScriptResult } from "@/api/script";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { mockStoryboard } from "@/lib/mock-data";
import type { StoryboardV1 } from "@/types/storyboard";
import { Film, Loader2, Sparkles } from "lucide-react";
import { useState, type ReactNode } from "react";

/** 演示用结构化结果 */
const MOCK_SCRIPT_RESULT: ScriptResult = {
  characters: ["林彻（主角）", "沈万川（反派）", "苏念（回忆）", "黑衣跟班"],
  scenes: [
    "场景一：雨夜天台（夜/外）",
    "场景二：工厂火场（回忆/内）",
    "场景三：天台对峙（夜/外）",
  ],
  hooks: [
    "开场 3 秒：雨夜天台孤立背影",
    "特写：主角冷峻侧脸 + 复仇台词",
    "钩子：反派丢文件羞辱，主角爆发前静默",
  ],
  episode_suggestions: [
    { title: "第 1 集：雨夜归人", synopsis: "主角十年后现身天台，与反派当面对峙，回忆火场旧事。" },
    { title: "第 2 集：火场真相", synopsis: "揭开大火背后另有主谋，反派只是棋子。" },
    { title: "第 3 集：宅门暗流", synopsis: "老管家递出关键证据，主角切入豪门内斗。" },
  ],
};

interface ScriptEditorProps {
  projectId: string;
  className?: string;
}

export function ScriptEditor({ projectId, className }: ScriptEditorProps) {
  const [novelText, setNovelText] = useState("");
  const [result, setResult] = useState<ScriptResult | null>(null);
  const [storyboard, setStoryboard] = useState<StoryboardV1 | null>(null);
  const [loading, setLoading] = useState<"generate" | "extract" | null>(null);
  const [isMock, setIsMock] = useState(false);

  const handleGenerate = async () => {
    setLoading("generate");
    const { data, isMock: mock } = await withFallback(
      () => generateScript({ project_id: projectId, novel_text: novelText }),
      () => MOCK_SCRIPT_RESULT
    );
    setResult(data);
    setIsMock(mock);
    setLoading(null);
  };

  const handleExtract = async () => {
    setLoading("extract");
    const { data, isMock: mock } = await withFallback(
      () =>
        extractStoryboard({
          project_id: projectId,
          episode_id: "ep01",
          script_text: novelText || "（空文本，按默认模板演示提取）",
        }),
      () => mockStoryboard
    );
    setStoryboard(data);
    setIsMock(mock);
    setLoading(null);
  };

  return (
    <div className={className}>
      {/* 操作栏 */}
      <div className="mb-4 flex items-center gap-2">
        <Button onClick={handleGenerate} disabled={loading !== null}>
          {loading === "generate" ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          生成剧本
        </Button>
        <Button variant="outline" onClick={handleExtract} disabled={loading !== null}>
          {loading === "extract" ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Film className="h-4 w-4" />
          )}
          提取分镜
        </Button>
        {isMock && <Badge variant="warning">演示数据</Badge>}
        {storyboard && (
          <Badge variant="secondary">
            已提取 {storyboard.total_shots} 镜 · {storyboard.hook_shots.length} 个钩子
          </Badge>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* 左栏：原文输入 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">小说原文</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Textarea
              value={novelText}
              onChange={(e) => setNovelText(e.target.value)}
              placeholder="粘贴小说章节原文，AI 将解析角色、场景与钩子点，并给出分集建议……"
              className="min-h-[420px] resize-y font-mono text-[13px] leading-6"
            />
            <div className="text-right text-xs text-muted-foreground">
              {novelText.length} 字
            </div>
          </CardContent>
        </Card>

        {/* 右栏：结构化结果 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">结构化结果</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {!result && (
              <p className="py-16 text-center text-muted-foreground">
                粘贴原文后点击「生成剧本」查看解析结果
              </p>
            )}

            {result && (
              <>
                <Section title={`出场角色（${result.characters.length}）`}>
                  <div className="flex flex-wrap gap-1.5">
                    {result.characters.map((c) => (
                      <Badge key={c} variant="secondary">
                        {c}
                      </Badge>
                    ))}
                  </div>
                </Section>
                <Separator />
                <Section title={`场景列表（${result.scenes.length}）`}>
                  <ul className="list-inside list-disc space-y-1 text-muted-foreground">
                    {result.scenes.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </Section>
                <Separator />
                <Section title={`钩子点（${result.hooks.length}）`}>
                  <ol className="list-inside list-decimal space-y-1 text-muted-foreground">
                    {result.hooks.map((h) => (
                      <li key={h}>{h}</li>
                    ))}
                  </ol>
                </Section>
                <Separator />
                <Section title={`分集建议（${result.episode_suggestions.length}）`}>
                  <div className="space-y-2">
                    {result.episode_suggestions.map((ep) => (
                      <div key={ep.title} className="rounded-md border p-3">
                        <p className="font-medium">{ep.title}</p>
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          {ep.synopsis}
                        </p>
                      </div>
                    ))}
                  </div>
                </Section>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2 font-medium">{title}</p>
      {children}
    </div>
  );
}
