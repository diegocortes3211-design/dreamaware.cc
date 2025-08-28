// src/FlowApp.tsx
import React, {useEffect, useMemo, useRef, useState} from "react";

type Hex = `#${string}`;

const PRESETS: Record<string, Hex[]> = {
  astro: ["#0b0e13","#90e0ef","#ffe066"],
  laflame: ["#ff0040","#ff7f11","#ffd166"],
  utopia: ["#111827","#7f5af0","#22d3ee"],
  jazz: ["#2b3246","#fca311","#a7f3d0"],
  ocean: ["#03045e","#00b4d8","#90e0fe"],
  candy: ["#f72585","#7209b7","#4cc9f0"],
};

function clamp(v:number,min:number,max:number){ return v<min?min:v>max?max:v; }
function lerp(a:number,b:number,t:number){ return a+(b-a)*t; }

function hexToRgb(h:Hex){ const x=h.replace("#",""); return {
  r: parseInt(x.slice(0,2),16),
  g: parseInt(x.slice(2,4),16),
  b: parseInt(x.slice(4,6),16)
};}
function rgbToStr(r:number,g:number,b:number,a=1){ return `rgba(${r|0},${g|0},${b|0},${a})`; }
function mixHex(a:Hex,b:Hex,t:number): string{
  const A=hexToRgb(a), B=hexToRgb(b);
  return rgbToStr(lerp(A.r,B.r,t), lerp(A.g,B.g,t), lerp(A.b,B.b,t));
}

type Orb = {
  x:number; y:number;
  vx:number; vy:number;
  hue:number; life:number; max:number;
  size:number; tintA:Hex; tintB:Hex;
};

