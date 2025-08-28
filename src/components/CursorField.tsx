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
      for(let i