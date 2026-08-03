"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ModelInfo, SettingsOut } from "@/lib/types";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsOut | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [openai, setOpenai] = useState("");
  const [deepgram, setDeepgram] = useState("");
  const [assembly, setAssembly] = useState("");
  const [device, setDevice] = useState("auto");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const [s, m] = await Promise.all([api.settings(), api.models()]);
    setSettings(s);
    setModels(m);
    setDevice(s.whisper_device || "auto");
  };

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);

  const save = async () => {
    setMsg(null);
    setError(null);
    try {
      const body: Record<string, string> = { whisper_device: device };
      if (openai.trim()) body.openai_api_key = openai.trim();
      if (deepgram.trim()) body.deepgram_api_key = deepgram.trim();
      if (assembly.trim()) body.assemblyai_api_key = assembly.trim();
      await api.updateSettings(body);
      setOpenai("");
      setDeepgram("");
      setAssembly("");
      await refresh();
      setMsg("Settings saved locally to apps/api/.env");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    }
  };

  return (
    <div className="space-y-8">
      <section className="animate-rise">
        <h1 className="font-[family-name:var(--font-display)] text-4xl font-extrabold tracking-tight">
          Settings
        </h1>
        <p className="mt-2 max-w-2xl text-[var(--muted)]">
          Cloud keys stay on your machine. Local Whisper models download on first use.
        </p>
      </section>

      {error && (
        <p className="rounded-md border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">
          {error}
        </p>
      )}
      {msg && <p className="text-sm text-[var(--accent-2)]">{msg}</p>}

      <section className="animate-rise-delay-1 grid gap-6 lg:grid-cols-2">
        <div className="space-y-4 rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5">
          <div className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Cloud API keys
          </div>
          <KeyField
            label="OpenAI"
            configured={settings?.openai_configured}
            value={openai}
            onChange={setOpenai}
            placeholder="sk-..."
          />
          <KeyField
            label="Deepgram"
            configured={settings?.deepgram_configured}
            value={deepgram}
            onChange={setDeepgram}
            placeholder="dg-..."
          />
          <KeyField
            label="AssemblyAI"
            configured={settings?.assemblyai_configured}
            value={assembly}
            onChange={setAssembly}
            placeholder="..."
          />
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Whisper device</span>
            <select
              value={device}
              onChange={(e) => setDevice(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-3 py-2"
            >
              <option value="auto">auto</option>
              <option value="cpu">cpu</option>
              <option value="cuda">cuda</option>
            </select>
          </label>
          <button
            type="button"
            onClick={save}
            className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-[var(--ink)]"
          >
            Save settings
          </button>
          {settings && (
            <p className="text-xs text-[var(--muted)]">Data directory: {settings.data_dir}</p>
          )}
        </div>

        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5">
          <div className="mb-3 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            Model readiness
          </div>
          <ul className="space-y-2 text-sm">
            {models.map((m) => (
              <li
                key={m.id}
                className="flex items-start justify-between gap-3 border-b border-white/5 py-2"
              >
                <div>
                  <div className="font-medium">{m.name}</div>
                  <div className="text-xs text-[var(--muted)]">{m.provider}</div>
                  {!m.ready && m.reason && (
                    <div className="text-xs text-[var(--warn)]">{m.reason}</div>
                  )}
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    m.ready
                      ? "bg-[var(--ok)]/15 text-[var(--ok)]"
                      : "bg-[var(--warn)]/15 text-[var(--warn)]"
                  }`}
                >
                  {m.ready ? "ready" : "blocked"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}

function KeyField({
  label,
  configured,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  configured?: boolean;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <label className="block text-sm">
      <span className="flex items-center justify-between text-[var(--muted)]">
        {label}
        <span className={configured ? "text-[var(--ok)]" : "text-[var(--warn)]"}>
          {configured ? "configured" : "missing"}
        </span>
      </span>
      <input
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={configured ? "•••••••• (leave blank to keep)" : placeholder}
        className="mt-1 w-full rounded-md border border-[var(--line)] bg-black/20 px-3 py-2 outline-none focus:ring-1 focus:ring-[var(--accent-2)]"
      />
    </label>
  );
}
