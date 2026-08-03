"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DatasetOut, SampleOut } from "@/lib/types";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetOut[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [active, setActive] = useState<DatasetOut | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const refreshList = async () => {
    const list = await api.listDatasets();
    setDatasets(list);
    return list;
  };

  const loadDataset = async (id: string) => {
    const d = await api.getDataset(id);
    setActive(d);
    setActiveId(id);
  };

  useEffect(() => {
    refreshList()
      .then((list) => {
        if (list[0]) return loadDataset(list[0].id);
      })
      .catch((e) => setError(e.message));
  }, []);

  const create = async () => {
    try {
      const d = await api.createDataset(name.trim() || "My voice set");
      setName("");
      await refreshList();
      await loadDataset(d.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    }
  };

  const addUpload = async (file: File) => {
    if (!activeId) return;
    setUploading(true);
    setError(null);
    try {
      await api.addSample(activeId, {
        file,
        filename: file.name,
        transcript: "",
        split: "train",
      });
      await loadDataset(activeId);
      await refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const updateSample = async (sample: SampleOut, patch: { transcript?: string; split?: "train" | "val" }) => {
    if (!activeId) return;
    await api.updateSample(activeId, sample.id, patch);
    await loadDataset(activeId);
    await refreshList();
  };

  const removeSample = async (sampleId: string) => {
    if (!activeId) return;
    await api.deleteSample(activeId, sampleId);
    await loadDataset(activeId);
    await refreshList();
  };

  return (
    <div className="space-y-8">
      <section className="animate-rise">
        <h1 className="font-[family-name:var(--font-display)] text-4xl font-extrabold tracking-tight">
          Datasets
        </h1>
        <p className="mt-2 max-w-2xl text-[var(--muted)]">
          Collect voice↔transcript pairs. Mark a validation split before fine-tuning.
        </p>
      </section>

      {error && (
        <p className="rounded-md border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">
          {error}
        </p>
      )}

      <section className="animate-rise-delay-1 grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
            <div className="mb-2 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
              New dataset
            </div>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
              className="mb-2 w-full rounded-md border border-[var(--line)] bg-black/20 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-[var(--accent-2)]"
            />
            <button
              type="button"
              onClick={create}
              className="w-full rounded-md bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-[var(--ink)]"
            >
              Create
            </button>
          </div>
          <div className="space-y-1">
            {datasets.map((d) => (
              <button
                key={d.id}
                type="button"
                onClick={() => loadDataset(d.id)}
                className={`block w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  d.id === activeId
                    ? "bg-[var(--accent)] text-[var(--ink)]"
                    : "hover:bg-white/5"
                }`}
              >
                <div className="font-medium">{d.name}</div>
                <div className={d.id === activeId ? "opacity-70" : "text-[var(--muted)]"}>
                  {d.train_count} train · {d.val_count} val
                </div>
              </button>
            ))}
          </div>
        </aside>

        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5 backdrop-blur">
          {!active ? (
            <p className="text-[var(--muted)]">Create or select a dataset.</p>
          ) : (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold">
                    {active.name}
                  </h2>
                  <p className="text-sm text-[var(--muted)]">
                    {active.sample_count} samples · warn if under ~30 before fine-tune
                  </p>
                </div>
                <label className="cursor-pointer rounded-md border border-[var(--line)] px-3 py-2 text-sm hover:border-[var(--accent-2)]">
                  {uploading ? "Uploading…" : "Add audio"}
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    disabled={uploading}
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void addUpload(f);
                      e.target.value = "";
                    }}
                  />
                </label>
              </div>

              <div className="space-y-3">
                {active.samples.length === 0 && (
                  <p className="text-sm text-[var(--muted)]">
                    No samples yet. Upload clips or save from Compare.
                  </p>
                )}
                {active.samples.map((s) => (
                  <div
                    key={s.id}
                    className="rounded-lg border border-white/5 bg-black/20 p-3"
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--muted)]">
                      <span className="truncate font-mono">{s.audio_path.split("/").pop()}</span>
                      <div className="flex items-center gap-2">
                        <select
                          value={s.split}
                          onChange={(e) =>
                            updateSample(s, { split: e.target.value as "train" | "val" })
                          }
                          className="rounded border border-[var(--line)] bg-transparent px-2 py-1"
                        >
                          <option value="train">train</option>
                          <option value="val">val</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => removeSample(s.id)}
                          className="text-[var(--danger)]"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    <audio
                      controls
                      src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/audio?path=${encodeURIComponent(s.audio_path)}`}
                      className="mb-2 w-full"
                    />
                    <textarea
                      defaultValue={s.transcript}
                      rows={2}
                      placeholder="Ground-truth transcript"
                      className="w-full rounded-md border border-[var(--line)] bg-transparent px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-[var(--accent-2)]"
                      onBlur={(e) => {
                        if (e.target.value !== s.transcript) {
                          void updateSample(s, { transcript: e.target.value });
                        }
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
