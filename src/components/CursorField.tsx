import { useEffect, useRef } from "react";
import { useSettings } from "../state";

type Orb = { x:number; y:number; vx:number; vy:number; life:number };

export default function CursorField() {
  const ref = useRef<HTMLCanvasElement | null>(null);
  const { settings } = useSettings();
  const mouse = useRef({ x: innerWidth/2, y: innerHeight/2, vx:0, vy:0, speed:0 });

  useEffect(() => {
    const c = ref.current!;
    const ctx = c.getContext("2d")!;
    let w = (c.width = innerWidth * devicePixelRatio);
    let h = (c.height = innerHeight * devicePixelRatio);
    ctx.scale(devicePixelRatio, devicePixelRatio);

    const orbs: Orb[] = [];
    let last = performance.now();

    function onMove(e: PointerEvent){
      const nx = e.clientX, ny = e.clientY;
      const dx = nx - mouse.current.x, dy = ny - mouse.current.y;
      mouse.current.vx = dx; mouse.current.vy = dy;
      mouse.current.x = nx; mouse.current.y = ny;
      mouse.current.speed = Math.hypot(dx, dy);
      // spawn bursts based on speed
      const count = Math.min(settings.spawn, Math.floor(mouse.current.speed/6));
      for(let i = 0; i < count; i++) {
        orbs.push({
          x: nx, y: ny,
          vx: (Math.random()-0.5)*8, vy: (Math.random()-0.5)*8,
          life: 1.0
        });
      }
    }

    function draw(ts: number) {
      const dt = Math.min(0.016, (ts - last) / 1000);
      last = ts;
      
      ctx.fillStyle = `hsl(${settings.bgHue}, 20%, 8%)`;
      ctx.fillRect(0, 0, innerWidth, innerHeight);
      
      // Update and draw orbs
      for(let i = orbs.length - 1; i >= 0; i--) {
        const o = orbs[i];
        o.x += o.vx * dt * 60;
        o.y += o.vy * dt * 60;
        o.life -= dt * settings.speed;
        
        if(o.life <= 0) {
          orbs.splice(i, 1);
          continue;
        }
        
        ctx.globalAlpha = o.life;
        ctx.fillStyle = `hsl(${settings.bgHue + 60}, 80%, 60%)`;
        ctx.fillRect(o.x - 2, o.y - 2, 4, 4);
      }
      
      ctx.globalAlpha = 1;
      requestAnimationFrame(draw);
    }

    addEventListener("pointermove", onMove);
    requestAnimationFrame(draw);
    
    return () => {
      removeEventListener("pointermove", onMove);
    };
  }, [settings]);

  return <canvas ref={ref} style={{position: "fixed", inset: 0, pointerEvents: "none", zIndex: 1}} />;
}