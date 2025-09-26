import { createContext, useContext, useMemo, useState } from "react";

export type PresetKey = "lsd" | "mdma" | "ket";

export type Settings = {
  preset: PresetKey;
  orbColor: string;
  bgHue: number; // 0..360
  spawn: number; // orbs per tick at high speed
  speed: number; // orb velocity
  trail: number; // fade factor
  gravity: number; // pull toward center
  audioReactive: boolean; // reserved
};

const defaults: Settings = {
  preset: "mdma",
  orbColor: "#c0ffee",
  bgHue: 270,
  spawn: 6,
  speed: 1.2,
  trail: 0.08,
  gravity: 0.03,
  audioReactive: false,
};

const Ctx = createContext<{
  settings: Settings;
  set: (patch: Partial<Settings>) => void;
}>({ settings: defaults, set: () => {} });

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<Settings>(() => {
    const saved = localStorage.getItem("dreamaware.settings");
    return saved ? { ...defaults, ...JSON.parse(saved) } : defaults;
  });
  const api = useMemo(
    () => ({
      settings,
      set: (patch: Partial<Settings>) => {
        setSettings(s => {
          const next = { ...s, ...patch };
          localStorage.setItem("dreamaware.settings", JSON.stringify(next));
          return next;
        });
      },
    }),
    [settings]
  );
  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}
export const useSettings = () => useContext(Ctx);
