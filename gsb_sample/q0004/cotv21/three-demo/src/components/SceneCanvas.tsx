import { useEffect, useRef, useCallback } from "react";
import * as THREE from "three";

export function SceneCanvas() {
  const mountRef = useRef<HTMLDivElement>(null);
  const scrollProgressRef = useRef(0);
  const targetScrollProgressRef = useRef(0);
  const isDraggingRef = useRef(false);
  const previousMousePositionRef = useRef({ x: 0, y: 0 });
  const orbitRotationRef = useRef({ x: 0, y: 0 });
  const raycasterRef = useRef(new THREE.Raycaster());
  const mousePositionRef = useRef(new THREE.Vector2());
  const isHoveringRef = useRef(false);

  const getScrollProgress = useCallback(() => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    return docHeight > 0 ? Math.min(1, Math.max(0, scrollTop / docHeight)) : 0;
  }, []);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0b1a);
    scene.fog = new THREE.FogExp2(0x0a0b1a, 0.02);

    // Camera
    const camera = new THREE.PerspectiveCamera(
      55,
      window.innerWidth / window.innerHeight,
      0.1,
      100,
    );
    camera.position.set(0, 0, 6);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    // Main object - Icosahedron with subdivisions
    const mainGeometry = new THREE.IcosahedronGeometry(1.8, 3);
    const mainMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x64b5f6,
      metalness: 0.8,
      roughness: 0.2,
      clearcoat: 1,
      clearcoatRoughness: 0.2,
    });
    const mainMesh = new THREE.Mesh(mainGeometry, mainMaterial);
    mainMesh.castShadow = true;
    mainMesh.receiveShadow = true;
    scene.add(mainMesh);

    // Wireframe object
    const wireframeGeometry = new THREE.IcosahedronGeometry(2.2, 2);
    const wireframeMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
    });
    const wireframeMesh = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
    scene.add(wireframeMesh);

    // Particle system
    const particleCount = 1000;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 15;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 15;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 15;
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.05,
      transparent: true,
      opacity: 0.6,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0x64b5f6, 2);
    keyLight.position.set(5, 5, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x880e4f, 1.5);
    fillLight.position.set(-5, -5, 5);
    scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xffffff, 1);
    rimLight.position.set(0, 0, -5);
    scene.add(rimLight);

    // Animation loop
    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);

      // Raycaster hover detection
      raycasterRef.current.setFromCamera(mousePositionRef.current, camera);
      const intersects = raycasterRef.current.intersectObject(mainMesh);
      const wasHovering = isHoveringRef.current;
      isHoveringRef.current = intersects.length > 0;

      // Update hover feedback
      if (isHoveringRef.current !== wasHovering) {
        if (isHoveringRef.current) {
          mainMaterial.emissive = new THREE.Color(0x336699);
          mainMaterial.emissiveIntensity = 0.3;
        } else {
          mainMaterial.emissive = new THREE.Color(0x000000);
          mainMaterial.emissiveIntensity = 0;
        }
      }

      // Smooth scroll progress interpolation
      scrollProgressRef.current += (targetScrollProgressRef.current - scrollProgressRef.current) * 0.05;
      const progress = scrollProgressRef.current;

      // Animate main object based on scroll progress and orbit rotation
      mainMesh.rotation.y = progress * Math.PI * 2 + orbitRotationRef.current.y;
      mainMesh.rotation.x = progress * Math.PI * 0.5 + orbitRotationRef.current.x;
      mainMesh.position.y = Math.sin(progress * Math.PI * 2) * 0.5;

      // Animate wireframe
      wireframeMesh.rotation.y = -progress * Math.PI * 1.5;
      wireframeMesh.rotation.x = progress * Math.PI * 0.3;
      wireframeMaterial.opacity = 0.3 + progress * 0.4;

      // Animate particles
      particles.rotation.y = progress * Math.PI * 0.3;
      particles.rotation.x = progress * Math.PI * 0.1;
      particleMaterial.opacity = 0.6 - progress * 0.4;

      // Camera animation
      const cameraRadius = 6 - progress * 2;
      camera.position.x = Math.sin(progress * Math.PI * 0.5) * cameraRadius;
      camera.position.z = Math.cos(progress * Math.PI * 0.5) * cameraRadius;
      camera.lookAt(0, 0, 0);

      // Light animation
      keyLight.intensity = 2 - progress * 1;
      fillLight.intensity = 1.5 + progress * 0.5;
      rimLight.intensity = 1 + progress * 0.8;

      // Fog animation
      (scene.fog as THREE.FogExp2).density = 0.02 + progress * 0.03;

      renderer.render(scene, camera);
    };
    tick();

    // Resize handler
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    // Scroll handler
    const handleScroll = () => {
      targetScrollProgressRef.current = getScrollProgress();
    };
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Initial scroll position
      handleScroll();

      // Mouse event handlers for orbit dragging
      const handleMouseDown = (event: MouseEvent) => {
        isDraggingRef.current = true;
        previousMousePositionRef.current = {
          x: event.clientX,
          y: event.clientY
        };
      };

      const handleMouseMove = (event: MouseEvent) => {
        // Update mouse position for raycaster
        mousePositionRef.current.x = (event.clientX / window.innerWidth) * 2 - 1;
        mousePositionRef.current.y = -(event.clientY / window.innerHeight) * 2 + 1;

        // Handle orbit dragging
        if (isDraggingRef.current) {
          const deltaX = event.clientX - previousMousePositionRef.current.x;
          const deltaY = event.clientY - previousMousePositionRef.current.y;

          // Update orbit rotation
          orbitRotationRef.current.y += deltaX * 0.01;
          orbitRotationRef.current.x += deltaY * 0.01;

          // Clamp vertical rotation to prevent flipping
          orbitRotationRef.current.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, orbitRotationRef.current.x));

          previousMousePositionRef.current = {
            x: event.clientX,
            y: event.clientY
          };
        }
      };

      const handleMouseUp = () => {
        isDraggingRef.current = false;
      };

      const handleMouseLeave = () => {
        isDraggingRef.current = false;
      };

      // Add mouse event listeners
      renderer.domElement.addEventListener('mousedown', handleMouseDown);
      renderer.domElement.addEventListener('mousemove', handleMouseMove);
      renderer.domElement.addEventListener('mouseup', handleMouseUp);
      renderer.domElement.addEventListener('mouseleave', handleMouseLeave);

      // Cleanup
      return () => {
        cancelAnimationFrame(raf);
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleScroll);
        
        // Remove mouse event listeners
        renderer.domElement.removeEventListener('mousedown', handleMouseDown);
        renderer.domElement.removeEventListener('mousemove', handleMouseMove);
        renderer.domElement.removeEventListener('mouseup', handleMouseUp);
        renderer.domElement.removeEventListener('mouseleave', handleMouseLeave);

      // Dispose geometries and materials
      mainGeometry.dispose();
      mainMaterial.dispose();
      wireframeGeometry.dispose();
      wireframeMaterial.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();

      // Dispose renderer
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [getScrollProgress]);

  return <div ref={mountRef} className="scene-mount" />;
}
