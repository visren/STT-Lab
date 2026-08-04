"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  addSampleFromPath,
  createDataset,
  fetchModels,
  listDatasets,
  transcribe,
} from "@/lib/api";
import type { DatasetSummary, ModelInfo, TranscribeResponse } from "@/lib/types";
import { DiffView } from "./DiffView";

function fmtMs(ms: number) {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

function fmtMetric(v: number | null | undefined) {
  if (v == null) return "—";
  return v.toFixed(3);
}

export function CompareStudio() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selected, setSelected] = useState<string[]>(["whisper-tiny", "whisper-base"]);
  const [reference, setReference] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<TranscribeResponse | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [saveDatasetId, setSaveDatasetId] = useState("");
  const [saveSplit, setSaveSplit] = useState<"train" | "val">("train");
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const load = useCallback(async () => {
    try {
      const [m, d] = await Promise.all([fetchModels(), listDatasets()]);
      setModels(m);
      setDatasets(d);
      if (d[0] && !saveDatasetId) setSaveDatasetId(d[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [saveDatasetId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const readyModels = useMemo(
    () => models.filter((m) => selected.includes(m.id)),
    [models, selected],
  );

  function toggleModel(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  function onFile(f: File | null) {
    setFile(f);
    setResponse(null);
    setSaveMsg(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(f ? URL.createObjectURL(f) : null);
  }

  async function startRecording() {
    setError(null);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (ev) => {
      if (ev.data.size) chunksRef.current.push(ev.data);
    };
    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      const f = new File([blob], `recording-${Date.now()}.webm`, {
        type: "audio/webm",
      });
      onFile(f);
    };
    mediaRef.current = recorder;
    recorder.start();
    setRecording(true);
  }

  function stopRecording() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  async function runCompare() {
    if (!file || selected.length === 0) return;
    setRunning(true);
    setError(null);
    setSaveMsg(null);
    setResponse(null);
    try {
      const resp = await transcribe({
        audio: file,
        filename: file.name,
        modelIds: selected,
        reference: reference.trim() || undefined,
      });
      setResponse(resp);
      setExpanded(resp.results[0]?.model_id ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  async function saveToDataset() {
    if (!response) return;
    setSaveMsg(null);
    try {
      let datasetId = saveDatasetId;
      if (!datasetId) {
        const created = await createDataset(`Voice ${new Date().toLocaleDateString()}`);
        datasetId = created.id;
        setSaveDatasetId(datasetId);
      }
      const transcript = reference.trim() || response.results.find((r) => r.transcript)?.transcript || "";
      if (!transcript) throw new Error("Need a reference or hypothesis transcript to save");
      await addSampleFromPath(datasetId, response.audio_path, transcript, saveSplit);
      setSaveMsg(`Saved to dataset as ${saveSplit}`);
      const d = await listDatasets();
      setDatasets(d);
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-6 pb-20 pt-6">
      <section className="animate-rise">
        <p className="max-w-xl font-sans text-base text-mist">
          Record or upload a clip, pick models, and contrast transcripts against your voice.
        </p>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-3">
              <label className="btn-ghost cursor-pointer">
                Upload audio
                <input
                  type="file"
                  accept="audio/*"
                  className="hidden"
                  onChange={(e) => onFile(e.target.files?.[0] ?? null)}
                />
              </label>
              {!recording ? (
                <button type="button" className="btn-ghost" onClick={() => void startRecording()}>
                  Record
                </button>
              ) : (
                <button type="button" className="btn-primary" onClick={stopRecording}>
                  Stop recording
                </button>
              )}
              {file && (
                <span className="font-sans text-xs text-mist truncate max-w-[220px]">
                  {file.name}
                </span>
              )}
            </div>

            {audioUrl && (
              <audio controls src={audioUrl} className="w-full opacity-90" />
            )}

            <label className="block space-y-2">
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
                Reference transcript
              </span>
              <textarea
                className="field min-h-[110px] resize-y"
                placeholder="Optional — enables WER / CER and word diffs"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
              />
            </label>

            <button
              type="button"
              className="btn-primary min-w-[140px]"
              disabled={!file || selected.length === 0 || running}
              onClick={() => void runCompare()}
            >
              {running ? "Running…" : "Run compare"}
            </button>
          </div>

          <div>
            <p className="mb-3 font-sans text-xs uppercase tracking-[0.14em] text-mist">
              Models
            </p>
            <div className="flex max-h-[320px] flex-col gap-2 overflow-y-auto pr-1">
              {models.map((m) => {
                const on = selected.includes(m.id);
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => toggleModel(m.id)}
                    className={`flex items-start justify-between gap-3 rounded-md border px-3 py-2 text-left transition ${
                      on
                        ? "border-tide/50 bg-tide/10"
                        : "border-mist/15 bg-ink-950/40 hover:border-mist/30"
                    } ${!m.ready ? "opacity-60" : ""}`}
                  >
                    <span>
                      <span className="block font-sans text-sm text-foam">{m.name}</span>
                      <span className="block font-sans text-xs text-mist">
                        {m.provider}
                        {!m.ready && m.reason ? ` · ${m.reason}` : ""}
                      </span>
                    </span>
                    <span
                      className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${
                        on ? "bg-ember" : "bg-mist/30"
                      }`}
                    />
                  </button>
                );
              })}
            </div>
            <p className="mt-2 font-sans text-xs text-mist/70">
              {readyModels.length} selected
            </p>
          </div>
        </div>
      </section>

      {running && (
        <div className="mt-10 animate-rise">
          <div className="h-1 w-full overflow-hidden rounded-full bg-ink-800">
            <div className="shimmer-bar h-full w-2/3" />
          </div>
          <p className="mt-2 font-sans text-sm text-mist animate-pulse-bar">
            Transcribing across {selected.length} model{selected.length === 1 ? "" : "s"}…
          </p>
        </div>
      )}

      {error && (
        <p className="mt-6 animate-rise font-sans text-sm text-ember">{error}</p>
      )}

      {response && (
        <section className="mt-12 animate-rise">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-display text-3xl text-foam">Contrast</h2>
              <p className="font-sans text-sm text-mist">
                Duration{" "}
                {response.audio_duration_sec != null
                  ? `${response.audio_duration_sec.toFixed(1)}s`
                  : "—"}
                {!response.reference && " · WER needs a reference"}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="field w-auto"
                value={saveDatasetId}
                onChange={(e) => setSaveDatasetId(e.target.value)}
              >
                <option value="">New dataset…</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.sample_count})
                  </option>
                ))}
              </select>
              <select
                className="field w-auto"
                value={saveSplit}
                onChange={(e) => setSaveSplit(e.target.value as "train" | "val")}
              >
                <option value="train">train</option>
                <option value="val">val</option>
              </select>
              <button type="button" className="btn-ghost" onClick={() => void saveToDataset()}>
                Save sample
              </button>
            </div>
          </div>
          {saveMsg && <p className="mb-3 font-sans text-xs text-tide">{saveMsg}</p>}

          <div className="overflow-x-auto border-y border-mist/15">
            <table className="w-full min-w-[720px] border-collapse text-left">
              <thead>
                <tr className="font-sans text-xs uppercase tracking-[0.12em] text-mist">
                  <th className="py-3 pr-4 font-medium">Model</th>
                  <th className="py-3 pr-4 font-medium">Latency</th>
                  <th className="py-3 pr-4 font-medium">WER</th>
                  <th className="py-3 pr-4 font-medium">CER</th>
                  <th className="py-3 font-medium">Transcript</th>
                </tr>
              </thead>
              <tbody>
                {response.results.map((r, idx) => {
                  const open = expanded === r.model_id;
                  return (
                    <tr
                      key={r.model_id}
                      className="animate-rise border-t border-mist/10 align-top"
                      style={{ animationDelay: `${idx * 60}ms` }}
                    >
                      <td className="py-3 pr-4">
                        <button
                          type="button"
                          className="text-left"
                          onClick={() =>
                            setExpanded(open ? null : r.model_id)
                          }
                        >
                          <span className="block font-sans text-sm text-foam">
                            {r.model_name}
                          </span>
                          <span className="block font-sans text-xs text-mist">
                            {r.provider}
                          </span>
                        </button>
                      </td>
                      <td className="py-3 pr-4 font-sans text-sm tabular-nums text-foam/90">
                        {r.error ? "—" : fmtMs(r.latency_ms)}
                        {r.rtf != null && (
                          <span className="block text-xs text-mist">
                            RTF {r.rtf.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-4 font-sans text-sm tabular-nums">
                        {response.reference
                          ? fmtMetric(r.wer)
                          : "needs ref"}
                      </td>
                      <td className="py-3 pr-4 font-sans text-sm tabular-nums">
                        {response.reference
                          ? fmtMetric(r.cer)
                          : "needs ref"}
                      </td>
                      <td className="py-3 font-sans text-sm text-foam/90">
                        {r.error ? (
                          <span className="text-ember">{r.error}</span>
                        ) : (
                          <>
                            <p className="line-clamp-2">{r.transcript || "—"}</p>
                            {open && (
                              <div className="mt-3 space-y-2 border-l-2 border-tide/40 pl-3">
                                <p className="text-xs uppercase tracking-[0.12em] text-mist">
                                  Word diff
                                </p>
                                <DiffView ops={r.diff_ops} />
                              </div>
                            )}
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
