"use client";

/**
 * 剧本编辑页
 */
import { PageHeader } from "@/components/layout/page-header";
import { ScriptEditor } from "@/components/editor/script-editor";
import { useProjectStore } from "@/store/use-project-store";

export default function ScriptPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);

  return (
    <div>
      <PageHeader
        title="剧本编辑"
        description="粘贴小说原文，AI 生成结构化剧本并提取分镜"
      />
      {activeProjectId && <ScriptEditor projectId={activeProjectId} />}
    </div>
  );
}
