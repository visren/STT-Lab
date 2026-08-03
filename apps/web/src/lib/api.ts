import type {
  DatasetOut,
  EvaluateResponse,
  FinetuneJobOut,
  ModelInfo,
  SettingsOut,
  TranscribeResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ ok: boolean }>("/api/health"),
  models: () => request<ModelInfo[]>("/api/models"),
  settings: () => request<SettingsOut>("/api/settings"),
  updateSettings: (body: Record<string, string | null | undefined>) =>
    request<SettingsOut>("/api/settings", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  transcribe: async (opts: {
    file: Blob;
    filename: string;
    modelIds: string[];
    reference?: string;
    language?: string;
  }) => {
    const fd = new FormData();
    fd.append("audio", opts.file, opts.filename);
    fd.append("model_ids", JSON.stringify(opts.modelIds));
    if (opts.reference) fd.append("reference", opts.reference);
    if (opts.language) fd.append("language", opts.language);
    return request<TranscribeResponse>("/api/transcribe", { method: "POST", body: fd });
  },

  listDatasets: () => request<DatasetOut[]>("/api/datasets"),
  getDataset: (id: string) => request<DatasetOut>(`/api/datasets/${id}`),
  createDataset: (name: string, description = "") =>
    request<DatasetOut>("/api/datasets", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  updateDataset: (id: string, body: { name?: string; description?: string }) =>
    request<DatasetOut>(`/api/datasets/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteDataset: (id: string) =>
    request<{ ok: boolean }>(`/api/datasets/${id}`, { method: "DELETE" }),

  addSample: async (
    datasetId: string,
    opts: {
      file?: Blob;
      filename?: string;
      audioPath?: string;
      transcript?: string;
      split?: "train" | "val";
    }
  ) => {
    const fd = new FormData();
    if (opts.file) fd.append("audio", opts.file, opts.filename || "clip.wav");
    if (opts.audioPath) fd.append("audio_path", opts.audioPath);
    fd.append("transcript", opts.transcript || "");
    fd.append("split", opts.split || "train");
    return request(`/api/datasets/${datasetId}/samples`, { method: "POST", body: fd });
  },
  updateSample: (
    datasetId: string,
    sampleId: string,
    body: { transcript?: string; split?: "train" | "val" }
  ) =>
    request(`/api/datasets/${datasetId}/samples/${sampleId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteSample: (datasetId: string, sampleId: string) =>
    request<{ ok: boolean }>(`/api/datasets/${datasetId}/samples/${sampleId}`, {
      method: "DELETE",
    }),

  listFinetuneJobs: () => request<FinetuneJobOut[]>("/api/finetune"),
  getFinetuneJob: (id: string) => request<FinetuneJobOut>(`/api/finetune/${id}`),
  startFinetune: (body: {
    dataset_id: string;
    base_model: string;
    lora_rank?: number;
    lora_alpha?: number;
    learning_rate?: number;
    epochs?: number;
    batch_size?: number;
    language?: string;
  }) =>
    request<FinetuneJobOut>("/api/finetune", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  cancelFinetune: (id: string) =>
    request<FinetuneJobOut>(`/api/finetune/${id}/cancel`, { method: "POST" }),

  evaluate: (body: {
    dataset_id: string;
    base_model: string;
    adapter_id?: string | null;
    split?: "train" | "val";
  }) =>
    request<EvaluateResponse>("/api/evaluate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
