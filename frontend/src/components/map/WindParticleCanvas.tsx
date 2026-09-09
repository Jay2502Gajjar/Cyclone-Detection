import { useEffect, useRef } from "react";

interface WindParticleCanvasProps {
  speed?: number;
  centerLat?: number;
  centerLon?: number;
}

export function WindParticleCanvas({ speed = 1 }: WindParticleCanvasProps) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: false });
    if (!ctx) return;
    let raf = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const width = () => canvas.offsetWidth;
    const height = () => canvas.offsetHeight;

    // Cambecc/earth style particle streamline pool
    const count = 550;
    const particles = Array.from({ length: count }).map(() => ({
      x: Math.random() * width(),
      y: Math.random() * height(),
      age: Math.random() * 90,
      maxAge: 60 + Math.random() * 60,
      speed: 0.8 + Math.random() * 0.6,
    }));

    // Semi-transparent fading canvas for persistent motion trails
    const trailCanvas = document.createElement("canvas");
    const trailCtx = trailCanvas.getContext("2d");

    const syncTrailSize = () => {
      trailCanvas.width = canvas.width;
      trailCanvas.height = canvas.height;
    };
    syncTrailSize();

    const tick = () => {
      const w = width();
      const h = height();
      const cx = w / 2;
      const cy = h / 2;

      // Draw faint semi-transparent overlay to create smooth decaying particle tails
      ctx.globalCompositeOperation = "destination-out";
      ctx.fillStyle = "rgba(0, 0, 0, 0.085)";
      ctx.fillRect(0, 0, w, h);
      ctx.globalCompositeOperation = "source-over";

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        const dx = p.x - cx;
        const dy = p.y - cy;
        const dist = Math.max(18, Math.hypot(dx, dy));

        // Cambecc Holland vortex vector field: tangential swirl + inward radial suction
        const tangentAngle = Math.atan2(dy, dx) + Math.PI / 2;
        // Inflow angle increases with distance (spira-inflow)
        const inflowAngle = 0.28 * Math.min(1.5, dist / (w * 0.25));
        const theta = tangentAngle + inflowAngle;

        // Rankine velocity profile: peaks near eyewall, diminishes outward
        const v = Math.min(3.8, (2.2 * speed * p.speed * 180) / Math.pow(dist, 0.82));
        const nx = p.x + Math.cos(theta) * v;
        const ny = p.y + Math.sin(theta) * v;

        // Calculate color based on wind speed intensity
        const lifeFraction = p.age / p.maxAge;
        const alpha = Math.sin(lifeFraction * Math.PI) * 0.75;

        // Cambecc/earth dynamic streamline colors: Cyan -> Cobalt -> Crisp White near eyewall
        if (dist < 80) {
          ctx.strokeStyle = `rgba(248, 250, 252, ${alpha.toFixed(2)})`;
          ctx.lineWidth = 1.4;
        } else if (dist < 180) {
          ctx.strokeStyle = `rgba(56, 189, 248, ${alpha.toFixed(2)})`;
          ctx.lineWidth = 1.1;
        } else {
          ctx.strokeStyle = `rgba(59, 130, 246, ${(alpha * 0.75).toFixed(2)})`;
          ctx.lineWidth = 0.85;
        }

        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(nx, ny);
        ctx.stroke();

        p.x = nx;
        p.y = ny;
        p.age += 1;

        // Reset dead or out-of-bounds particles with fresh random positions
        if (p.age >= p.maxAge || p.x < -20 || p.x > w + 20 || p.y < -20 || p.y > h + 20 || dist < 12) {
          // 65% spawn in active outer storm bands, 35% across wider canvas
          if (Math.random() < 0.65) {
            const rad = 40 + Math.random() * (Math.min(w, h) * 0.45);
            const ang = Math.random() * Math.PI * 2;
            p.x = cx + Math.cos(ang) * rad;
            p.y = cy + Math.sin(ang) * rad;
          } else {
            p.x = Math.random() * w;
            p.y = Math.random() * h;
          }
          p.age = 0;
          p.maxAge = 50 + Math.random() * 50;
        }
      }

      raf = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [speed]);

  return <canvas ref={ref} className="pointer-events-none absolute inset-0 z-[400] h-full w-full" />;
}
