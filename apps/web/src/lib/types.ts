export type ModelProvider =
  | "local"
  | "openai"
  | "deepgram"
  | "assemblyai"
  | "adapted";

export interface ModelInfo {
  id: string;
  name: string;
  provider: ModelProvider;
  ready: boolean;
  reason?: string | null;
  size_hint?: string | null;
  base_model?: string | null;
  adapter_path?: string | null;
}

export interface DiffOp {
  op: "equal" | "insert" | "delete" | "replace";
  text: string;
}

export interface TranscriptResult {
  model_id: string;
  model_name: string;
  provider: string;
  transcript: string;
  latency_ms: number;
  audio_duration_sec?: number | null;
  rtf?: number | null;
  wer?: number | null;
  cer?: number | null;
  error?: string | null;
  words: string[];
  diff_ops: DiffOp[];
}

export interface TranscribeResponse {
  run_id: string;
  audio_path: string;
  audio_duration_sec?: number | null;
  reference?: string | null;
  results: TranscriptResult[];
}

export interface SampleOut {
  id: string;
  dataset_id: string;
  audio_path: string;
  transcript: string;
  split: "train" | "val" | string;
  duration_sec?: number | null;
  created_at: string;
}

export interface DatasetOut {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  sample_count: number;
  train_count: number;
  val_count: number;
  samples: SampleOut[];
}

export interface FinetuneJobOut {
  id: string;
  dataset_id: string;
  base_model: string;
  status: string;
  progress: number;
  logs: string;
  adapter_path?: string | null;
  error?: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  cancelled: boolean;
}

export interface EvaluateSampleResult {
  sample_id: string;
  reference: string;
  base_transcript: string;
  adapted_transcript?: string | null;
  base_wer?: number | null;
  adapted_wer?: number | null;
  base_cer?: number | null;
  adapted_cer?: number | null;
}

export interface EvaluateResponse {
  id: string;
  dataset_id: string;
  base_model: string;
  adapter_id?: string | null;
  split: string;
  sample_count: number;
  base_wer?: number | null;
  adapted_wer?: number | null;
  delta_wer?: number | null;
  base_cer?: number | null;
  adapted_cer?: number | null;
  delta_cer?: number | null;
  samples: EvaluateSampleResult[];
}

export interface SettingsOut {
  openai_configured: boolean;
  deepgram_configured: boolean;
  assemblyai_configured: boolean;
  whisper_device: string;
  data_dir: string;
}
