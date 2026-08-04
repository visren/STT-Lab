"use client";

import { useEffect, useState } from "react";
import { fetchSettings, updateSettings } from "@/lib/api";
import type { ModelInfo } from "@/lib/types";

export default function SettingsPage() {
  const [openai, setOpenai] = useState("");
  const [deepgram, setDeepgram] = useState("");
  const [assemblyai, setAssemblyai] = useState("");
  const [device, setDevice] = useState("auto");
  const [keys, setKeys] = useState({ openai: false, deepgram: false, assemblyai: false });
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const s = await fetchSettings();
    setDevice(s.whisper_device || "auto");
    setKeys(s.keys);
    setModels(s.models);
  }

  useEffect(() => {
    void load().catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  async function onSave() {
    setMsg(null);
    setError(null);
    try {
      const body: Record<string, string> = { whisper_device: device };
      if (openai.trim()) body.openai_api_key = openai.trim();
      if (deepgram.trim()) body.deepgram_api_key = deepgram.trim();
      if (assemblyai.trim()) body.assemblyai_api_key = assemblyai.trim();
      await updateSettings(body);
      setOpenai("");
      setDeepgram("");
      setAssemblyai("");
      await load();
      setMsg("Saved locally to data/local_keys.json");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-6 pb-20 pt-6">
      <section className="animate-rise">
        <h1 className="font-display text-3xl text-foam md:text-4xl">Settings</h1>
        <p className="mt-2 max-w-xl font-sans text-sm text-mist">
          Cloud keys stay on this machine. Local Whisper downloads on first use.
        </p>
      </section>

      {error && <p className="mt-4 font-sans text-sm text-ember">{error}</p>}
      {msg && <p className="mt-4 font-sans text-sm text-tide">{msg}</p>}

      <div className="mt-8 grid gap-10 lg:grid-cols-2">
        <section className="animate-rise space-y-4">
          <label className="block space-y-1">
            <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
              OpenAI API key {keys.openai ? "(set)" : "(missing)"}
            </span>
            <input
              className="field"
              type="password"
              autoComplete="off"
              placeholder={keys.openai ? "•••••••• (leave blank to keep)" : "sk-…"}
              value={openai}
              onChange={(e) => setOpenai(e.target.value)}
            />
          </label>
          <label className="block space-y-1">
            <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
              Deepgram API key {keys.deepgram ? "(set)" : "(missing)"}
            </span>
            <input
              className="field"
              type="password"
              autoComplete="off"
              placeholder={keys.deepgram ? "•••••••• (leave blank to keep)" : ""}
              value={deepgram}
              onChange={(e) => setDeepgram(e.target.value)}
            />
          </label>
          <label className="block space-y-1">
            <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
              AssemblyAI API key {keys.assemblyai ? "(set)" : "(missing)"}
            </span>
            <input
              className="field"
              type="password"
              autoComplete="off"
              placeholder={keys.assemblyai ? "•••••••• (leave blank to keep)" : ""}
              value={assemblyai}
              onChange={(e) => setAssemblyai(e.target.value)}
            />
          </label>
          <label className="block space-y-1">
            <span className="font-sans text-xs uppercase tracking-[0.14em] text-mist">
              Whisper device
            </span>
            <select
              className="field"
              value={device}
              onChange={(e) => setDevice(e.target.value)}
            >
              <option value="auto">auto</option>
              <option value="cpu">cpu</option>
              <option value="cuda">cuda</option>
            </select>
          </label>
          <button type="button" className="btn-primary" onClick={() => void onSave()}>
            Save settings
          </button>
          <p className="font-sans text-xs text-mist">
            You can also set keys in the repo-root <code className="text-foam/80">.env</code> file.
          </p>
        </section>

        <section className="animate-rise">
          <h2 className="font-display text-2xl text-foam">Model readiness</h2>
          <ul className="mt-4 divide-y divide-mist/10 border-y border-mist/15">
            {models.map((m) => (
              <li
                key={m.id}
                className="flex items-start justify-between gap-4 py-3 font-sans text-sm"
              >
                <span>
                  <span className="block text-foam">{m.name}</span>
                  <span className="block text-xs text-mist">{m.provider}</span>
                </span>
                <span
                  className={`shrink-0 text-xs ${
                    m.ready ? "text-tide" : "text-ember"
                  }`}
                >
                  {m.ready ? "ready" : m.reason || "not ready"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
