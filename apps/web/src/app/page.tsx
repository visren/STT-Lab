"use client";

import { useEffect, useMemo, useState } from "react";
import { AudioCapture } from "@/components/AudioCapture";
import { ModelPicker } from "@/components/ModelPicker";
import { ResultsTable } from "@/components/ResultsTable";
import { api } from "@/lib/api";
import type { DatasetOut, ModelInfo, TranscriptResult, TranscribeResponse } from "@/lib/types";

export default function ComparePage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selected, setSelected] = useState<string[]>(["whisper-tiny", "whisper-base"]);
  const [file, setFile] = useState<File | null>(null);
  const [reference, setReference] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TranscribeResponse | null>(null);
  const [datasets, setDatasets] = useState<DatasetOut[]>([]);
  const [saveDatasetId, setSaveDatasetId] = useState("");
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    api
      .models()
      .then((m) => {
        setModels(m);
        const readyLocal = m.filter((x) => x.provider === "local" && x.ready).map((x) => x.id);
        if (readyLocal.length) {
          setSelected(readyLocal.slice(0, 2));
        }
      })
      .catch((e) => setError(e.message));
    api
      .listDatasets()
      .then((d) => {
        setDatasets(d);
        if (d[0]) setSaveDatasetId(d[0].id);
      })
      .catch(() => undefined);
  }, []);

  const readyCount = useMemo(
    () => models.filter((m) => selected.includes(m.id) && m.ready).length,
    [models, selected]
  );

  const run = async () => {
    if (!file || !selected.length) return;
    setRunning(true);
    setError(null);
    setSaveMsg(null);
    try {
      const res = await api.transcribe({
        file,
        filename: file.name,
        modelIds: selected,
        reference: reference.trim() || undefined,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Transcription failed");
    } finally {
      setRunning(false);
    }
  };

  const saveToDataset = async (r: TranscriptResult) => {
    if (!result || !file) return;
    let datasetId = saveDatasetId;
    try {
      if (!datasetId) {
        const created = await api.createDataset(`Voice set ${new Date().toLocaleDateString()}`);
        datasetId = created.id;
        setDatasets((d) => [created, ...d]);
        setSaveDatasetId(created.id);
      }
      const transcript = reference.trim() || r.transcript;
      await api.addSample(datasetId, {
        file,
        filename: file.name,
        transcript,
        split: "train",
        audioPath: result.audio_path,
      });
      setSaveMsg(`Saved clip to dataset using ${r.model_name} / reference text`);
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : "Save failed");
    }
  };

  return (
    <div className="space-y-10">
      <section className="animate-rise grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-5xl font-extrabold leading-[0.95] tracking-tight text-[var(--text)] md:text-6xl">
            STT Lab
          </h1>
          <p className="mt-4 max-w-xl text-lg text-[var(--muted)]">
            Drop a voice sample, pick models, and see who hears you best — then keep the winners
            for fine-tuning.
          </p>
        </div>
        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5 backdrop-blur">
          <div className="mb-3 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Audio input
          </div>
          <AudioCapture file={file} onFile={setFile} />
        </div>
      </section>

      <section className="animate-rise-delay-1 grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5 backdrop-blur">
          <div className="mb-3 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Models
          </div>
          <ModelPicker models={models} selected={selected} onChange={setSelected} />
        </div>
        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5 backdrop-blur">
          <label className="mb-3 block text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Reference transcript (optional)
          </label>
          <textarea
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            rows={6}
            placeholder="Paste the ground-truth text to unlock WER / CER and word diffs."
            className="w-full resize-y rounded-md border border-[var(--line)] bg-black/20 px-3 py-2 text-sm outline-none ring-[var(--accent-2)] focus:ring-1"
          />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              disabled={!file || !readyCount || running}
              onClick={run}
              className="rounded-md bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-[var(--ink)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {running ? "Running…" : `Run ${readyCount || 0} model${readyCount === 1 ? "" : "s"}`}
            </button>
            {running && (
              <span className="inline-flex items-center gap-2 text-sm text-[var(--accent-2)]">
                <span className="spinner inline-block h-4 w-4 rounded-full border-2 border-[var(--accent-2)] border-t-transparent" />
                Transcribing in parallel
              </span>
            )}
          </div>
        </div>
      </section>

      {error && (
        <p className="rounded-md border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">
          {error}
        </p>
      )}

      {result && (
        <section className="space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold">
                Contrast
              </h2>
              <p className="text-sm text-[var(--muted)]">
                Duration{" "}
                {result.audio_duration_sec != null
                  ? `${result.audio_duration_sec.toFixed(1)}s`
                  : "unknown"}
                {" · "}
                click a row for word-level diff
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <label className="text-[var(--muted)]">Save into</label>
              <select
                value={saveDatasetId}
                onChange={(e) => setSaveDatasetId(e.target.value)}
                className="rounded-md border border-[var(--line)] bg-black/30 px-2 py-1"
              >
                <option value="">New dataset</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {saveMsg && <p className="text-sm text-[var(--accent-2)]">{saveMsg}</p>}
          <ResultsTable
            results={result.results}
            hasReference={Boolean(result.reference?.trim())}
            onSave={saveToDataset}
          />
        </section>
      )}
    </div>
  );
}
