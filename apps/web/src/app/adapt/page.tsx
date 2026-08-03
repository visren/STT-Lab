"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { DatasetOut, EvaluateResponse, FinetuneJobOut } from "@/lib/types";

const BASES = ["tiny", "base", "small", "medium"] as const;

export default function AdaptPage() {
  const [datasets, setDatasets] = useState<DatasetOut[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [baseModel, setBaseModel] = useState<(typeof BASES)[number]>("tiny");
  const [loraRank, setLoraRank] = useState(16);
  const [epochs, setEpochs] = useState(3);
  const [lr, setLr] = useState(1e-4);
  const [jobs, setJobs] = useState<FinetuneJobOut[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<FinetuneJobOut | null>(null);
  const [evalResult, setEvalResult] = useState<EvaluateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const selectedDataset = useMemo(
    () => datasets.find((d) => d.id === datasetId) || null,
    [datasets, datasetId]
  );

  const refreshJobs = async () => {
    const list = await api.listFinetuneJobs();
    setJobs(list);
    return list;
  };

  useEffect(() => {
    api
      .listDatasets()
      .then((d) => {
        setDatasets(d);
        if (d[0]) setDatasetId(d[0].id);
      })
      .catch((e) => setError(e.message));
    refreshJobs().catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!activeJobId) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const job = await api.getFinetuneJob(activeJobId);
        if (cancelled) return;
        setActiveJob(job);
        if (job.status === "queued" || job.status === "running") {
          setTimeout(tick, 1500);
        } else {
          void refreshJobs();
        }
      } catch {
        /* ignore transient */
      }
    };
    void tick();
    return () => {
      cancelled = true;
    };
  }, [activeJobId]);

  const start = async () => {
    if (!datasetId) return;
    setBusy(true);
    setError(null);
    setEvalResult(null);
    try {
      const job = await api.startFinetune({
        dataset_id: datasetId,
        base_model: baseModel,
        lora_rank: loraRank,
        epochs,
        learning_rate: lr,
      });
      setActiveJobId(job.id);
      setActiveJob(job);
      await refreshJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start job");
    } finally {
      setBusy(false);
    }
  };

  const cancel = async () => {
    if (!activeJobId) return;
    const job = await api.cancelFinetune(activeJobId);
    setActiveJob(job);
    await refreshJobs();
  };

  const runEval = async (job: FinetuneJobOut) => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.evaluate({
        dataset_id: job.dataset_id,
        base_model: job.base_model as (typeof BASES)[number],
        adapter_id: job.id,
        split: "val",
      });
      setEvalResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed");
    } finally {
      setBusy(false);
    }
  };

  const lowSamples = (selectedDataset?.train_count ?? 0) < 30;

  return (
    <div className="space-y-8">
      <section className="animate-rise">
        <h1 className="font-[family-name:var(--font-display)] text-4xl font-extrabold tracking-tight">
          Adapt
        </h1>
        <p className="mt-2 max-w-2xl text-[var(--muted)]">
          LoRA-fine-tune Whisper on your personal dataset, then measure before/after WER on the
          validation split.
        </p>
      </section>

      {error && (
        <p className="rounded-md border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">
          {error}
        </p>
      )}

      <section className="animate-rise-delay-1 grid gap-6 lg:grid-cols-2">
        <div className="space-y-4 rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5">
          <div className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Fine-tune wizard
          </div>

          <label className="block text-sm">
            <span className="text-[var(--muted)]">Dataset</span>
            <select
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-3 py-2"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.train_count} train / {d.val_count} val)
                </option>
              ))}
            </select>
          </label>

          {lowSamples && selectedDataset && (
            <p className="rounded-md border border-[var(--warn)]/40 bg-[var(--warn)]/10 px-3 py-2 text-sm text-[var(--warn)]">
              Only {selectedDataset.train_count} train samples — results improve with ~30+.
            </p>
          )}

          <label className="block text-sm">
            <span className="text-[var(--muted)]">Base Whisper</span>
            <select
              value={baseModel}
              onChange={(e) => setBaseModel(e.target.value as (typeof BASES)[number])}
              className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-3 py-2"
            >
              {BASES.map((b) => (
                <option key={b} value={b}>
                  whisper-{b}
                </option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-3 gap-3 text-sm">
            <label>
              <span className="text-[var(--muted)]">LoRA rank</span>
              <input
                type="number"
                min={4}
                max={64}
                value={loraRank}
                onChange={(e) => setLoraRank(Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-2 py-2"
              />
            </label>
            <label>
              <span className="text-[var(--muted)]">Epochs</span>
              <input
                type="number"
                min={1}
                max={20}
                value={epochs}
                onChange={(e) => setEpochs(Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-2 py-2"
              />
            </label>
            <label>
              <span className="text-[var(--muted)]">LR</span>
              <input
                type="number"
                step="0.00001"
                value={lr}
                onChange={(e) => setLr(Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-2 py-2"
              />
            </label>
          </div>

          <p className="text-xs text-[var(--muted)]">
            Runtime depends on hardware. MPS/CUDA preferred; CPU is demo-only and very slow.
          </p>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!datasetId || busy}
              onClick={start}
              className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-[var(--ink)] disabled:opacity-40"
            >
              Start fine-tune
            </button>
            {activeJob && (activeJob.status === "queued" || activeJob.status === "running") && (
              <button
                type="button"
                onClick={cancel}
                className="rounded-md border border-[var(--danger)] px-4 py-2 text-sm text-[var(--danger)]"
              >
                Cancel
              </button>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5">
          <div className="mb-3 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Active job
          </div>
          {!activeJob ? (
            <p className="text-sm text-[var(--muted)]">No job selected. Start one or pick from history.</p>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium">
                    whisper-{activeJob.base_model} · {activeJob.status}
                  </div>
                  <div className="font-mono text-xs text-[var(--muted)]">{activeJob.id}</div>
                </div>
                {activeJob.status === "completed" && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => runEval(activeJob)}
                    className="rounded-md bg-[var(--accent-2)] px-3 py-1.5 text-sm font-medium text-[var(--ink)]"
                  >
                    Evaluate vs base
                  </button>
                )}
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-black/40">
                <div
                  className="h-full bg-[var(--accent)] transition-all duration-500"
                  style={{ width: `${Math.round(activeJob.progress * 100)}%` }}
                />
              </div>
              <pre className="max-h-64 overflow-auto rounded-md bg-black/30 p-3 font-mono text-xs leading-relaxed text-[var(--muted)]">
                {activeJob.logs || "Waiting for logs…"}
              </pre>
              {activeJob.error && (
                <p className="text-sm text-[var(--danger)]">{activeJob.error}</p>
              )}
            </div>
          )}
        </div>
      </section>

      {evalResult && (
        <section className="animate-rise space-y-4 rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5">
          <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold">
            Before / after
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <Metric
              label="Base WER"
              value={evalResult.base_wer}
            />
            <Metric
              label="Adapted WER"
              value={evalResult.adapted_wer}
            />
            <Metric
              label="Δ WER"
              value={evalResult.delta_wer}
              emphasize
            />
          </div>
          <p className="text-sm text-[var(--muted)]">
            {evalResult.sample_count} val samples · negative Δ means the adapted model improved
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.12em] text-[var(--muted)]">
                <tr>
                  <th className="py-2 pr-3">Reference</th>
                  <th className="py-2 pr-3">Base</th>
                  <th className="py-2 pr-3">Adapted</th>
                  <th className="py-2">WER</th>
                </tr>
              </thead>
              <tbody>
                {evalResult.samples.map((s) => (
                  <tr key={s.sample_id} className="border-t border-white/5 align-top">
                    <td className="py-2 pr-3">{s.reference}</td>
                    <td className="py-2 pr-3 text-[var(--muted)]">{s.base_transcript}</td>
                    <td className="py-2 pr-3">{s.adapted_transcript}</td>
                    <td className="py-2 font-mono text-xs">
                      {s.base_wer != null ? `${(s.base_wer * 100).toFixed(1)}%` : "—"}
                      {" → "}
                      {s.adapted_wer != null ? `${(s.adapted_wer * 100).toFixed(1)}%` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-bold">Job history</h2>
        <div className="space-y-2">
          {jobs.map((j) => (
            <button
              key={j.id}
              type="button"
              onClick={() => {
                setActiveJobId(j.id);
                setActiveJob(j);
              }}
              className="flex w-full items-center justify-between rounded-md border border-[var(--line)] px-3 py-2 text-left text-sm hover:border-[var(--accent-2)]"
            >
              <span>
                whisper-{j.base_model} · {j.status}
                <span className="ml-2 font-mono text-xs text-[var(--muted)]">{j.id.slice(0, 8)}</span>
              </span>
              <span className="text-[var(--muted)]">{Math.round(j.progress * 100)}%</span>
            </button>
          ))}
          {!jobs.length && <p className="text-sm text-[var(--muted)]">No jobs yet.</p>}
        </div>
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  emphasize,
}: {
  label: string;
  value?: number | null;
  emphasize?: boolean;
}) {
  const text =
    value == null ? "—" : emphasize ? `${(value * 100).toFixed(1)} pts` : `${(value * 100).toFixed(1)}%`;
  const color =
    emphasize && value != null
      ? value < 0
        ? "text-[var(--ok)]"
        : value > 0
          ? "text-[var(--danger)]"
          : "text-[var(--text)]"
      : "text-[var(--text)]";
  return (
    <div className="rounded-lg border border-white/5 bg-black/20 p-4">
      <div className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">{label}</div>
      <div className={`mt-1 font-[family-name:var(--font-display)] text-3xl font-bold ${color}`}>
        {text}
      </div>
    </div>
  );
}
