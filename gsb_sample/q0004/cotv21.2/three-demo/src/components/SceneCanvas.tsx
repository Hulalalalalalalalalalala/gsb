import { useEffect, useRef } from "react";
import * as THREE from "three";

export function SceneCanvas() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0d12);
    scene.fog = new THREE.Fog(0x0b0d12, 5, 25);

    const camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      0.1,
      100,
    );
    camera.position.set(0, 0, 8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x0b0d12, 1);
    mount.appendChild(renderer.domElement);

    const mainGeometry = new THREE.IcosahedronGeometry(2, 4);
    const mainMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x7c9ef0,
      metalness: 0.9,
      roughness: 0.2,
      clearcoat: 1,
      clearcoatRoughness: 0.1,
      emissive: 0x000000,
    });
    const mainMesh = new THREE.Mesh(mainGeometry, mainMaterial);
    scene.add(mainMesh);

    const wireframeGeometry = new THREE.IcosahedronGeometry(2.5, 1);
    const wireframeMaterial = new THREE.MeshBasicMaterial({
      color: 0xa8c4ff,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
    });
    const wireframeMesh = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
    scene.add(wireframeMesh);

    const particleCount = 1500;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0xa8c4ff,
      size: 0.05,
      transparent: true,
      opacity: 0.6,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x7c9ef0, 1, 50);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xa8c4ff, 0.8, 50);
    pointLight2.position.set(-5, -3, 3);
    scene.add(pointLight2);

    let scrollProgress = 0;
    let targetScrollProgress = 0;
    let raf = 0;

    let isDragging = false;
    let dragDeltaX = 0;
    let dragDeltaY = 0;
    let targetDragDeltaX = 0;
    let targetDragDeltaY = 0;
    let lastMouseX = 0;
    let lastMouseY = 0;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let isHovering = false;

    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      targetScrollProgress = docHeight > 0 ? scrollTop / docHeight : 0;
    };

    const handleMouseDown = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const isInCanvas = e.clientX >= rect.left && e.clientX <= rect.right &&
                        e.clientY >= rect.top && e.clientY <= rect.bottom;
      
      if (e.button === 0 && isInCanvas) {
        isDragging = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const isInCanvas = e.clientX >= rect.left && e.clientX <= rect.right &&
                        e.clientY >= rect.top && e.clientY <= rect.bottom;
      
      if (isInCanvas) {
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      }

      if (isDragging) {
        const deltaX = e.clientX - lastMouseX;
        const deltaY = e.clientY - lastMouseY;
        targetDragDeltaX += deltaX * 0.01;
        targetDragDeltaY += deltaY * 0.01;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      }
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    const handleMouseLeave = () => {
      isDragging = false;
    };

    const tick = () => {
      raf = requestAnimationFrame(tick);

      scrollProgress += (targetScrollProgress - scrollProgress) * 0.05;
      dragDeltaX += (targetDragDeltaX - dragDeltaX) * 0.1;
      dragDeltaY += (targetDragDeltaY - dragDeltaY) * 0.1;

      mainMesh.rotation.x = scrollProgress * Math.PI * 2;
      mainMesh.rotation.y = scrollProgress * Math.PI * 1.5;
      mainMesh.position.y = Math.sin(scrollProgress * Math.PI * 2) * 1.5;
      mainMesh.position.z = Math.cos(scrollProgress * Math.PI) * 2;

      wireframeMesh.rotation.x = -scrollProgress * Math.PI * 1.5;
      wireframeMesh.rotation.y = -scrollProgress * Math.PI * 2;
      wireframeMesh.position.y = Math.sin(scrollProgress * Math.PI * 2 + 0.5) * 1.5;
      wireframeMesh.position.z = Math.cos(scrollProgress * Math.PI + 0.5) * 2;
      wireframeMaterial.opacity = 0.1 + scrollProgress * 0.4;

      particles.rotation.y = scrollProgress * Math.PI * 0.5;
      particleMaterial.opacity = 0.3 + (1 - scrollProgress) * 0.5;

      const cameraAngle = scrollProgress * Math.PI * 0.3 + dragDeltaX;
      const cameraRadius = 8 - scrollProgress * 3;
      const cameraY = Math.sin(scrollProgress * Math.PI) * 2 + dragDeltaY * 2;
      camera.position.x = Math.sin(cameraAngle) * cameraRadius;
      camera.position.z = Math.cos(cameraAngle) * cameraRadius;
      camera.position.y = Math.max(-5, Math.min(5, cameraY));
      camera.lookAt(0, 0, 0);

      pointLight1.intensity = 0.5 + scrollProgress * 1;
      pointLight2.intensity = 0.3 + (1 - scrollProgress) * 1;

      (scene.fog as THREE.Fog).near = 5 + scrollProgress * 5;
      (scene.fog as THREE.Fog).far = 15 + scrollProgress * 15;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObject(mainMesh);
      const wasHovering = isHovering;
      isHovering = intersects.length > 0;

      if (isHovering !== wasHovering) {
        if (isHovering) {
          mainMaterial.emissive.setHex(0x2a3f5f);
        } else {
          mainMaterial.emissive.setHex(0x000000);
        }
      }

      renderer.render(scene, camera);
    };
    tick();

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleResize);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mouseleave', handleMouseLeave);
      mainGeometry.dispose();
      mainMaterial.dispose();
      wireframeGeometry.dispose();
      wireframeMaterial.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div 
      ref={mountRef} 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 1,
      }} 
    />
  );
}
