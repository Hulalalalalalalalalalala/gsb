import createGlobe from "cobe";
import { useEffect, useRef } from "react";

const W = 1000;
const H = 1000;

export function Globe() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let phi = 0;
    let theta = 0.2;
    let isDragging = false;
    let lastX = 0;
    let lastY = 0;
    let velocityX = 0;
    let velocityY = 0;
    let isAutoRotating = true;
    let scale = 1;
    let targetScale = 1;
    let pinchDistance = 0;
    
    // For Task C: marker animation
    let time = 0;
    let marker1Size = 0.05;

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
      markers: [
        { location: [31.2304, 121.4737], size: 0.05 },
        { location: [37.7595, -122.4367], size: 0.04 },
      ],
      onRender: (state) => {
        state.phi = phi;
        state.theta = theta;
        state.scale = scale;
        
        // Task C: Animate marker sizes
        time += 0.05;
        marker1Size = 0.04 + 0.06 * Math.sin(time * 3); // Shanghai marker animates with larger range and faster speed
        if (state.markers && state.markers[0]) {
          state.markers[0].size = marker1Size;
        }
        
        // Update scale with smooth transition
        scale += (targetScale - scale) * 0.1;
        
        if (isAutoRotating && !isDragging && Math.abs(velocityX) < 0.001 && Math.abs(velocityY) < 0.001) {
          phi += 0.01; // Increase auto rotation speed
        } else if (!isDragging) {
          phi += velocityX;
          theta += velocityY;
          
          // Apply friction
          velocityX *= 0.98; // Increase friction to stop faster
          velocityY *= 0.98;
          
          // Check if velocity is low enough to stop and resume auto rotation
          if (Math.abs(velocityX) < 0.001 && Math.abs(velocityY) < 0.001) {
            velocityX = 0;
            velocityY = 0;
            isAutoRotating = true;
          }
        }
      },
    });

    // Mouse event handlers
    const handleMouseDown = (e: MouseEvent) => {
      if (e.button === 0) {
        isDragging = true;
        isAutoRotating = false;
        velocityX = 0;
        velocityY = 0;
        lastX = e.clientX;
        lastY = e.clientY;
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - lastX;
        const deltaY = e.clientY - lastY;
        
        // Update phi (horizontal rotation)
        phi -= deltaX * 0.005;
        
        // Update theta (vertical rotation) with limits
        theta = Math.max(-0.8, Math.min(0.8, theta - deltaY * 0.005));
        
        // Update velocity for inertia
        velocityX = -deltaX * 0.005;
        velocityY = -deltaY * 0.005;
        
        lastX = e.clientX;
        lastY = e.clientY;
      }
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (isDragging && e.button === 0) {
        isDragging = false;
      }
    };

    // Touch event handlers
    const handleTouchStart = (e: TouchEvent) => {
      e.preventDefault();
      if (e.touches.length === 1) {
        isDragging = true;
        isAutoRotating = false;
        velocityX = 0;
        velocityY = 0;
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
      } else if (e.touches.length === 2) {
        // Initialize pinch distance
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        pinchDistance = Math.sqrt(dx * dx + dy * dy);
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      if (e.touches.length === 1 && isDragging) {
        const deltaX = e.touches[0].clientX - lastX;
        const deltaY = e.touches[0].clientY - lastY;
        
        // Update phi (horizontal rotation)
        phi -= deltaX * 0.005;
        
        // Update theta (vertical rotation) with limits
        theta = Math.max(-0.8, Math.min(0.8, theta - deltaY * 0.005));
        
        // Update velocity for inertia
        velocityX = -deltaX * 0.005;
        velocityY = -deltaY * 0.005;
        
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
      } else if (e.touches.length === 2) {
        // Calculate new pinch distance
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const newDistance = Math.sqrt(dx * dx + dy * dy);
        
        // Update scale based on pinch gesture
        const deltaScale = (newDistance - pinchDistance) / pinchDistance;
        targetScale = Math.max(0.5, Math.min(2, targetScale * (1 + deltaScale)));
        
        pinchDistance = newDistance;
      }
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (e.touches.length === 0) {
        isDragging = false;
      } else if (e.touches.length === 1 && isDragging) {
        // If one finger remains, continue dragging
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
      }
    };

    // Wheel event handler for zoom
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      // Wheel up (negative deltaY) zooms in, wheel down (positive deltaY) zooms out
      const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
      targetScale = Math.max(0.5, Math.min(2, targetScale * zoomFactor));
    };

    // Add event listeners
    canvas.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    canvas.addEventListener('touchend', handleTouchEnd);
    canvas.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      globe.destroy();
      // Remove event listeners
      canvas.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('touchstart', handleTouchStart);
      canvas.removeEventListener('touchmove', handleTouchMove);
      canvas.removeEventListener('touchend', handleTouchEnd);
      canvas.removeEventListener('wheel', handleWheel);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={W}
      height={H}
      style={{ width: "min(92vw, 520px)", height: "auto", display: "block" }}
    />
  );
}