export default function FlowApp(){
  // visual state
  const [preset,setPreset] = useState<keyof typeof PRESETS>("candy");
  const [custom,setCustom] = useState<string>("");
  const palette = useMemo<Hex[]>(()=>{
    const raw = custom.trim();
    if(raw){
      const toks = raw.split(/[,\s]+/).filter(Boolean) as Hex[];
      return toks.slice(0,8);
    }
    return PRESETS[preset];
  },[preset,custom]);

  const [orbCount,setOrbCount] = useState(240);
  const [speed,setSpeed] = useState(1.0);
  const [trail,setTrail] = useState(0.08);  // alpha clear
  const [glow,setGlow] = useState(8);       // shadow blur
  const [bounce,setBounce] = useState(true);
  const [centerPull,setCenterPull] = useState(0.06);
  const [cursorPull,setCursorPull] = useState(0.20);

  // canvas refs
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D|null>(null);

  // field
  const orbsRef = useRef<Orb[]>([]);
  const cursorRef = useRef({x:0,y:0,vx:0,vy:0,speed:0});
  const timeRef = useRef(0);
  const rafRef = useRef(0);
  const resizedRef = useRef(false);

  useEffect(()=>{
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    ctxRef.current = ctx;

    function fit(){
      const dpr = clamp(window.devicePixelRatio || 1, 1, 2);
      const w = window.innerWidth;
      const h = window.innerHeight;
      canvas.width = (w*dpr)|0;
      canvas.height = (h*dpr)|0;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr,0,0,dpr,0,0);
      resizedRef.current = true;
    }
    fit();
    window.addEventListener("resize", fit);

    // init orbs
    const seedOrbs: Orb[] = [];
    function pick<T>(arr:T[]){ return arr[(Math.random()*arr.length)|0]; }
    for(let i=0;i<orbCount;i++){
      const tA = pick(palette), tB = pick(palette);
      seedOrbs.push({
        x: Math.random()*window.innerWidth,
        y: Math.random()*window.innerHeight,
        vx: (Math.random()*2-1)*1.5,
        vy: (Math.random()*2-1)*1.5,
        hue: Math.random(),
        life: Math.random()*1,
        max: 3 + Math.random()*6,
        size: 2 + Math.random()*3,
        tintA: tA, tintB: tB
      });
    }
    orbsRef.current = seedOrbs;

    // cursor move
    let lastT = performance.now();
    let lastX = window.innerWidth*0.5;
    let lastY = window.innerHeight*0.5;
    cursorRef.current.x = lastX;
    cursorRef.current.y = lastY;

    function onMove(e:MouseEvent){
      const now = performance.now();
      const dt = (now - lastT) || 16;
      const x = e.clientX;
      const y = e.clientY;
      const vx = (x - lastX) / dt;
      const vy = (y - lastY) / dt;
      const sp = Math.hypot(vx,vy);
      cursorRef.current = {x,y,vx,vy,speed: sp};
      lastT = now; lastX = x; lastY = y;
    }
    window.addEventListener("mousemove", onMove);

    function tick(t:number){
      rafRef.current = requestAnimationFrame(tick);
      const ctx = ctxRef.current!;
      const W = window.innerWidth, H = window.innerHeight;

      // trail clear
      ctx.fillStyle = `rgba(0,0,0,${trail})`;
      ctx.fillRect(0,0,W,H);

      const cx = W*0.5, cy = H*0.5;
      const cur = cursorRef.current;
      const speedBoost = 1 + clamp(cur.speed*40, 0, 3);

      // soft field
      timeRef.current += 0.005;

      // spawn or trim to target count (gentle drift)
      const arr = orbsRef.current;
      while(arr.length < orbCount){
        const tA = palette[(Math.random()*palette.length)|0] as Hex;
        const tB = palette[(Math.random()*palette.length)|0] as Hex;
        arr.push({
          x: Math.random()*W, y: Math.random()*H,
          vx: (Math.random()*2-1)*1.5, vy: (Math.random()*2-1)*1.5,
          hue: Math.random(), life: 0, max: 3 + Math.random()*6,
          size: 2 + Math.random()*3, tintA: tA, tintB: tB
        });
      }
      if(arr.length > orbCount){
        arr.splice(orbCount);
      }

      // draw
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.shadowColor = "rgba(255,255,255,0.25)";
      ctx.shadowBlur = glow;

      for(const o of arr){
        // forces
        const toCenterX = cx - o.x;
        const toCenterY = cy - o.y;
        o.vx += toCenterX * centerPull * 0.001;
        o.vy += toCenterY * centerPull * 0.001;

        const toCursorX = cur.x - o.x;
        const toCursorY = cur.y - o.y;
        o.vx += toCursorX * cursorPull * 0.001 * speedBoost * speed;
        o.vy += toCursorY * cursorPull * 0.001 * speedBoost * speed;

        // integrate
        o.x += o.vx * speed;
        o.y += o.vy * speed;

        // bounds
        if(bounce){
          if(o.x < 0){ o.x=0; o.vx*=-0.8; }
          if(o.x > W){ o.x=W; o.vx*=-0.8; }
          if(o.y < 0){ o.y=0; o.vy*=-0.8; }
          if(o.y > H){ o.y=H; o.vy*=-0.8; }
        }else{
          if(o.x < 0) o.x += W;
          if(o.x > W) o.x -= W;
          if(o.y < 0) o.y += H;
          if(o.y > H) o.y -= H;
        }

        // style
        o.hue = (o.hue + 0.003) % 1;
        o.life += 0.01;
        const t = (Math.sin(o.life) * 0.5 + 0.5);
        const col = mixHex(o.tintA, o.tintB, t) as string;

        ctx.beginPath();
        ctx.fillStyle = col;
        ctx.arc(o.x, o.y, o.size, 0, Math.PI*2);
        ctx.fill();

        // ring
        ctx.strokeStyle = rgbToStr(255,255,255,0.04);
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      ctx.restore();

      resizedRef.current = false;
    }
    rafRef.current = requestAnimationFrame(tick);

    return ()=>{
      window.removeEventListener("resize", fit);
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(rafRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  // when main knobs change, we simply let the loop react
  useEffect(()=>{
    // palette change nudges orb tints
    const arr = orbsRef.current;
    if(!arr.length || !palette.length) return;
    for(const o of arr){
      o.tintA = palette[(Math.random()*palette.length)|0] as Hex;
      o.tintB = palette[(Math.random()*palette.length)|0] as Hex;
    }
  },[palette]);

  // ui
  return (
    <div ref={wrapRef} style={S.wrap}>
      <canvas ref={canvasRef} style={S.canvas} />

      <div style={S.panel}>
        <div style={S.title}>dreamaware</div>

        <div style={S.row}>
          <label style={S.lab}>preset</label>
          <select value={preset} onChange={e=>{ setPreset(e.target.value as any); setCustom(""); }} style={S.sel}>
            {Object.keys(PRESETS).map(k=>(<option key={k} value={k}>{k}</option>))}
          </select>
        </div>

        <div style={S.row}>
          <label style={S.lab}>custom</label>
          <input
            placeholder="#ff0040 #ff7f11 #ffd166"
            value={custom}
            onChange={e=>setCustom(e.target.value)}
            style={S.input}
          />
        </div>

        <Knob label="orbs" v={orbCount} set={setOrbCount} min={40} max={800} />
        <Knob label="speed" v={speed} set={setSpeed} min={0.2} max={3} step={0.01}/>
        <Knob label="trail" v={trail} set={setTrail} min={0.02} max={0.2} step={0.005}/>
        <Knob label="glow" v={glow} set={setGlow} min={0} max={24} />
        <Knob label="center" v={centerPull} set={setCenterPull} min={0} max={0.2} step={0.005}/>
        <Knob label="cursor" v={cursorPull} set={setCursorPull} min={0} max={0.6} step={0.01}/>

        <div style={S.row}>
          <label style={S.lab}>bounce</label>
          <input type="checkbox" checked={bounce} onChange={e=>setBounce(e.target.checked)} />
        </div>

        <div style={S.footer}>
          <span>☆</span>
          <span>◇</span>
          <span>♡</span>
        </div>
      </div>
    </div>
  );
}

function Knob(props:{
  label:string, v:number, set:(n:number)=>void,
  min:number, max:number, step?:number
}){
  const {label,v,set,min,max,step} = props;
  return (
    <div style={S.row}>
      <label style={S.lab}>{label}</label>
      <input
        type="range"
        min={min}
        max={max}
        step={step ?? 1}
        value={v}
        onChange={e=>set(parseFloat(e.target.value))}
        style={S.range}
      />
      <div style={S.val}>{(typeof v==="number" && v%1!==0)? v.toFixed(2): v}</div>
    </div>
  );
}

const S: Record<string, React.CSSProperties> = {
  wrap: {
    position:"fixed", left:0, top:0, right:0, bottom:0,
    background:"radial-gradient(1200px 800px at 50% 50%, rgba(16,16,32,0.8), rgba(0,0,0,1))",
    overflow:"hidden", userSelect:"none"
  },
  canvas: { position:"absolute", left:0, top:0, width:"100%", height:"100%" },
  panel: {
    position:"absolute", right:18, top:18, width:300,
    background:"rgba(18,18,28,0.66)",
    border:"1px solid rgba(255,255,255,0.08)",
    borderRadius:14, padding:14, boxShadow:"0 12px 40px rgba(0,0,0,0.45)",
    backdropFilter:"blur(8px)", color:"#e5e7eb", fontFamily:"ui-sans-serif, system-ui, Segoe UI, Roboto, Helvetica, Arial"
  },
  title: { fontSize:20, fontWeight:700, marginBottom:8, letterSpacing:1 },
  row: { display:"flex", alignItems:"center", gap:8, margin:"8px 0" },
  lab: { width:88, opacity:0.9 },
  sel: {
    flex:1, padding:"6px 8px", background:"rgba(255,255,255,0.06)",
    color:"#e5e7eb", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, outline:"none"
  },
  input: {
    flex:1, padding:"6px 8px", background:"rgba(255,255,255,0.06)",
    color:"#e5e7eb", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, outline:"none", fontFamily:"monospace"
  },
  range: { flex:1 },
  val: { width:64, textAlign:"right", opacity:0.9, fontVariantNumeric:"tabular-nums" },
  footer: { display:"flex", gap:12, justifyContent:"flex-end", marginTop:6, opacity:0.8 }
};