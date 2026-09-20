import { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { VRM, VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';
import type { VoiceStatus } from '../hooks/useVoice';

interface Avatar3DProps {
  isConnected: boolean;
  status: VoiceStatus;
  lastTranscription: string;
  lastResponse: string;
  onTapStart: () => void;
  onTapStop: () => void;
}

const STATUS_LABELS: Record<VoiceStatus, string> = {
  idle: 'Tap to Speak',
  recording: 'Listening...',
  transcribing: 'Transcribing...',
  thinking: 'Thinking...',
  speaking: 'Speaking...',
  error: 'Error — Try Again',
};

export const Avatar3D = ({
  isConnected,
  status,
  lastTranscription,
  lastResponse,
  onTapStart,
  onTapStop,
}: Avatar3DProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const vrmRef = useRef<VRM | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadProgress, setLoadProgress] = useState(0);

  const isRecording = status === 'recording';
  const isProcessing = status === 'transcribing' || status === 'thinking';
  const isSpeaking = status === 'speaking';

  // Mouse position in normalized device coords (-1 to +1)
  const mousePos = useRef({ x: 0, y: 0 });

  const handlePointerMove = useCallback((e: MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    mousePos.current = { x: Math.max(-1, Math.min(1, x)), y: Math.max(-1, Math.min(1, y)) };
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handlePointerMove);
    return () => window.removeEventListener('mousemove', handlePointerMove);
  }, [handlePointerMove]);

  // Main Three.js setup and animation loop
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene
    const scene = new THREE.Scene();

    // 2. Camera (Upper-body portrait framing)
    const width = container.clientWidth;
    const height = container.clientHeight;
    const camera = new THREE.PerspectiveCamera(30, width / height, 0.1, 20);
    camera.position.set(0, 1.4, 1.15);

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    // 4. Lighting (Warm fill + Cyberpunk Cyan Rim Light)
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xfff5ea, 1.5);
    keyLight.position.set(1, 2, 2);
    scene.add(keyLight);

    // Arc reactor cyan rim light for futuristic glow
    const rimLight = new THREE.DirectionalLight(0x00d4ff, 2.0);
    rimLight.position.set(-1.5, 1.5, -1);
    scene.add(rimLight);

    // 5. Load VRM Model
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      '/models/avatar.vrm',
      (gltf) => {
        const vrm = gltf.userData.vrm as VRM;
        if (!vrm) return;

        VRMUtils.removeUnnecessaryVertices(gltf.scene);
        VRMUtils.removeUnnecessaryJoints(gltf.scene);
        VRMUtils.rotateVRM0(vrm);

        vrmRef.current = vrm;
        scene.add(vrm.scene);

        // Position avatar so face is centered
        vrm.scene.position.set(0, 0, 0);

        setIsLoading(false);
      },
      (progress) => {
        if (progress.total > 0) {
          setLoadProgress(Math.round((progress.loaded / progress.total) * 100));
        }
      },
      (err) => {
        console.error('Error loading VRM:', err);
        setIsLoading(false);
      }
    );

    // 6. Animation State
    const clock = new THREE.Clock();
    let blinkTimer = 0;
    let nextBlinkInterval = 3;
    let isBlinking = false;
    let blinkProgress = 0;

    let animId: number;

    const animate = () => {
      animId = requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();
      const vrm = vrmRef.current;

      if (vrm) {
        // --- A. Breathing Animation ---
        const spine = vrm.humanoid?.getNormalizedBoneNode('spine');
        if (spine) {
          spine.rotation.x = Math.sin(elapsed * 2.0) * 0.02;
        }

        // --- B. Smooth Head Mouse Tracking ---
        const head = vrm.humanoid?.getNormalizedBoneNode('head');
        if (head) {
          const targetY = mousePos.current.x * 0.35;
          const targetX = -mousePos.current.y * 0.25;
          head.rotation.y = THREE.MathUtils.lerp(head.rotation.y, targetY, 0.06);
          head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, targetX, 0.06);
        }

        // --- C. Natural Blinking Cycle ---
        blinkTimer += delta;
        if (!isBlinking && blinkTimer > nextBlinkInterval) {
          isBlinking = true;
          blinkTimer = 0;
          blinkProgress = 0;
          nextBlinkInterval = 2.5 + Math.random() * 3.5;
        }

        if (isBlinking) {
          blinkProgress += delta * 8; // blink speed
          const eyeClose = Math.sin(blinkProgress * Math.PI);
          if (eyeClose <= 0) {
            isBlinking = false;
            vrm.expressionManager?.setValue('blink', 0);
          } else {
            vrm.expressionManager?.setValue('blink', Math.min(1, Math.max(0, eyeClose)));
          }
        }

        // --- D. Lip Sync & Speaking Visemes ---
        if (status === 'speaking') {
          // Dynamic lip movements using multiple visemes
          const mouthA = (Math.sin(elapsed * 12) + 1) * 0.35;
          const mouthO = (Math.cos(elapsed * 8) + 1) * 0.25;
          vrm.expressionManager?.setValue('aa', mouthA);
          vrm.expressionManager?.setValue('oh', mouthO);
          vrm.expressionManager?.setValue('happy', 0.4);
        } else {
          vrm.expressionManager?.setValue('aa', 0);
          vrm.expressionManager?.setValue('oh', 0);

          if (status === 'thinking') {
            vrm.expressionManager?.setValue('happy', 0.1);
            vrm.expressionManager?.setValue('relaxed', 0.5);
          } else if (status === 'recording') {
            vrm.expressionManager?.setValue('happy', 0.2);
            vrm.expressionManager?.setValue('relaxed', 0);
          } else {
            vrm.expressionManager?.setValue('happy', 0.15);
            vrm.expressionManager?.setValue('relaxed', 0);
          }
        }

        vrm.expressionManager?.update();
        vrm.update(delta);
      }

      renderer.render(scene, camera);
    };

    animate();

    // 7. Resize handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [status]);

  const handleTap = () => {
    if (!isConnected || isProcessing || isSpeaking) return;
    if (isRecording) {
      onTapStop();
    } else {
      onTapStart();
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center h-full w-full bg-[var(--color-arc-bg)] border-r border-[var(--color-arc-border)] overflow-hidden select-none">
      {/* 3D Canvas Container */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--color-arc-bg)] z-30 font-mono">
          <div className="w-12 h-12 rounded-full border-2 border-t-[var(--color-arc-cyan)] border-r-transparent border-b-transparent border-l-transparent animate-spin mb-4" />
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-arc-cyan)]">
            Loading Neural Avatar... {loadProgress}%
          </p>
        </div>
      )}

      {/* Ambient Cyberpunk Hologram Grid */}
      <div className="absolute bottom-0 inset-x-0 h-40 bg-gradient-to-t from-[rgba(0,212,255,0.06)] to-transparent pointer-events-none" />

      {/* Floating Interactive Controls (Bottom HUD) */}
      <div className="absolute bottom-6 inset-x-0 flex flex-col items-center pointer-events-auto z-20 px-4">
        {/* Tap to Talk Button */}
        <button
          onClick={handleTap}
          disabled={!isConnected || isProcessing || isSpeaking}
          className={`flex items-center gap-3 px-6 py-2.5 rounded-full border transition-all duration-300 backdrop-blur-md font-mono text-xs uppercase tracking-wider shadow-lg ${
            isRecording
              ? 'bg-red-500/20 border-red-500 text-red-400 shadow-[0_0_25px_rgba(239,68,68,0.4)] animate-pulse'
              : isProcessing
                ? 'bg-amber-500/20 border-amber-500 text-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.3)]'
                : isSpeaking
                  ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400 shadow-[0_0_20px_rgba(34,197,94,0.3)]'
                  : 'bg-[var(--color-arc-surface)]/80 border-[var(--color-arc-border)] text-[var(--color-arc-cyan)] hover:border-[var(--color-arc-cyan)] hover:shadow-[0_0_15px_rgba(0,212,255,0.3)]'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${
            isRecording ? 'bg-red-400 animate-ping' :
            isProcessing ? 'bg-amber-400 animate-pulse' :
            isSpeaking ? 'bg-emerald-400 animate-bounce' :
            'bg-[var(--color-arc-cyan)]'
          }`} />
          <span>{STATUS_LABELS[status]}</span>
        </button>

        {/* Subtitles & Thoughts Display */}
        {lastTranscription && (status === 'thinking' || status === 'speaking') && (
          <p className="text-xs text-[var(--color-arc-muted)] mt-3 italic text-center max-w-sm px-4 animate-fade-in bg-black/40 py-1 rounded backdrop-blur-sm">
            "{lastTranscription}"
          </p>
        )}

        {lastResponse && status === 'speaking' && (
          <p className="text-xs text-[var(--color-arc-text)] mt-2 text-center max-w-sm px-4 leading-relaxed animate-fade-in line-clamp-3 bg-black/50 py-1.5 rounded-md backdrop-blur-sm border border-white/5">
            {lastResponse}
          </p>
        )}
      </div>
    </div>
  );
};
