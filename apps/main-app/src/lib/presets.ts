import type { Settings } from "../state";

export const PRESETS: Record<string, Partial<Settings>> = {
  lsd: {
    preset: "lsd",
    orbColor: "#74f7ff",
    bgHue: 285,
    spawn: 7,
    speed: 1.4,
    trail: 0.05,
    gravity: 0.018,
  },
  mdma: {
    preset: "mdma",
    orbColor: "#ff79d3",
    bgHue: 315,
    spawn: 8,
    speed: 1.1,
    trail: 0.1,
    gravity: 0.012,
  },
  ket: {
    preset: "ket",
    orbColor: "#9fffb9",
    bgHue: 200,
    spawn: 5,
    speed: 0.8,
    trail: 0.06,
    gravity: 0.028,
  },
};
