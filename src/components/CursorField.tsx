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
          x: mouse.current.x + (Math.random() - 0.5) * 20,
          y: mouse.current.y + (Math.random() - 0.5) * 20,
          vx: mouse.current.vx * 0.1 + (Math.random() - 0.5) * 2,
          vy: mouse.current.vy * 0.1 + (Math.random() - 0.5) * 2,
          life: 1.0
        });
      }
    }

    function draw(ts: number) {
      const dt = Math.min(0.032, (ts - last) / 1000);
      last = ts;

      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = `rgba(0,0,0,${settings.trail})`;
      ctx.fillRect(0, 0, w / devicePixelRatio, h / devicePixelRatio);

      ctx.globalCompositeOperation = 'screen';
      for (let i = orbs.length - 1; i >= 0; i--) {
        const o = orbs[i];
        o.x += o.vx * dt * 60;
        o.y += o.vy * dt * 60;
        o.vx *= Math.pow(0.95, dt * 60);
        o.vy *= Math.pow(0.95, dt * 60);
        o.life -= dt * 2;

        if (o.life <= 0) {
          orbs.splice(i, 1);
          continue;
        }

        const size = o.life * 8;
        ctx.shadowBlur = settings.glow;
        ctx.shadowColor = '#4cc9f0';
        ctx.fillStyle = `rgba(76,201,240,${o.life * 0.8})`;
        ctx.beginPath();
        ctx.arc(o.x, o.y, size, 0, Math.PI * 2);
        ctx.fill();
      }

      requestAnimationFrame(draw);
    }

    document.addEventListener('pointermove', onMove);
    requestAnimationFrame(draw);

    return () => {
      document.removeEventListener('pointermove', onMove);
    };
  }, [settings]);

  return <canvas ref={ref} style={{ position: 'fixed', top: 0, left: 0, pointerEvents: 'none', zIndex: 1 }} />;
}