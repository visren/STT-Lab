import type { DiffOp } from "@/lib/types";

export function DiffView({ ops }: { ops: DiffOp[] }) {
  if (!ops.length) {
    return <p className="text-sm text-mist/70">No diff available.</p>;
  }
  return (
    <p className="font-sans text-sm leading-relaxed text-foam/90">
      {ops.map((op, i) => {
        if (op.op === "equal") {
          return (
            <span key={i} className="mr-1">
              {op.text}
            </span>
          );
        }
        if (op.op === "insert") {
          return (
            <span
              key={i}
              className="mr-1 rounded bg-tide/25 px-1 text-tide underline decoration-tide/50"
            >
              +{op.text}
            </span>
          );
        }
        if (op.op === "delete") {
          return (
            <span
              key={i}
              className="mr-1 rounded bg-ember/20 px-1 text-ember line-through decoration-ember/60"
            >
              {op.text}
            </span>
          );
        }
        return (
          <span key={i} className="mr-1 rounded bg-mist/20 px-1">
            {op.text}
          </span>
        );
      })}
    </p>
  );
}
