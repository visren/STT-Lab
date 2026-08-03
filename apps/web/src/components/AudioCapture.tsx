"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  file: File | null;
  onFile: (file: File | null) => void;
};

export function AudioCapture({ file, onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const startRecording = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const recorded = new File([blob], `recording-${Date.now()}.webm`, {
          type: "audio/webm",
        });
        onFile(recorded);
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Microphone access failed");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setRecording(false);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="rounded-md border border-[var(--line)] px-4 py-2 text-sm hover:border-[var(--accent-2)]"
        >
          Upload audio
        </button>
        {!recording ? (
          <button
            type="button"
            onClick={startRecording}
            className="rounded-md bg-[var(--accent-2)] px-4 py-2 text-sm font-medium text-[var(--ink)]"
          >
            Record
          </button>
        ) : (
          <button
            type="button"
            onClick={stopRecording}
            className="rounded-md bg-[var(--danger)] px-4 py-2 text-sm font-medium text-white"
          >
            Stop
          </button>
        )}
        {file && (
          <button
            type="button"
            onClick={() => onFile(null)}
            className="rounded-md px-3 py-2 text-sm text-[var(--muted)] hover:text-[var(--text)]"
          >
            Clear
          </button>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*,.wav,.mp3,.m4a,.webm,.ogg,.flac"
        className="hidden"
        onChange={(e) => onFile(e.target.files?.[0] || null)}
      />
      {recording && (
        <div className="flex h-8 items-end gap-1">
          {Array.from({ length: 12 }).map((_, i) => (
            <span
              key={i}
              className="eq-bar w-1.5 rounded-sm bg-[var(--accent)]"
              style={{
                height: `${10 + ((i * 17) % 22)}px`,
                animationDelay: `${i * 0.07}s`,
              }}
            />
          ))}
          <span className="ml-2 text-sm text-[var(--accent)]">Listening…</span>
        </div>
      )}
      {file && (
        <div className="text-sm text-[var(--muted)]">
          <span className="text-[var(--text)]">{file.name}</span>
          {" · "}
          {(file.size / 1024).toFixed(1)} KB
        </div>
      )}
      {previewUrl && <audio controls src={previewUrl} className="w-full max-w-md" />}
      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
    </div>
  );
}
