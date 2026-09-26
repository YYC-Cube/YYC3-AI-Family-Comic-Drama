"use client";

/**
 * 资产管理：角色一致性资产库
 */
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { mockCharacters } from "@/lib/mock-operations";
import { cn } from "@/lib/utils";

export default function AssetsPage() {
  return (
    <div>
      <PageHeader
        title="资产管理"
        description="角色一致性资产：512 维特征向量锚定，跨镜头保持人设统一"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {mockCharacters.map((character) => (
          <Card key={character.anchor_id}>
            <CardContent className="flex items-start gap-4 p-5">
              {/* 首字母圆形头像（渐变背景） */}
              <div
                className={cn(
                  "flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-lg font-bold text-white",
                  character.gradient
                )}
                aria-hidden
              >
                {character.name.charAt(0)}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate font-medium">{character.name}</p>
                  <Badge variant={character.indexed ? "success" : "warning"}>
                    {character.vector_dim}维 {character.indexed ? "已建库" : "待建库"}
                  </Badge>
                </div>
                <p className="mt-1 font-mono text-xs text-muted-foreground">
                  {character.anchor_id}
                </p>
                <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                  <span>使用 {character.usage_count} 次</span>
                  <span>来源：{character.source}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
