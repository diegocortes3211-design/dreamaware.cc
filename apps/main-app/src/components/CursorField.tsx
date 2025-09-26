import { useEffect, useRef } from "react";
import { useSettings } from "../state";

type Orb = { x: number; y: number; vx: number; vy: number; life: number };

export default function CursorField() {
  const ref = useRef<HTMLCanvasElement | null>(null);
  const { settings } = useSettings();
  const mouse = useRef({
    x: innerWidth / 2,
    y: innerHeight / 2,
    vx: 0,
    vy: 0,
    speed: 0,
  });

  useEffect(() => {
    const c = ref.current!;
    const ctx = c.getContext("2d")!;
    let w = (c.width = innerWidth * devicePixelRatio);
    let h = (c.height = innerHeight * devicePixelRatio);
    ctx.scale(devicePixelRatio, devicePixelRatio);

    const orbs: Orb[] = [];
    let last = performance.now();

    function onMove(e: PointerEvent) {
      const nx = e.clientX,
        ny = e.clientY;
      const dx = nx - mouse.current.x,
        dy = ny - mouse.current.y;
      mouse.current.vx = dx;
      mouse.current.vy = dy;
      mouse.current.x = nx;
      mouse.current.y = ny;
      mouse.current.speed = Math.hypot(dx, dy);
      // spawn bursts based on speed
      const count = Math.min(
        settings.spawn,
        Math.floor(mouse.current.speed / 6)
      );
      for (let i = 0; i < count; i++) {
        orbs.push({
          x: nx + (Math.random() - 0.5) * 20,
          y: ny + (Math.random() - 0.5) * 20,
          vx: (Math.random() - 0.5) * settings.speed * 2,
          vy: (Math.random() - 0.5) * settings.speed * 2,
          life: 1.0,
        });
      }
    }

    function onResize() {
      w = c.width = innerWidth * devicePixelRatio;
      h = c.height = innerHeight * devicePixelRatio;
      ctx.scale(devicePixelRatio, devicePixelRatio);
      mouse.current.x = innerWidth / 2;
      mouse.current.y = innerHeight / 2;
    }

    function frame(now: number) {
      const dt = Math.min(now - last, 32) / 1000; // cap at ~30fps
      last = now;

      // clear with trail effect
      ctx.fillStyle = `hsla(${settings.bgHue}, 40%, 8%, ${settings.trail})`;
      ctx.fillRect(0, 0, innerWidth, innerHeight);

      // update and draw orbs
      for (let i = orbs.length - 1; i >= 0; i--) {
        const orb = orbs[i];

        // gravity toward center
        const centerX = innerWidth / 2;
        const centerY = innerHeight / 2;
        const dx = centerX - orb.x;
        const dy = centerY - orb.y;
        orb.vx += dx * settings.gravity * dt;
        orb.vy += dy * settings.gravity * dt;

        // update position
        orb.x += orb.vx * settings.speed * 60 * dt;
        orb.y += orb.vy * settings.speed * 60 * dt;
        orb.life -= dt * 0.5;

        // remove dead orbs
        if (orb.life <= 0) {
          orbs.splice(i, 1);
          continue;
        }

        // draw orb
        const alpha = orb.life;
        ctx.fillStyle = settings.orbColor
          .replace(")", `, ${alpha})`)
          .replace("#", "rgba(")
          .replace(/(..)(..)(..)/, "$1,$2,$3,");
        ctx.beginPath();
        ctx.arc(orb.x, orb.y, 2, 0, Math.PI * 2);
        ctx.fill();
      }

      requestAnimationFrame(frame);
    }

    addEventListener("pointermove", onMove);
    addEventListener("resize", onResize);
    requestAnimationFrame(frame);

    return () => {
      removeEventListener("pointermove", onMove);
      removeEventListener("resize", onResize);
    };
  }, [settings]);

  return (
    <canvas
      ref={ref}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: -1,
        pointerEvents: "none",
      }}
    />
  );
}
