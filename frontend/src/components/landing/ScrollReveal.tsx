import { useEffect, useRef, type ReactNode } from "react";

// Single shared IntersectionObserver for maximum 120fps performance
let sharedObserver: IntersectionObserver | null = null;
const observedElements = new Map<Element, (isIntersecting: boolean) => void>();

function getSharedObserver() {
  if (typeof window === "undefined") return null;
  if (!sharedObserver) {
    sharedObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const callback = observedElements.get(entry.target);
          if (callback) {
            callback(entry.isIntersecting);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -30px 0px",
      }
    );
  }
  return sharedObserver;
}

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  delay?: number; // in ms
  direction?: "up" | "down" | "left" | "right" | "fade" | "zoom";
  distance?: number; // in px
  duration?: number; // in ms
  once?: boolean;
}

export function ScrollReveal({
  children,
  className = "",
  delay = 0,
  direction = "up",
  distance = 24,
  duration = 500,
  once = true,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = getSharedObserver();
    if (!observer) return;

    const onIntersect = (isIntersecting: boolean) => {
      if (isIntersecting) {
        el.style.opacity = "1";
        el.style.transform = "translate3d(0, 0, 0) scale(1)";
        if (once) {
          observedElements.delete(el);
          observer.unobserve(el);
        }
      } else if (!once) {
        el.style.opacity = "0";
        el.style.transform = getInitialTransform();
      }
    };

    const getInitialTransform = () => {
      switch (direction) {
        case "up":
          return `translate3d(0, ${distance}px, 0)`;
        case "down":
          return `translate3d(0, -${distance}px, 0)`;
        case "left":
          return `translate3d(${distance}px, 0, 0)`;
        case "right":
          return `translate3d(-${distance}px, 0, 0)`;
        case "zoom":
          return "translate3d(0, 12px, 0) scale(0.96)";
        case "fade":
        default:
          return "translate3d(0, 0, 0)";
      }
    };

    // Initial hidden state
    el.style.opacity = "0";
    el.style.transform = getInitialTransform();
    el.style.transition = `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms, transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`;
    el.style.willChange = "opacity, transform";

    observedElements.set(el, onIntersect);
    observer.observe(el);

    return () => {
      observedElements.delete(el);
      observer.unobserve(el);
    };
  }, [delay, direction, distance, duration, once]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}

/**
 * 60-120fps Zero-Re-render Scroll Progress Bar
 */
export function ScrollProgressBar() {
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let ticking = false;

    const updateBar = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (totalHeight > 0 && barRef.current) {
        const progress = Math.min(100, Math.max(0, (window.scrollY / totalHeight) * 100));
        barRef.current.style.transform = `scaleX(${progress / 100})`;
      }
      ticking = false;
    };

    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(updateBar);
        ticking = true;
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    updateBar();

    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-[60] h-[2px] bg-transparent pointer-events-none">
      <div
        ref={barRef}
        className="h-full w-full origin-left bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] shadow-[0_0_12px_rgba(56,189,248,0.9)] will-change-transform"
        style={{ transform: "scaleX(0)" }}
      />
    </div>
  );
}
