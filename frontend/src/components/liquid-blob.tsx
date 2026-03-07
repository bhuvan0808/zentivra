"use client";

import { useRef, useEffect } from "react";

const STYLES = `
:root {
  --blob-a: rgba(126,34,206,0.10);
  --blob-b: rgba(147,51,234,0.06);
  --blob-cursor: rgba(168,85,247,0.30);
}
.dark {
  --blob-a: rgba(192,132,252,0.20);
  --blob-b: rgba(216,180,254,0.12);
  --blob-cursor: rgba(192,132,252,0.30);
}
@keyframes blob-drift-a {
  0%, 100% { transform: translate3d(-10%, -15%, 0) scale(1); }
  33%      { transform: translate3d(15%, 5%, 0) scale(1.08); }
  66%      { transform: translate3d(-5%, 20%, 0) scale(0.95); }
}
@keyframes blob-drift-b {
  0%, 100% { transform: translate3d(20%, 10%, 0) scale(1); }
  33%      { transform: translate3d(-15%, 25%, 0) scale(1.1); }
  66%      { transform: translate3d(10%, -10%, 0) scale(0.92); }
}
@keyframes blob-morph {
  0%, 100% { border-radius: 30% 70% 60% 40% / 65% 35% 55% 45%; }
  25%      { border-radius: 58% 42% 35% 65% / 40% 60% 68% 32%; }
  50%      { border-radius: 42% 58% 65% 35% / 55% 45% 30% 70%; }
  75%      { border-radius: 65% 35% 42% 58% / 32% 68% 55% 45%; }
}
`;

export function LiquidBlob() {
  const blobRef = useRef<HTMLDivElement>(null);
  const mouse = useRef({ x: -300, y: -300 });
  const pos = useRef({ x: -300, y: -300 });
  const raf = useRef(0);
  const dirty = useRef(false);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      mouse.current.x = e.clientX;
      mouse.current.y = e.clientY;
      dirty.current = true;
    }
    function onTouch(e: TouchEvent) {
      const t = e.touches[0];
      if (t) {
        mouse.current.x = t.clientX;
        mouse.current.y = t.clientY;
        dirty.current = true;
      }
    }

    function tick() {
      if (dirty.current) {
        const dx = mouse.current.x - pos.current.x;
        const dy = mouse.current.y - pos.current.y;

        if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) {
          pos.current.x += dx * 0.08;
          pos.current.y += dy * 0.08;
        } else {
          pos.current.x = mouse.current.x;
          pos.current.y = mouse.current.y;
          dirty.current = false;
        }

        if (blobRef.current) {
          blobRef.current.style.transform = `translate3d(${pos.current.x}px,${pos.current.y}px,0)`;
        }
      }
      raf.current = requestAnimationFrame(tick);
    }

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("touchmove", onTouch, { passive: true });
    raf.current = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("touchmove", onTouch);
      cancelAnimationFrame(raf.current);
    };
  }, []);

  return (
    <>
      {/* eslint-disable-next-line react/no-danger */}
      <style dangerouslySetInnerHTML={{ __html: STYLES }} />

      {/* Ambient background blobs */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div
          className="absolute h-[80%] w-[80%] rounded-full"
          style={{
            background:
              "radial-gradient(ellipse at center, var(--blob-a), transparent 70%)",
            animation: "blob-drift-a 20s ease-in-out infinite",
            willChange: "transform",
          }}
        />
        <div
          className="absolute h-[70%] w-[70%] rounded-full"
          style={{
            background:
              "radial-gradient(ellipse at center, var(--blob-b), transparent 70%)",
            animation: "blob-drift-b 28s ease-in-out infinite",
            willChange: "transform",
          }}
        />
      </div>

      {/* Cursor-following morphing blob */}
      <div
        ref={blobRef}
        className="pointer-events-none fixed left-0 top-0 z-1"
        style={{
          width: 600,
          height: 600,
          marginLeft: -300,
          marginTop: -300,
          background:
            "radial-gradient(circle at center, var(--blob-cursor) 0%, transparent 85%)",
          filter: "blur(32px)",
          animation: "blob-morph 8s ease-in-out infinite",
          willChange: "transform, filter",
        }}
      />
    </>
  );
}
