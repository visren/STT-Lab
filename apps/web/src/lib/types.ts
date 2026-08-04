export type ModelInfo = {
  id: string;
  name: string;
  provider: "local" | "openai" | "deepgram" | "assemblyai" | "adapted";
  ready: boolean;
  reason: string | null;
  size_hint?: string | null;
  base_model?: string | null;
  adapter_path?: string | null;
};

export type DiffOp = {
  op: "equal" | "insert" | "delete" | "replace";
  text: string;
};

export type TranscriptResult = {
  model_id: string;
  model_name: string;
  provider: string;
  transcript: string;
  latency_ms: number;
  audio_duration_sec: number | null;
  rtf: number | null;
  wer: number | null;
  cer: number | null;
  error: string | null;
  words: string[];
  diff_ops: DiffOp[];
};

export type TranscribeResponse = {
  run_id: string;
  audio_path: string;
  audio_duration_sec: number | null;
  reference: string | null;
  results: TranscriptResult[];
};

export type DatasetSummary = {
  id: string;
  name: string;
  description: string;
  sample_count: number;
  train_count: number;
  val_count: number;
  created_at: string | null;
  updated_at: string | null;
};

export type Sample = {
  id: string;
  audio_path: string;
  transcript: string;
  split: "train" | "val" | string;
  duration_sec: number | null;
  created_at: string | null;
};

export type DatasetDetail = {
  id: string;
  name: string;
  description: string;
  samples: Sample[];
  train_count: number;
  val_count: number;
};

export type FinetuneJob = {
  id: string;
  dataset_id: string;
  base_model: string;
  status: string;
  progress: number;
  error: string | null;
  adapter_path: string | null;
  config: Record<string, unknown>;
  warn_low_samples?: boolean;
  logs: string;
  created_at: string | null;
  updated_at: string | null;
};

export type EvaluateResponse = {
  id: string;
  dataset_id: string;
  base_model: string;
  adapter_id: string | null;
  split: string;
  sample_count: number;
  base_wer: number | null;
  adapted_wer: number | null;
  delta_wer: number | null;
  base_cer: number | null;
  adapted_cer: number | null;
  delta_cer: number | null;
  samples: Array<{
    sample_id: string;
    reference: string;
    base_transcript: string;
    adapted_transcript: string | null;
    base_wer: number | null;
    adapted_wer: number | null;
    base_cer: number | null;
    adapted_cer: number | null;
  }>;
};
