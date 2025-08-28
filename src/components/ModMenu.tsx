import { useSettings } from "../state";
import { PRESETS } from "../lib/presets";

export default function ModMenu() {
  const { settings, set } = useSettings();

  return (
    <div className="modmenu">
      <h3>dreamaware control</h3>

      <div className="row">
        <label>preset</label>
        <div style={{display:"flex",gap:8}}>
          {Object.keys(PRESETS).map(k => (
            <button key={k}
              className={"pill " + (settings.preset===k ? "active": "")}
              onClick={() => set(PRESETS[k])}>
              {k}
            </button>
          ))}
        </div>
      </div>

      <div className="row">
        <label>orb color</label>
        <input
          type="color"
          value={settings.orbColor}
          onChange={e => set({ orbColor: e.target.value })}
        />
        <div className="colorchip" style={{background:settings.orbColor}}/>
      </div>

      <div className="row">
        <label>bg hue</label>
        <input type="range" min={0} max={360} value={settings.bgHue}
               onChange={e => set({ bgHue: +e.target.value })}/>
        <span>{settings.bgHue}</span>
      </div>

      <div className="row">
        <label>spawn</label>
        <input type="range" min={1} max={20} value={settings.spawn}
               onChange={e => set({ spawn: +e.target.value })}/>
        <span>{settings.spawn}</span>
      </div>

      <div className="row">
        <label>speed</label>
        <input type="range" min={0.2} max={2.0} step={0.05} value={settings.speed}
               onChange={e => set({ speed: +e.target.value })}/>
        <span>{settings.speed.toFixed(2)}</span>
      </div>

      <div className="row">
        <label>trail</label>
        <input type="range" min={0.02} max={0.2} step={0.01} value={settings.trail}
               onChange={e => set({ trail: +e.target.value })}/>
        <span>{settings.trail.toFixed(2)}</span>
      </div>

      <div className="row">
        <label>gravity</label>
        <input type="range" min={0.0} max={0.06} step={0.002} value={settings.gravity}
               onChange={e => set({ gravity: +e.target.value })}/>
        <span>{settings.gravity.toFixed(3)}</span>
      </div>

      <div className="row" style={{justifyContent:"space-between"}}>
        <button className="pill" onClick={() => set({})}>save</button>
        <button className="pill" onClick={() => {
          localStorage.removeItem("dreamaware.settings");
          location.reload();
        }}>reset</button>
      </div>
    </div>
  );
}