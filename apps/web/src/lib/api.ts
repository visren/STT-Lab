import type {
  DatasetDetail,
  DatasetSummary,
  EvaluateResponse,
  FinetuneJob,
  ModelInfo,
  TranscribeResponse,
} from "./types";

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data?.detail ?? data);
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch("/api/models", { cache: "no-store" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchSettings(): Promise<{
  whisper_device: string;
  keys: { openai: boolean; deepgram: boolean; assemblyai: boolean };
  models: ModelInfo[];
}> {
  const res = await fetch("/api/settings", { cache: "no-store" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function updateSettings(body: {
  openai_api_key?: string;
  deepgram_api_key?: string;
  assemblyai_api_key?: string;
  whisper_device?: string;
}): Promise<void> {
  const res = await fetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function transcribe(opts: {
  audio: Blob;
  filename: string;
  modelIds: string[];
  reference?: string;
  language?: string;
}): Promise<TranscribeResponse> {
  const form = new FormData();
  form.append("audio", opts.audio, opts.filename);
  form.append("model_ids", JSON.stringify(opts.modelIds));
  form.append("reference", opts.reference ?? "");
  form.append("language", opts.language ?? "");
  const res = await fetch("/api/transcribe", { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function listDatasets(): Promise<DatasetSummary[]> {
  const res = await fetch("/api/datasets", { cache: "no-store" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function createDataset(name: string, description = ""): Promise<{ id: string }> {
  const res = await fetch("/api/datasets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getDataset(id: string): Promise<DatasetDetail> {
  const res = await fetch(`/api/datasets/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function addSampleUpload(
  datasetId: string,
  audio: Blob,
  filename: string,
  transcript: string,
  split: "train" | "val",
): Promise<{ id: string }> {
  const form = new FormData();
  form.append("audio", audio, filename);
  form.append("transcript", transcript);
  form.append("split", split);
  const res = await fetch(`/api/datasets/${datasetId}/samples`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function addSampleFromPath(
  datasetId: string,
  audioPath: string,
  transcript: string,
  split: "train" | "val",
): Promise<{ id: string }> {
  const res = await fetch(`/api/datasets/${datasetId}/samples/from-path`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_path: audioPath, transcript, split }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function updateSample(
  datasetId: string,
  sampleId: string,
  body: { transcript?: string; split?: string },
): Promise<void> {
  const res = await fetch(`/api/datasets/${datasetId}/samples/${sampleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function deleteSample(datasetId: string, sampleId: string): Promise<void> {
  const res = await fetch(`/api/datasets/${datasetId}/samples/${sampleId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function listFinetuneJobs(): Promise<FinetuneJob[]> {
  const res = await fetch("/api/finetune", { cache: "no-store" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function startFinetune(body: {
  dataset_id: string;
  base_model: string;
  epochs: number;
  lora_rank: number;
  learning_rate: number;
  batch_size: number;
  language: string;
}): Promise<FinetuneJob> {
  const res = await fetch("/api/finetune", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getFinetuneJob(id: string): Promise<FinetuneJob> {
  const res = await fetch(`/api/finetune/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function cancelFinetune(id: string): Promise<FinetuneJob> {
  const res = await fetch(`/api/finetune/${id}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function evaluate(body: {
  dataset_id: string;
  base_model: string;
  adapter_id: string | null;
  split?: string;
}): Promise<EvaluateResponse> {
  const res = await fetch("/api/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ split: "val", ...body }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
