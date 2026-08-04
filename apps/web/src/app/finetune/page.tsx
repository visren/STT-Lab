"use client";

import { useCallback, useEffect, useState } from "react";
import {
  cancelFinetune,
  evaluate,
  getFinetuneJob,
  listDatasets,
  listFinetuneJobs,
  startFinetune,
} from "@/lib/api";
import type { DatasetSummary, EvaluateResponse, FinetuneJob } from "@/lib/types";

export default function FinetunePage() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [jobs, setJobs] = useState<FinetuneJob[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [baseModel, setBaseModel] = useState("tiny");
  const [epochs, setEpochs] = useState(3);
  const [loraRank, setLoraRank] = useState(16);
  const [lr, setLr] = useState(0.0001);
  const [batchSize, setBatchSize] = useState(1);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<FinetuneJob | null>(null);
  const [evalResult, setEvalResult] = useState<EvaluateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const [d, j] = await Promise.all([listDatasets(), listFinetuneJobs()]);
    setDatasets(d);
    setJobs(j);
    if (!datasetId && d[0]) setDatasetId(d[0].id);
    return j;
  }, [datasetId]);

  useEffect(() => {
    void refresh().catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [refresh]);

  useEffect(() => {
    if (!activeJobId) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const job = await getFinetuneJob(activeJobId);
        if (cancelled) return;
        setActiveJob(job);
        if (["completed", "failed", "cancelled"].includes(job.status)) {
          void refresh();
          return;
        }
        window.setTimeout(() => void tick(), 1500);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    };
    void tick();
    return () => {
      cancelled = true;
    };
  }, [activeJobId, refresh]);

  const selected = datasets.find((d) => d.id === datasetId);
  const lowSamples = (selected?.train_count ?? 0) < 30;

  async function onStart() {
    setError(null);
    setEvalResult(null);
    setBusy(true);
    try {
      const job = await startFinetune({
        dataset_id: datasetId,
        base_model: baseModel,
        epochs,
        lora_rank: loraRank,
        learning_rate: lr,
        batch_size: batchSize,
        language: "en",
      });
      setActiveJobId(job.id);
      setActiveJob(job);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onEvaluate() {
    if (!activeJob || activeJob.status !== "completed") return;
    setBusy(true);
    setError(null);
    try {
      const result = await evaluate({
        dataset_id: activeJob.dataset_id,
        base_model: activeJob.base_model,
        adapter_id: activeJob.id,
        split: "val",
      });
      setEvalResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-6 pb-20 pt-6">
      <section className="animate-rise">
        <h1 className="font-display text-3xl text-foam md:text-4xl">Fine-tune</h1>
        <p className="mt-2 max-w-xl font-sans text-sm text-mist">
          LoRA-adapt a Whisper checkpoint on your dataset, then measure before/after WER.
        </p>
      </section>

      {error && <p className="mt-4 font-sans text-sm text-ember">{error}</p>}

      <div className="mt-8 grid gap-10 lg:grid-cols-2">
        <section className="animate-rise space-y-4">
          <label className="block space-y-1">
            <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
              Dataset
            </span>
            <select
              className="field"
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} — {d.train_count} train / {d.val_count} val
                </option>
              ))}
            </select>
          </label>

          {lowSamples && selected && (
            <p className="font-sans text-xs text-ember">
              Warning: only {selected.train_count} train samples. Aim for ~30+ for useful adaptation.
            </p>
          )}
          {selected && selected.val_count < 1 && (
            <p className="font-sans text-xs text-ember">
              Add at least one val sample before starting.
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <label className="block space-y-1">
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                Base model
              </span>
              <select
                className="field"
                value={baseModel}
                onChange={(e) => setBaseModel(e.target.value)}
              >
                {["tiny", "base", "small", "medium"].map((s) => (
                  <option key={s} value={s}>
                    whisper-{s}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1">
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                Epochs
              </span>
              <input
                className="field"
                type="number"
                min={1}
                max={20}
                value={epochs}
                onChange={(e) => setEpochs(Number(e.target.value))}
              />
            </label>
            <label className="block space-y-1">
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                LoRA rank
              </span>
              <input
                className="field"
                type="number"
                min={4}
                max={64}
                value={loraRank}
                onChange={(e) => setLoraRank(Number(e.target.value))}
              />
            </label>
            <label className="block space-y-1">
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                Learning rate
              </span>
              <input
                className="field"
                type="number"
                step="0.00001"
                value={lr}
                onChange={(e) => setLr(Number(e.target.value))}
              />
            </label>
            <label className="block space-y-1">
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                Batch size
              </span>
              <input
                className="field"
                type="number"
                min={1}
                max={8}
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
              />
            </label>
          </div>

          <p className="font-sans text-xs text-mist">
            Runs locally on CUDA / MPS / CPU. CPU is for tiny demos only and will be slow.
          </p>

          <button
            type="button"
            className="btn-primary"
            disabled={!datasetId || busy}
            onClick={() => void onStart()}
          >
            Start LoRA job
          </button>
        </section>

        <section className="animate-rise space-y-4">
          <h2 className="font-display text-2xl text-foam">Job status</h2>
          {!activeJob ? (
            <p className="font-sans text-sm text-mist">
              Start a job or select one from recent runs.
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-sans text-sm text-foam">
                  {activeJob.status} · whisper-{activeJob.base_model}
                </span>
                <span className="font-sans text-xs text-mist">
                  {activeJob.id.slice(0, 8)}
                </span>
                {["queued", "running"].includes(activeJob.status) && (
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() =>
                      void cancelFinetune(activeJob.id).then((j) => setActiveJob(j))
                    }
                  >
                    Cancel
                  </button>
                )}
                {activeJob.status === "completed" && (
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={busy}
                    onClick={() => void onEvaluate()}
                  >
                    Evaluate vs base
                  </button>
                )}
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-ink-800">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    activeJob.status === "running" ? "shimmer-bar" : "bg-tide"
                  }`}
                  style={{ width: `${Math.round((activeJob.progress || 0) * 100)}%` }}
                />
              </div>
              {activeJob.error && (
                <p className="font-sans text-sm text-ember">{activeJob.error}</p>
              )}
              <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-md bg-ink-950/70 p-3 font-sans text-xs text-mist">
                {activeJob.logs || "Waiting for logs…"}
              </pre>
            </div>
          )}

          {evalResult && (
            <div className="mt-6 space-y-3 border-t border-mist/15 pt-6">
              <h3 className="font-display text-xl text-foam">Before / after</h3>
              <div className="grid grid-cols-3 gap-3 font-sans text-sm">
                <div>
                  <p className="text-xs uppercase tracking-[0.12em] text-mist">Base WER</p>
                  <p className="text-foam tabular-nums">
                    {evalResult.base_wer?.toFixed(3) ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.12em] text-mist">Adapted WER</p>
                  <p className="text-foam tabular-nums">
                    {evalResult.adapted_wer?.toFixed(3) ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.12em] text-mist">Δ WER</p>
                  <p
                    className={`tabular-nums ${
                      (evalResult.delta_wer ?? 0) < 0 ? "text-tide" : "text-ember"
                    }`}
                  >
                    {evalResult.delta_wer != null
                      ? `${evalResult.delta_wer > 0 ? "+" : ""}${evalResult.delta_wer.toFixed(3)}`
                      : "—"}
                  </p>
                </div>
              </div>
              <p className="font-sans text-xs text-mist">
                Negative Δ WER means the adapted model improved. Adapted models appear in Compare.
              </p>
              <div className="space-y-2">
                {evalResult.samples.map((s) => (
                  <div key={s.sample_id} className="border-t border-mist/10 py-2 font-sans text-xs">
                    <p className="text-mist">ref: {s.reference}</p>
                    <p className="text-foam/80">base: {s.base_transcript}</p>
                    <p className="text-tide/90">adapted: {s.adapted_transcript}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-mist/15 pt-6">
            <p className="mb-2 font-sans text-xs uppercase tracking-[0.14em] text-mist">
              Recent jobs
            </p>
            <ul className="space-y-1">
              {jobs.map((j) => (
                <li key={j.id}>
                  <button
                    type="button"
                    className="w-full rounded-md px-2 py-1.5 text-left font-sans text-sm text-mist hover:bg-ink-800/50 hover:text-foam"
                    onClick={() => {
                      setActiveJobId(j.id);
                      setActiveJob(j);
                      setEvalResult(null);
                    }}
                  >
                    {j.status} · whisper-{j.base_model} · {j.id.slice(0, 8)}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
