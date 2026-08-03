"use client";

import { Fragment, useState } from "react";
import type { TranscriptResult } from "@/lib/types";
import { DiffView } from "./DiffView";

function fmtMs(ms: number) {
  if (ms < 1000) return `${ms.toFixed(0)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

function fmtPct(v: number | null | undefined) {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

export function ResultsTable({
  results,
  hasReference,
  onSave,
}: {
  results: TranscriptResult[];
  hasReference: boolean;
  onSave?: (result: TranscriptResult) => void;
}) {
  const [open, setOpen] = useState<string | null>(results[0]?.model_id ?? null);

  if (!results.length) return null;

  return (
    <div className="animate-rise-delay-2 overflow-x-auto rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur">
      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--line)] text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
            <th className="px-4 py-3 font-medium">Model</th>
            <th className="px-4 py-3 font-medium">Latency</th>
            <th className="px-4 py-3 font-medium">WER</th>
            <th className="px-4 py-3 font-medium">CER</th>
            <th className="px-4 py-3 font-medium">Transcript</th>
            {onSave && <th className="px-4 py-3 font-medium">Save</th>}
          </tr>
        </thead>
        <tbody>
          {results.map((r) => {
            const expanded = open === r.model_id;
            return (
              <Fragment key={r.model_id}>
                <tr
                  className="cursor-pointer border-b border-white/5 transition-colors hover:bg-white/[0.03]"
                  onClick={() => setOpen(expanded ? null : r.model_id)}
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-[var(--text)]">{r.model_name}</div>
                    <div className="text-xs text-[var(--muted)]">{r.provider}</div>
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {r.error ? "—" : fmtMs(r.latency_ms)}
                    {r.rtf != null && !r.error && (
                      <div className="text-xs text-[var(--muted)]">{r.rtf.toFixed(2)}× RTF</div>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {hasReference ? (
                      fmtPct(r.wer)
                    ) : (
                      <span className="text-[var(--muted)]">needs ref</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {hasReference ? (
                      fmtPct(r.cer)
                    ) : (
                      <span className="text-[var(--muted)]">needs ref</span>
                    )}
                  </td>
                  <td className="max-w-md px-4 py-3">
                    {r.error ? (
                      <span className="text-[var(--danger)]">{r.error}</span>
                    ) : (
                      <span className="line-clamp-2 text-[var(--text)]">
                        {r.transcript || "∅"}
                      </span>
                    )}
                  </td>
                  {onSave && (
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        className="rounded border border-[var(--line)] px-2 py-1 text-xs hover:border-[var(--accent)]"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSave(r);
                        }}
                      >
                        To dataset
                      </button>
                    </td>
                  )}
                </tr>
                {expanded && !r.error && (
                  <tr className="border-b border-white/5 bg-black/20">
                    <td colSpan={onSave ? 6 : 5} className="px-4 py-4">
                      <div className="mb-2 text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
                        Word diff vs reference
                      </div>
                      <DiffView ops={r.diff_ops} />
                      <div className="mt-3 whitespace-pre-wrap text-[var(--muted)]">
                        {r.transcript}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
