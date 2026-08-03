"use client";

import type { ModelInfo } from "@/lib/types";

const providerLabel: Record<string, string> = {
  local: "Local",
  openai: "OpenAI",
  deepgram: "Deepgram",
  assemblyai: "AssemblyAI",
  adapted: "Adapted",
};

export function ModelPicker({
  models,
  selected,
  onChange,
}: {
  models: ModelInfo[];
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const toggle = (id: string, ready: boolean) => {
    if (!ready) return;
    if (selected.includes(id)) {
      onChange(selected.filter((x) => x !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const groups = models.reduce<Record<string, ModelInfo[]>>((acc, m) => {
    (acc[m.provider] ||= []).push(m);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {Object.entries(groups).map(([provider, items]) => (
        <div key={provider}>
          <div className="mb-2 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            {providerLabel[provider] || provider}
          </div>
          <div className="flex flex-wrap gap-2">
            {items.map((m) => {
              const on = selected.includes(m.id);
              return (
                <button
                  key={m.id}
                  type="button"
                  disabled={!m.ready}
                  title={m.reason || undefined}
                  onClick={() => toggle(m.id, m.ready)}
                  className={`rounded-md border px-3 py-1.5 text-sm transition-all ${
                    on
                      ? "border-[var(--accent)] bg-[var(--accent)] text-[var(--ink)]"
                      : m.ready
                        ? "border-[var(--line)] bg-transparent text-[var(--text)] hover:border-[var(--accent-2)]"
                        : "cursor-not-allowed border-transparent bg-white/5 text-[var(--muted)] opacity-60"
                  }`}
                >
                  {m.name}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
