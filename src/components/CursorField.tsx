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
          vx: (Math.random() - 0.5) * 10,
          vy: (Math.random() - 0.5) * 10,
          life: 1
        });
      }
    }

    function draw(now: number) {
      const dt = Math.min((now - last) / 1000, 1/60);
      last = now;
      
      ctx.clearRect(0, 0, w/devicePixelRatio, h/devicePixelRatio);
      ctx.fillStyle = '#ffffff';
      
      for(let i = orbs.length - 1; i >= 0; i--) {
        const orb = orbs[i];
        orb.x += orb.vx * dt * 60;
        orb.y += orb.vy * dt * 60;
        orb.life -= dt * 2;
        
        if(orb.life <= 0) {
          orbs.splice(i, 1);
          continue;
        }
        
        ctx.globalAlpha = orb.life;
        ctx.fillRect(orb.x - 1, orb.y - 1, 2, 2);
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

  return <canvas ref={ref} className="fixed inset-0 pointer-events-none z-10" />;
}