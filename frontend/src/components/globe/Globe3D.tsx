import { Canvas, useFrame, useLoader, useThree } from "@react-three/fiber";
import { Html, Line, OrbitControls } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import earthMap from "@/assets/earth-map.jpg";
import { useCyclone } from "@/state/cyclone-store";
import type { Cyclone } from "@/types/cyclone";

const R = 1;

function toVec(lat: number, lon: number, r = R): THREE.Vector3 {
  const safeLat = typeof lat === "number" && !isNaN(lat) ? lat : 15.0;
  const safeLon = typeof lon === "number" && !isNaN(lon) ? lon : 75.0;
  const phi = ((90 - safeLat) * Math.PI) / 180;
  const theta = ((safeLon + 180) * Math.PI) / 180;
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta),
  );
}

// =========================================================================
// 🌀 CAMBECC/EARTH (earth.nullschool.net) CYCLONE PARTICLE STREAMLINE VORTEX
// Dynamic GPU Canvas Texture with continuous decaying streamline physics
// =========================================================================
function EarthNullschoolCycloneVortex({ lat, lon, intensity }: { lat: number; lon: number; intensity: number }) {
  const pos = useMemo(() => toVec(lat, lon, R + 0.006), [lat, lon]);
  const size = 512;
  const count = 380;
  const scale = 0.13 + (Math.min(260, Math.max(60, intensity)) / 260) * 0.12;

  // Create persistent canvas & particles for real-time streamline animation
  const [canvas, ctx, tex, particles] = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = size;
    c.height = size;
    const context = c.getContext("2d");

    const cx = size / 2;
    const cy = size / 2;

    const parts = Array.from({ length: count }).map(() => {
      const rad = 15 + Math.random() * (size * 0.46);
      const ang = Math.random() * Math.PI * 2;
      return {
        x: cx + Math.cos(ang) * rad,
        y: cy + Math.sin(ang) * rad,
        age: Math.random() * 80,
        maxAge: 50 + Math.random() * 50,
        speed: 0.85 + Math.random() * 0.45,
      };
    });

    const texture = new THREE.CanvasTexture(c);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;

    return [c, context, texture, parts];
  }, []);

  useFrame(() => {
    if (!ctx) return;
    const cx = size / 2;
    const cy = size / 2;

    // Decaying trail effect for smooth silky streamlines
    ctx.globalCompositeOperation = "destination-out";
    ctx.fillStyle = "rgba(0, 0, 0, 0.09)";
    ctx.fillRect(0, 0, size, size);
    ctx.globalCompositeOperation = "source-over";

    const speedMultiplier = (intensity / 100) * 1.35;

    for (let i = 0; i < count; i++) {
      const p = particles[i];
      if (!p) continue;
      const dx = p.x - cx;
      const dy = p.y - cy;
      const dist = Math.max(8, Math.hypot(dx, dy));

      // Holland/Rankine vortex physics: tangential circulation + inward suction
      const tangent = Math.atan2(dy, dx) + Math.PI / 2;
      const inflow = 0.28 * Math.min(1.4, dist / 90);
      const angle = tangent + inflow;

      const v = Math.min(4.8, (2.6 * speedMultiplier * p.speed * 85) / Math.pow(dist, 0.78));
      const nx = p.x + Math.cos(angle) * v;
      const ny = p.y + Math.sin(angle) * v;

      const lifeFraction = p.age / p.maxAge;
      const alpha = Math.sin(lifeFraction * Math.PI) * 0.75;

      // Color based on distance to eyewall: Electric Cyan -> Cobalt -> Crisp White
      if (dist < 45) {
        ctx.strokeStyle = `rgba(248, 250, 252, ${alpha.toFixed(2)})`;
        ctx.lineWidth = 1.6;
      } else if (dist < 120) {
        ctx.strokeStyle = `rgba(56, 189, 248, ${alpha.toFixed(2)})`;
        ctx.lineWidth = 1.2;
      } else {
        ctx.strokeStyle = `rgba(59, 130, 246, ${(alpha * 0.8).toFixed(2)})`;
        ctx.lineWidth = 0.9;
      }

      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(nx, ny);
      ctx.stroke();

      p.x = nx;
      p.y = ny;
      p.age += 1;

      // Reset particles when expired or spiraled too close to the eye
      if (p.age >= p.maxAge || dist < 10 || p.x < 0 || p.x > size || p.y < 0 || p.y > size) {
        const rad = 25 + Math.random() * (size * 0.44);
        const ang = Math.random() * Math.PI * 2;
        p.x = cx + Math.cos(ang) * rad;
        p.y = cy + Math.sin(ang) * rad;
        p.age = 0;
        p.maxAge = 45 + Math.random() * 50;
      }
    }

    tex.needsUpdate = true;
  });

  return (
    <group position={pos} onUpdate={(self) => { if (self.position.lengthSq() > 0.001) self.lookAt(0, 0, 0); }}>
      <mesh rotation={[Math.PI, 0, 0]}>
        <planeGeometry args={[scale * 2.4, scale * 2.4]} />
        <meshBasicMaterial
          map={tex}
          transparent
          opacity={0.95}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}

