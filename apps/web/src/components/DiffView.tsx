import type { DiffOp } from "@/lib/types";

export function DiffView({ ops }: { ops: DiffOp[] }) {
  if (!ops.length) {
    return <span className="text-[var(--muted)]">No diff available</span>;
  }
  return (
    <p className="flex flex-wrap gap-x-1.5 gap-y-1 font-mono text-sm leading-relaxed">
      {ops.map((op, i) => (
        <span
          key={`${op.op}-${i}-${op.text}`}
          className={
            op.op === "equal"
              ? "diff-equal"
              : op.op === "insert"
                ? "diff-insert"
                : "diff-delete"
          }
        >
          {op.text}
        </span>
      ))}
    </p>
  );
}
