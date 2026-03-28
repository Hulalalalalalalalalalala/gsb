import createGlobe from "cobe";
import { useEffect, useRef } from "react";

const W = 1000;
const H = 1000;

export function Globe() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const zoomRef = useRef(1);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let phi = 0;
    let theta = 0.2;
    let zoom = 1;
    let autoRotateSpeed = 0.005;

    let isDragging = false;
    let lastX = 0;
    let lastY = 0;
    let velocityX = 0;
    let velocityY = 0;
    let lastMoveTime = 0;

    let isPinching = false;
    let lastDistance = 0;

    const minZoom = 0.5;
    const maxZoom = 2.5;

    const minTheta = -Math.PI / 2 + 0.1;
    const maxTheta = Math.PI / 2 - 0.1;

    let time = 0;

    const markers: Array<{ location: [number, number]; size: number }> = [
      { location: [31.2304, 121.4737] as [number, number], size: 0.05 },
      { location: [37.7595, -122.4367] as [number, number], size: 0.04 },
    ];

    const globe = createGlobe(canvas, {
      devicePixelRatio: 2,
      width: W,
      height: H,
      phi: 0,
      theta: 0.2,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 6,
      baseColor: [0.3, 0.3, 0.35],
      markerColor: [0.98, 0.45, 0.15],
      glowColor: [0.35, 0.45, 0.55],
      markers: markers,
      onRender: (state) => {
        time += 1;

        if (!isDragging && !isPinching) {
          phi += velocityX;
          theta += velocityY;

          velocityX *= 0.95;
          velocityY *= 0.95;

          if (Math.abs(velocityX) < 0.0001 && Math.abs(velocityY) < 0.0001) {
            phi += autoRotateSpeed;
          }
        }

        theta = Math.max(minTheta, Math.min(maxTheta, theta));

        const dynamicSize = 0.05 + 0.02 * Math.sin(time * 0.02);
        state.markers = [
          { ...markers[0], size: dynamicSize },
          markers[1],
        ];

        state.phi = phi;
        state.theta = theta;
      },
    });

    const handlePointerDown = (e: PointerEvent) => {
      if (e.pointerType === 'mouse' && e.button !== 0) return;

      canvas.setPointerCapture(e.pointerId);
      isDragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      velocityX = 0;
      velocityY = 0;
      lastMoveTime = Date.now();
    };

    const handlePointerMove = (e: PointerEvent) => {
      if (!isDragging) return;

      const deltaX = e.clientX - lastX;
      const deltaY = e.clientY - lastY;
      const now = Date.now();
      const deltaTime = now - lastMoveTime;

      phi += deltaX * 0.005;
      theta += deltaY * 0.005;

      if (deltaTime > 0) {
        velocityX = deltaX * 0.005 / deltaTime * 16;
        velocityY = deltaY * 0.005 / deltaTime * 16;
      }

      lastX = e.clientX;
      lastY = e.clientY;
      lastMoveTime = now;
    };

    const handlePointerUp = (e: PointerEvent) => {
      if (canvas.hasPointerCapture(e.pointerId)) {
        canvas.releasePointerCapture(e.pointerId);
      }
      isDragging = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();

      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      zoom = Math.max(minZoom, Math.min(maxZoom, zoom * delta));
      zoomRef.current = zoom;
      canvas.style.transform = `scale(${zoom})`;
    };

    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        isPinching = true;
        isDragging = false;
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        lastDistance = Math.sqrt(dx * dx + dy * dy);
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2 && isPinching) {
        e.preventDefault();
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        const delta = distance / lastDistance;
        zoom = Math.max(minZoom, Math.min(maxZoom, zoom * delta));
        zoomRef.current = zoom;
        canvas.style.transform = `scale(${zoom})`;

        lastDistance = distance;
      }
    };

    const handleTouchEnd = () => {
      isPinching = false;
    };

    canvas.addEventListener('pointerdown', handlePointerDown);
    canvas.addEventListener('pointermove', handlePointerMove);
    canvas.addEventListener('pointerup', handlePointerUp);
    canvas.addEventListener('pointercancel', handlePointerUp);
    canvas.addEventListener('wheel', handleWheel, { passive: false });
    canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    canvas.addEventListener('touchend', handleTouchEnd);

    return () => {
      canvas.removeEventListener('pointerdown', handlePointerDown);
      canvas.removeEventListener('pointermove', handlePointerMove);
      canvas.removeEventListener('pointerup', handlePointerUp);
      canvas.removeEventListener('pointercancel', handlePointerUp);
      canvas.removeEventListener('wheel', handleWheel);
      canvas.removeEventListener('touchstart', handleTouchStart);
      canvas.removeEventListener('touchmove', handleTouchMove);
      canvas.removeEventListener('touchend', handleTouchEnd);
      globe.destroy();
    };
  }, []);

  return (
    <div style={{ 
      display: "flex", 
      justifyContent: "center", 
      alignItems: "center",
      overflow: "hidden",
      width: "min(92vw, 520px)",
      height: "min(92vw, 520px)"
    }}>
      <canvas
        ref={canvasRef}
        width={W}
        height={H}
        style={{ 
          width: "100%", 
          height: "100%", 
          display: "block", 
          touchAction: "none",
          transformOrigin: "center center"
        }}
      />
    </div>
  );
}