// =========================================================================
// 🎯 CAMBECC/EARTH (earth.nullschool.net) TARGET PINPOINT RETICLE
// Concentric pulsating sonar wave and precision targeting crosshair
// =========================================================================
function EarthNullschoolPinpoint({ lat, lon }: { lat: number; lon: number }) {
  const pos = useMemo(() => toVec(lat, lon, R + 0.008), [lat, lon]);
  const sonarRef = useRef<THREE.Mesh>(null);
  const sonarRef2 = useRef<THREE.Mesh>(null);

  useFrame(() => {
    const t = performance.now() / 1000;
    
    // Smooth expanding sonar waves
    if (sonarRef.current) {
      const phase1 = (t % 1.6) / 1.6;
      const s1 = 1 + phase1 * 2.4;
      sonarRef.current.scale.set(s1, s1, 1);
      (sonarRef.current.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 0.7 * (1 - phase1));
    }
    if (sonarRef2.current) {
      const phase2 = ((t + 0.8) % 1.6) / 1.6;
      const s2 = 1 + phase2 * 2.4;
      sonarRef2.current.scale.set(s2, s2, 1);
      (sonarRef2.current.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 0.7 * (1 - phase2));
    }
  });

  return (
    <group position={pos} onUpdate={(self) => { if (self.position.lengthSq() > 0.001) self.lookAt(0, 0, 0); }}>
      {/* 1. Core Pinpoint Dot */}
      <mesh>
        <circleGeometry args={[0.007, 32]} />
        <meshBasicMaterial color="#38BDF8" depthWrite={false} />
      </mesh>

      {/* 2. Inner Precision Target Ring */}
      <mesh position={[0, 0, 0.0005]}>
        <ringGeometry args={[0.010, 0.0125, 36]} />
        <meshBasicMaterial color="#38BDF8" depthWrite={false} side={THREE.DoubleSide} />
      </mesh>

      {/* 3. Outer Reticle Ring */}
      <mesh position={[0, 0, 0.0004]}>
        <ringGeometry args={[0.018, 0.0195, 36]} />
        <meshBasicMaterial color="#38BDF8" transparent opacity={0.45} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>

      {/* 4. Pulsating Sonar Wave 1 */}
      <mesh ref={sonarRef} position={[0, 0, 0.0002]}>
        <ringGeometry args={[0.011, 0.0125, 36]} />
        <meshBasicMaterial color="#38BDF8" transparent opacity={0.6} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>

      {/* 5. Pulsating Sonar Wave 2 */}
      <mesh ref={sonarRef2} position={[0, 0, 0.0003]}>
        <ringGeometry args={[0.011, 0.0125, 36]} />
        <meshBasicMaterial color="#38BDF8" transparent opacity={0.6} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

function TangentCircle({
  lat,
  lon,
  radiusKm,
  color,
  opacity,
}: {
  lat: number;
  lon: number;
  radiusKm: number;
  color: string;
  opacity: number;
}) {
  const pos = useMemo(() => toVec(lat, lon, R + 0.004), [lat, lon]);
  const r = Math.max(0.01, radiusKm / 6371);
  return (
    <group position={pos} onUpdate={(self) => { if (self.position.lengthSq() > 0.001) self.lookAt(0, 0, 0); }}>
      <mesh>
        <circleGeometry args={[r, 48]} />
        <meshBasicMaterial color={color} transparent opacity={opacity} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

// Photorealistic Natural Earth
function Earth() {
  const texture = useLoader(THREE.TextureLoader, earthMap);

  return (
    <>
      {/* Photorealistic Natural Earth Sphere */}
      <mesh>
        <sphereGeometry args={[R, 64, 64]} />
        <meshStandardMaterial
          map={texture}
          roughness={0.80}
          metalness={0.05}
        />
      </mesh>

      {/* Subtle geographic grid lines */}
      <mesh>
        <sphereGeometry args={[R + 0.0012, 36, 36]} />
        <meshBasicMaterial color="#94A3B8" wireframe transparent opacity={0.02} />
      </mesh>

      {/* Realistic atmospheric glow shell */}
      <mesh scale={1.025}>
        <sphereGeometry args={[R, 48, 48]} />
        <meshBasicMaterial color="#38BDF8" transparent opacity={0.06} side={THREE.BackSide} />
      </mesh>
    </>
  );
}

function Scene({ cyclone }: { cyclone: Cyclone }) {
  const { layers, prediction, focusHour, setFocusHour, cameraNonce, compareId } = useCyclone();
  const controls = useRef<React.ComponentRef<typeof OrbitControls>>(null);
  const [auto, setAuto] = useState(true);
  const { camera } = useThree();
  const target = useRef<THREE.Vector3 | null>(null);

  useEffect(() => {
    const lat = cyclone.lat !== 0 || cyclone.lon !== 0 ? cyclone.lat : 15.0;
    const lon = cyclone.lat !== 0 || cyclone.lon !== 0 ? cyclone.lon : 75.0;
    target.current = toVec(lat, lon, 2.7);
  }, [cyclone.lat, cyclone.lon, cameraNonce]);

  useFrame(() => {
    if (target.current) {
      camera.position.lerp(target.current, 0.06);
      camera.lookAt(0, 0, 0);
      if (camera.position.distanceTo(target.current) < 0.02) target.current = null;
    }
  });

  const revealed = prediction.status === "idle" ? cyclone.forecast : cyclone.forecast.filter((f) => prediction.revealedHours.includes(f.hour));
  const visibleForecast = layers.prediction ? revealed : [];

  const histPoints = useMemo(
    () => cyclone.track.map((p) => toVec(p.lat, p.lon, R + 0.006).toArray() as [number, number, number]),
    [cyclone],
  );
  const forecastLine = useMemo(() => {
    const pts = [toVec(cyclone.lat, cyclone.lon, R + 0.006), ...visibleForecast.map((f) => toVec(f.lat, f.lon, R + 0.006))];
    return pts.map((p) => p.toArray() as [number, number, number]);
  }, [cyclone, visibleForecast]);

  const compare = compareId ? cyclone.historical.find((h) => h.id === compareId) : null;
  const hasValidCoords = cyclone.lat !== 0 || cyclone.lon !== 0;

  return (
    <>
      <ambientLight intensity={0.65} />
      <directionalLight position={[4, 3, 5]} intensity={1.35} />
      <directionalLight position={[-4, -2, -3]} intensity={0.25} />
      <Earth />

      {/* Cambecc/earth Cyclone Streamline Vortex */}
      {hasValidCoords ? (
        <EarthNullschoolCycloneVortex
          lat={cyclone.lat}
          lon={cyclone.lon}
          intensity={cyclone.windKph > 0 ? cyclone.windKph : 120}
        />
      ) : null}

      {/* Historical Track */}
      {layers.history && histPoints.length > 1 ? (
        <Line points={histPoints} color="#94A3B8" lineWidth={1.5} />
      ) : null}

      {/* Forecast Line */}
      {forecastLine.length > 1 ? (
        <Line points={forecastLine} color="#3B82F6" lineWidth={2} dashed dashSize={0.025} gapSize={0.015} />
      ) : null}

      {/* Confidence corridor */}
      {layers.corridor
        ? visibleForecast.map((f) => (
          <TangentCircle key={`c-${f.hour}`} lat={f.lat} lon={f.lon} radiusKm={f.confidenceRadiusKm} color="#38BDF8" opacity={0.07} />
        ))
        : null}

      {/* Risk Zone */}
      {layers.risk && visibleForecast.length > 0 ? (
        <TangentCircle
          lat={visibleForecast[visibleForecast.length - 1]?.lat ?? cyclone.lat}
          lon={visibleForecast[visibleForecast.length - 1]?.lon ?? cyclone.lon}
          radiusKm={cyclone.risk.score * 4.5}
          color={cyclone.risk.level === "LOW" ? "#10B981" : "#F43F5E"}
          opacity={0.10}
        />
      ) : null}

      {/* Compare Line */}
      {compare ? (
        <Line
          points={compare.track.map((p) => toVec(p.lat, p.lon, R + 0.007).toArray() as [number, number, number])}
          color="#F59E0B"
          lineWidth={1.3}
          dashed
          dashSize={0.03}
          gapSize={0.02}
        />
      ) : null}

      {/* Sleek Minimalist Waypoint Dots */}
      {visibleForecast.map((f) => {
        const isSelected = focusHour === f.hour;

        return (
          <group key={f.hour} position={toVec(f.lat, f.lon, R + 0.008)}>
            <mesh
              onClick={(e) => {
                e.stopPropagation();
                setFocusHour(isSelected ? null : f.hour);
              }}
            >
              <sphereGeometry args={[isSelected ? 0.012 : 0.006, 16, 16]} />
              <meshBasicMaterial color={isSelected ? "#38BDF8" : "#94A3B8"} />
            </mesh>

            {isSelected && (
              <Html center distanceFactor={3.2} zIndexRange={[10, 0]}>
                <div className="pointer-events-none -translate-y-6 w-36 rounded-lg border border-border/80 bg-card/95 p-2 text-left shadow-xl backdrop-blur-md">
                  <p className="font-display text-[10px] font-semibold uppercase tracking-wider text-primary">+{f.hour}H Telemetry</p>
                  <p className="mt-0.5 font-mono text-[11px] text-foreground">
                    {f.lat.toFixed(1)}°N, {f.lon.toFixed(1)}°E
                  </p>
                  <p className="text-[10px] text-muted-foreground">Wind: <span className="font-semibold text-foreground">{f.windKph} km/h</span></p>
                  <p className="text-[10px] text-muted-foreground">Radius: ±{f.confidenceRadiusKm} km</p>
                </div>
              </Html>
            )}
          </group>
        );
      })}

      {/* Cambecc/earth Target Pinpoint with Pulsating Sonar Wave */}
      {hasValidCoords ? (
        <EarthNullschoolPinpoint lat={cyclone.lat} lon={cyclone.lon} />
      ) : null}

      <OrbitControls
        ref={controls}
        enablePan={false}
        autoRotate={auto}
        autoRotateSpeed={0.25}
        minDistance={1.4}
        maxDistance={5}
        onStart={() => setAuto(false)}
      />
    </>
  );
}

export default function Globe3D() {
  const { cyclone } = useCyclone();
  return (
    <Canvas camera={{ position: [0, 0, 3.2], fov: 42 }} dpr={[1, 2]} gl={{ antialias: true, alpha: true }}>
      <Suspense fallback={null}>
        <Scene cyclone={cyclone} />
      </Suspense>
    </Canvas>
  );
}
