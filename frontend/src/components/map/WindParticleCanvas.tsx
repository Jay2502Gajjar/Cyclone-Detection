import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";

interface WindParticleCanvasProps {
  lat: number;
  lon: number;
  speed?: number;
}

export function WindParticleCanvas({ lat, lon, speed = 1 }: WindParticleCanvasProps) {
  const map = useMap();
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !map) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: false });
    if (!ctx) return;
    let raf = 0;

    const resize = () => {
      const size = map.getSize();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = size.x * dpr;
      canvas.height = size.y * dpr;
      canvas.style.width = `${size.x}px`;
      canvas.style.height = `${size.y}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    map.on("resize", resize);

    // Function to get current container pixel center of cyclone
    const getCyclonePoint = () => map.latLngToContainerPoint([lat, lon]);

    let cp = getCyclonePoint();
    const count = 350;

    const getRadius = () => {
      const zoom = map.getZoom();
      return Math.max(45, Math.min(300, 75 * Math.pow(1.35, zoom - 5)));
    };

    const particles = Array.from({ length: count }).map(() => {
      const rMax = getRadius();
      const ang = Math.random() * Math.PI * 2;
      const rad = 12 + Math.random() * (rMax - 12);
      return {
        x: cp.x + Math.cos(ang) * rad,
        y: cp.y + Math.sin(ang) * rad,
        age: Math.random() * 70,
        maxAge: 35 + Math.random() * 45,
        speed: 0.8 + Math.random() * 0.5,
      };
    });

    const onMapMove = () => {
      cp = getCyclonePoint();
    };
    map.on("move", onMapMove);
    map.on("zoom", onMapMove);

    const tick = () => {
      const size = map.getSize();
      const w = size.x;
      const h = size.y;
      cp = getCyclonePoint();
      const currentMaxRadius = getRadius();

      // Clear with soft alpha fade to produce silky wind streaks
      ctx.globalCompositeOperation = "destination-out";
      ctx.fillStyle = "rgba(0, 0, 0, 0.14)";
      ctx.fillRect(0, 0, w, h);
      ctx.globalCompositeOperation = "source-over";

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        if (!p) continue;
        const dx = p.x - cp.x;
        const dy = p.y - cp.y;
        const dist = Math.hypot(dx, dy);

        // Inward cyclonic swirl vector field
        const tangentAngle = Math.atan2(dy, dx) + Math.PI / 2;
        const inflowAngle = 0.24 * Math.min(1.2, dist / currentMaxRadius);
        const theta = tangentAngle + inflowAngle;

        const v = Math.min(3.4, (2.2 * speed * p.speed * 110) / Math.pow(Math.max(12, dist), 0.72));
        const nx = p.x + Math.cos(theta) * v;
        const ny = p.y + Math.sin(theta) * v;

        const lifeFraction = p.age / p.maxAge;
        const falloff = Math.max(0, 1 - dist / currentMaxRadius);
        const alpha = Math.sin(lifeFraction * Math.PI) * falloff * 0.85;

        if (alpha > 0.02) {
          if (dist < 35) {
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha.toFixed(2)})`;
            ctx.lineWidth = 1.3;
          } else if (dist < currentMaxRadius * 0.5) {
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha.toFixed(2)})`;
            ctx.lineWidth = 1.0;
          } else {
            ctx.strokeStyle = `rgba(59, 130, 246, ${(alpha * 0.75).toFixed(2)})`;
            ctx.lineWidth = 0.8;
          }

          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(nx, ny);
          ctx.stroke();
        }

        p.x = nx;
        p.y = ny;
        p.age += 1;

        if (p.age >= p.maxAge || dist > currentMaxRadius || dist < 7) {
          const ang = Math.random() * Math.PI * 2;
          const rad = 10 + Math.random() * (currentMaxRadius - 10);
          p.x = cp.x + Math.cos(ang) * rad;
          p.y = cp.y + Math.sin(ang) * rad;
          p.age = 0;
          p.maxAge = 30 + Math.random() * 40;
        }
      }

      raf = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      cancelAnimationFrame(raf);
      map.off("resize", resize);
      map.off("move", onMapMove);
      map.off("zoom", onMapMove);
    };
  }, [lat, lon, speed, map]);

  return <canvas ref={ref} className="pointer-events-none absolute inset-0 z-[400] h-full w-full" />;
}
