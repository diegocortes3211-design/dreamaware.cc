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
      for(let i = 0; i < count; i++){
        orbs.push({
          x: nx + (Math.random()-0.5)*20,
          y: ny + (Math.random()-0.5)*20,
          vx: (Math.random()-0.5)*4,
          vy: (Math.random()-0.5)*4,
          life: 1
        });
      }
    }

    function draw(ts: number) {
      const dt = Math.min(0.016, (ts - last) / 1000);
      last = ts;

      // Update orbs
      for (let i = orbs.length - 1; i >= 0; i--) {
        const o = orbs[i];
        o.x += o.vx * settings.speed;
        o.y += o.vy * settings.speed;
        o.life -= dt * settings.trail;
        
        // Apply gravity toward center
        const dx = w / 2 / devicePixelRatio - o.x;
        const dy = h / 2 / devicePixelRatio - o.y;
        o.vx += dx * settings.gravity * dt;
        o.vy += dy * settings.gravity * dt;

        if (o.life <= 0) {
          orbs.splice(i, 1);
        }
      }

      // Clear canvas
      ctx.fillStyle = `hsla(${settings.bgHue}, 50%, 5%, ${settings.trail})`;
      ctx.fillRect(0, 0, w / devicePixelRatio, h / devicePixelRatio);

      // Draw orbs
      for (const o of orbs) {
        const alpha = Math.max(0, o.life);
        ctx.fillStyle = `${settings.orbColor}${Math.floor(alpha * 255).toString(16).padStart(2, '0')}`;
        ctx.beginPath();
        ctx.arc(o.x, o.y, 2, 0, Math.PI * 2);
        ctx.fill();
      }

      requestAnimationFrame(draw);
    }

    window.addEventListener("pointermove", onMove);
    requestAnimationFrame(draw);

    return () => {
      window.removeEventListener("pointermove", onMove);
    };
  }, [settings]);

  return <canvas ref={ref} style={{ position: 'fixed', inset: 0, zIndex: 1 }} />;
}