"use client";

import { useCallback, useEffect, useState } from "react";
import {
  addSampleUpload,
  createDataset,
  deleteSample,
  getDataset,
  listDatasets,
  updateSample,
} from "@/lib/api";
import type { DatasetDetail, DatasetSummary } from "@/lib/types";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [newTranscript, setNewTranscript] = useState("");
  const [newSplit, setNewSplit] = useState<"train" | "val">("train");
  const [file, setFile] = useState<File | null>(null);

  const refresh = useCallback(async () => {
    const rows = await listDatasets();
    setDatasets(rows);
    return rows;
  }, []);

  const loadDetail = useCallback(async (id: string) => {
    const d = await getDataset(id);
    setDetail(d);
    setActiveId(id);
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const rows = await refresh();
        if (rows[0]) await loadDetail(rows[0].id);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [refresh, loadDetail]);

  async function onCreate() {
    setError(null);
    try {
      const created = await createDataset(name.trim() || "My voice");
      setName("");
      await refresh();
      await loadDetail(created.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function onAddSample() {
    if (!activeId || !file || !newTranscript.trim()) return;
    setError(null);
    try {
      await addSampleUpload(activeId, file, file.name, newTranscript.trim(), newSplit);
      setFile(null);
      setNewTranscript("");
      await refresh();
      await loadDetail(activeId);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-6 pb-20 pt-6">
      <section className="animate-rise">
        <h1 className="font-display text-3xl text-foam md:text-4xl">Datasets</h1>
        <p className="mt-2 max-w-xl font-sans text-sm text-mist">
          Collect voice ↔ transcript pairs. Mark train and val before fine-tuning.
        </p>
      </section>

      {error && <p className="mt-4 font-sans text-sm text-ember">{error}</p>}

      <div className="mt-8 grid gap-10 lg:grid-cols-[240px_1fr]">
        <aside className="space-y-4">
          <div className="flex gap-2">
            <input
              className="field"
              placeholder="Dataset name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button type="button" className="btn-primary shrink-0" onClick={() => void onCreate()}>
              Add
            </button>
          </div>
          <ul className="space-y-1">
            {datasets.map((d) => (
              <li key={d.id}>
                <button
                  type="button"
                  onClick={() => void loadDetail(d.id)}
                  className={`w-full rounded-md px-3 py-2 text-left font-sans text-sm transition ${
                    activeId === d.id
                      ? "bg-tide/15 text-foam"
                      : "text-mist hover:bg-ink-800/50 hover:text-foam"
                  }`}
                >
                  <span className="block">{d.name}</span>
                  <span className="block text-xs opacity-70">
                    {d.train_count} train · {d.val_count} val
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section>
          {!detail ? (
            <p className="font-sans text-sm text-mist">Create a dataset to start.</p>
          ) : (
            <div className="animate-rise space-y-8">
              <div>
                <h2 className="font-display text-2xl text-foam">{detail.name}</h2>
                <p className="font-sans text-sm text-mist">
                  {detail.train_count} train · {detail.val_count} val
                  {detail.train_count < 30 && (
                    <span className="text-ember"> · recommend ~30+ train samples</span>
                  )}
                </p>
              </div>

              <div className="space-y-3 border-t border-mist/15 pt-6">
                <p className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                  Add sample
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <label className="btn-ghost cursor-pointer">
                    {file ? file.name : "Choose audio"}
                    <input
                      type="file"
                      accept="audio/*"
                      className="hidden"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    />
                  </label>
                  <select
                    className="field w-auto"
                    value={newSplit}
                    onChange={(e) => setNewSplit(e.target.value as "train" | "val")}
                  >
                    <option value="train">train</option>
                    <option value="val">val</option>
                  </select>
                </div>
                <textarea
                  className="field min-h-[80px]"
                  placeholder="Ground-truth transcript"
                  value={newTranscript}
                  onChange={(e) => setNewTranscript(e.target.value)}
                />
                <button
                  type="button"
                  className="btn-primary"
                  disabled={!file || !newTranscript.trim()}
                  onClick={() => void onAddSample()}
                >
                  Add to dataset
                </button>
              </div>

              <div className="space-y-3">
                {detail.samples.length === 0 && (
                  <p className="font-sans text-sm text-mist">No samples yet.</p>
                )}
                {detail.samples.map((s) => (
                  <article
                    key={s.id}
                    className="border-t border-mist/10 py-4"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <select
                        className="field w-auto"
                        value={s.split}
                        onChange={(e) =>
                          void updateSample(detail.id, s.id, {
                            split: e.target.value,
                          }).then(() => loadDetail(detail.id))
                        }
                      >
                        <option value="train">train</option>
                        <option value="val">val</option>
                      </select>
                      <span className="font-sans text-xs text-mist truncate max-w-[280px]">
                        {s.audio_path.split("/").pop()}
                        {s.duration_sec != null
                          ? ` · ${s.duration_sec.toFixed(1)}s`
                          : ""}
                      </span>
                      <button
                        type="button"
                        className="ml-auto font-sans text-xs text-ember hover:underline"
                        onClick={() =>
                          void deleteSample(detail.id, s.id).then(() => {
                            void refresh();
                            void loadDetail(detail.id);
                          })
                        }
                      >
                        Delete
                      </button>
                    </div>
                    <textarea
                      className="field min-h-[70px]"
                      defaultValue={s.transcript}
                      onBlur={(e) => {
                        if (e.target.value !== s.transcript) {
                          void updateSample(detail.id, s.id, {
                            transcript: e.target.value,
                          }).then(() => loadDetail(detail.id));
                        }
                      }}
                    />
                  </article>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
