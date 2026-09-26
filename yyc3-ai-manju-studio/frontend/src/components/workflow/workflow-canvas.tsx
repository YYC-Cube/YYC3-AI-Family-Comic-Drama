"use client";

/**
 * 六阶段流水线画布：SVG 绘制，节点可点击
 */
import { cn } from "@/lib/utils";
import { STAGE_COLORS } from "@/lib/constants";

export type StageStatus = "idle" | "running" | "done" | "failed";

export interface WorkflowStage {
  key: string;
  name: string;
  status: StageStatus;
}

/** 状态视觉配置：描边色 / 填充 / 中文标签 */
const STATUS_STYLE: Record<StageStatus, { stroke: string; fill: string; label: string }> = {
  idle: { stroke: "#94a3b8", fill: "#f8fafc", label: "待启动" },
  running: { stroke: "#2563eb", fill: "#dbeafe", label: "进行中" },
  done: { stroke: "#16a34a", fill: "#dcfce7", label: "已完成" },
  failed: { stroke: "#dc2626", fill: "#fee2e2", label: "失败" },
};

const NODE_W = 150;
const NODE_H = 110;
const GAP = 46;
const ORIGIN_X = 20;
const ORIGIN_Y = 24;
const CANVAS_H = 210;

interface WorkflowCanvasProps {
  stages: WorkflowStage[];
  onSelect?: (key: string) => void;
  className?: string;
}

export function WorkflowCanvas({ stages, onSelect, className }: WorkflowCanvasProps) {
  const count = Math.max(stages.length, 1);
  const width = ORIGIN_X * 2 + count * NODE_W + (count - 1) * GAP;

  const nodeX = (i: number) => ORIGIN_X + i * (NODE_W + GAP);
  const centerY = ORIGIN_Y + NODE_H / 2;

  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <svg
        viewBox={`0 0 ${width} ${CANVAS_H}`}
        className="h-auto w-full min-w-[760px]"
        role="img"
        aria-label="六阶段生产流水线"
      >
        <defs>
          <marker
            id="arrow-solid"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
          </marker>
          <marker
            id="arrow-dashed"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#c084fc" />
          </marker>
        </defs>

        {/* 相邻节点实线箭头 */}
        {stages.slice(0, -1).map((_, i) => (
          <line
            key={`edge-${i}`}
            x1={nodeX(i) + NODE_W + 4}
            y1={centerY}
            x2={nodeX(i + 1) - 6}
            y2={centerY}
            stroke="#94a3b8"
            strokeWidth="2"
            markerEnd="url(#arrow-solid)"
          />
        ))}

        {/* 阶段 6 → 阶段 1 虚线反哺箭头（绕行底部） */}
        {stages.length >= 2 && (
          <path
            d={[
              `M ${nodeX(stages.length - 1) + NODE_W / 2} ${ORIGIN_Y + NODE_H + 6}`,
              `L ${nodeX(stages.length - 1) + NODE_W / 2} ${ORIGIN_Y + NODE_H + 44}`,
              `L ${nodeX(0) + NODE_W / 2} ${ORIGIN_Y + NODE_H + 44}`,
              `L ${nodeX(0) + NODE_W / 2} ${ORIGIN_Y + NODE_H + 6}`,
            ].join(" ")}
            fill="none"
            stroke="#c084fc"
            strokeWidth="2"
            strokeDasharray="6 4"
            markerEnd="url(#arrow-dashed)"
          />
        )}

        {/* 阶段节点 */}
        {stages.map((stage, i) => {
          const style = STATUS_STYLE[stage.status];
          const color = STAGE_COLORS[stage.key] ?? "#64748b";
          return (
            <g
              key={stage.key}
              onClick={() => onSelect?.(stage.key)}
              className={onSelect ? "cursor-pointer" : undefined}
            >
              <rect
                x={nodeX(i)}
                y={ORIGIN_Y}
                width={NODE_W}
                height={NODE_H}
                rx={18}
                fill={style.fill}
                stroke={style.stroke}
                strokeWidth={stage.status === "running" ? 3 : 2}
              />
              {/* 阶段序号圆点 */}
              <circle cx={nodeX(i) + 26} cy={ORIGIN_Y + 28} r={13} fill={color} />
              <text
                x={nodeX(i) + 26}
                y={ORIGIN_Y + 33}
                textAnchor="middle"
                fontSize="13"
                fontWeight="700"
                fill="#ffffff"
              >
                {i + 1}
              </text>
              {/* 中文阶段名 */}
              <text
                x={nodeX(i) + NODE_W / 2}
                y={ORIGIN_Y + 66}
                textAnchor="middle"
                fontSize="16"
                fontWeight="600"
                fill="#0f172a"
              >
                {stage.name}
              </text>
              {/* 状态标签 */}
              <text
                x={nodeX(i) + NODE_W / 2}
                y={ORIGIN_Y + 90}
                textAnchor="middle"
                fontSize="12"
                fill={style.stroke}
              >
                {style.label}
              </text>
            </g>
          );
        })}

        {/* 反哺标注 */}
        {stages.length >= 2 && (
          <text
            x={width / 2}
            y={ORIGIN_Y + NODE_H + 60}
            textAnchor="middle"
            fontSize="12"
            fill="#c084fc"
          >
            运营数据反哺下一轮创意
          </text>
        )}
      </svg>
    </div>
  );
}
