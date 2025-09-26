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
          x: nx, y: ny,
          vx: (Math.random() - 0.5) * 8,
          vy: (Math.random() - 0.5) * 8,
          life: 1.0
        });
      }
    }

    function draw() {
      const now = performance.now();
      const dt = Math.min(0.032, (now - last) / 1000);
      last = now;

      // Clear canvas
      ctx.clearRect(0, 0, w / devicePixelRatio, h / devicePixelRatio);

      // Update and draw orbs
      for (let i = orbs.length - 1; i >= 0; i--) {
        const orb = orbs[i];
        orb.x += orb.vx * dt * 60;
        orb.y += orb.vy * dt * 60;
        orb.life -= dt * settings.trail * 60;
        
        // Apply gravity toward center
        const cx = w / devicePixelRatio / 2;
        const cy = h / devicePixelRatio / 2;
        const dx = cx - orb.x;
        const dy = cy - orb.y;
        const dist = Math.hypot(dx, dy);
        if (dist > 0) {
          orb.vx += dx / dist * settings.gravity * dt * 60;
          orb.vy += dy / dist * settings.gravity * dt * 60;
        }

        if (orb.life <= 0) {
          orbs.splice(i, 1);
          continue;
        }

        // Draw orb
        ctx.save();
        ctx.globalAlpha = orb.life;
        ctx.fillStyle = settings.orbColor;
        ctx.beginPath();
        ctx.arc(orb.x, orb.y, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      requestAnimationFrame(draw);
    }

    addEventListener("pointermove", onMove);
    addEventListener("resize", () => {
      w = c.width = innerWidth * devicePixelRatio;
      h = c.height = innerHeight * devicePixelRatio;
      ctx.scale(devicePixelRatio, devicePixelRatio);
    });

    draw();

    return () => {
      removeEventListener("pointermove", onMove);
    };
  }, [settings]);

  return <canvas ref={ref} style={{ position: "fixed", inset: 0, pointerEvents: "none" }} />;
}