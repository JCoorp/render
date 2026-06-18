import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const MODEL_URL = './models/Casa_mejor.glb';

const canvas = document.getElementById('viewer');
const viewerCard = document.querySelector('.viewerCard');
const message = document.getElementById('message');
const statusDot = document.getElementById('statusDot');
const loader = document.getElementById('loader');
const errorBox = document.getElementById('errorBox');
const resetViewBtn = document.getElementById('resetView');
const toggleRotateBtn = document.getElementById('toggleRotate');
const toggleLightsBtn = document.getElementById('toggleLights');
const toggleKeyboardMoveBtn = document.getElementById('toggleKeyboardMove');
const mouseLookBtn = document.getElementById('mouseLookBtn');
const fullscreenBtn = document.getElementById('fullscreen');

let model = null;
let initialCamera = null;
let extraLightsOn = true;
let keyboardMoveEnabled = true;
let mouseLookEnabled = true;
let isPointerLocked = false;
let yaw = 0;
let pitch = 0;
const mouseSensitivity = 0.0022;
const pressedKeys = new Set();
const moveClock = new THREE.Clock();

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x090b17);
scene.fog = new THREE.Fog(0x090b17, 18, 70);

const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 5000);
camera.position.set(6, 4.2, 7);

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
  powerPreference: 'high-performance'
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.22;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.065;
controls.enablePan = true;
controls.screenSpacePanning = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.55;
controls.minDistance = 0.2;
controls.maxDistance = 1000;

scene.add(new THREE.HemisphereLight(0xeaf0ff, 0x202436, 2.2));

const keyLight = new THREE.DirectionalLight(0xffffff, 3.2);
keyLight.position.set(8, 12, 8);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.near = 0.1;
keyLight.shadow.camera.far = 90;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x9edcff, 1.45);
fillLight.position.set(-8, 5, -7);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffd6f4, 1.2);
rimLight.position.set(-4, 7, 8);
scene.add(rimLight);

const extraLights = new THREE.Group();
const cyan = new THREE.PointLight(0x57f7ff, 8, 20, 2);
cyan.position.set(0, 3, 4);
const magenta = new THREE.PointLight(0xff55d7, 6, 18, 2);
magenta.position.set(-5, 3, -3);
const warm = new THREE.PointLight(0xffe3bc, 5, 16, 2);
warm.position.set(5, 3, -2);
extraLights.add(cyan, magenta, warm);
scene.add(extraLights);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(16, 128),
  new THREE.MeshStandardMaterial({ color: 0x0f1729, roughness: 0.8, metalness: 0.02 })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.02;
ground.receiveShadow = true;
scene.add(ground);

const grid = new THREE.GridHelper(32, 32, 0x57f7ff, 0x39415c);
grid.material.transparent = true;
grid.material.opacity = 0.13;
scene.add(grid);

function canvasTexture(kind, base = '#ffffff') {
  const size = 512;
  const cnv = document.createElement('canvas');
  cnv.width = size;
  cnv.height = size;
  const ctx = cnv.getContext('2d');

  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);

  if (kind === 'grass') {
    for (let i = 0; i < 3600; i++) {
      const g = 70 + Math.random() * 85;
      ctx.fillStyle = `rgba(${25 + Math.random()*25},${g},${35 + Math.random()*35},${0.22 + Math.random()*0.3})`;
      ctx.fillRect(Math.random()*size, Math.random()*size, 1 + Math.random()*3, 6 + Math.random()*18);
    }
  }

  if (kind === 'marble') {
    for (let i = 0; i < 28; i++) {
      ctx.strokeStyle = `rgba(${120+Math.random()*60},${120+Math.random()*60},${130+Math.random()*70},${0.12+Math.random()*0.18})`;
      ctx.lineWidth = 1 + Math.random()*3;
      ctx.beginPath();
      let y = Math.random()*size;
      ctx.moveTo(0, y);
      for (let x = 0; x < size; x += 20) {
        y += (Math.random() - .5) * 30;
        ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }

  if (kind === 'wood' || kind === 'darkwood') {
    for (let y = 0; y < size; y += 5) {
      const alpha = 0.12 + Math.random()*0.16;
      ctx.fillStyle = kind === 'darkwood'
        ? `rgba(20,10,4,${alpha})`
        : `rgba(120,65,25,${alpha})`;
      ctx.fillRect(0, y + Math.sin(y*.04)*8, size, 2 + Math.random()*4);
    }
    for (let i=0;i<20;i++){
      ctx.strokeStyle = kind === 'darkwood' ? 'rgba(255,210,160,.08)' : 'rgba(50,25,10,.12)';
      ctx.beginPath();
      const y = Math.random()*size;
      ctx.ellipse(Math.random()*size, y, 20+Math.random()*50, 5+Math.random()*15, 0, 0, Math.PI*2);
      ctx.stroke();
    }
  }

  if (kind === 'concrete') {
    for (let i = 0; i < 6000; i++) {
      const v = 150 + Math.random()*70;
      ctx.fillStyle = `rgba(${v},${v-6},${v-14},${0.05 + Math.random()*0.1})`;
      ctx.fillRect(Math.random()*size, Math.random()*size, 1+Math.random()*2, 1+Math.random()*2);
    }
  }

  if (kind === 'roof') {
    for (let y = 0; y < size; y += 32) {
      ctx.fillStyle = 'rgba(255,255,255,.035)';
      ctx.fillRect(0, y, size, 2);
    }
  }

  const texture = new THREE.CanvasTexture(cnv);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2, 2);
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}

const tex = {
  grass: canvasTexture('grass', '#2f6b3f'),
  marble: canvasTexture('marble', '#e7e0d2'),
  wood: canvasTexture('wood', '#7a4a2a'),
  darkwood: canvasTexture('darkwood', '#2a160d'),
  concrete: canvasTexture('concrete', '#c8c0b0'),
  roof: canvasTexture('roof', '#2d3039')
};

function applyNamedMaterial(mat) {
  if (!mat) return;

  const name = (mat.name || '').toLowerCase();

  mat.side = THREE.DoubleSide;
  mat.needsUpdate = true;

  if (mat.map) mat.map.colorSpace = THREE.SRGBColorSpace;
  if (mat.emissiveMap) mat.emissiveMap.colorSpace = THREE.SRGBColorSpace;

  if (name.includes('pasto') || name.includes('jardín') || name.includes('jardin')) {
    mat.color = new THREE.Color('#3d7b46');
    mat.map = tex.grass;
    mat.roughness = 0.95;
    mat.metalness = 0;
  } else if (name.includes('mármol') || name.includes('marmol') || name.includes('banqueta') || name.includes('camino')) {
    mat.color = new THREE.Color('#e8e2d6');
    mat.map = tex.marble;
    mat.roughness = 0.36;
    mat.metalness = 0.02;
  } else if (name.includes('nogal')) {
    mat.color = new THREE.Color('#7a4a2a');
    mat.map = tex.wood;
    mat.roughness = 0.48;
    mat.metalness = 0;
  } else if (name.includes('concreto') || name.includes('muro')) {
    mat.color = new THREE.Color('#c8c0b0');
    mat.map = tex.concrete;
    mat.roughness = 0.82;
    mat.metalness = 0;
  } else if (name.includes('madera oscura') || name.includes('puerta')) {
    mat.color = new THREE.Color('#2a160d');
    mat.map = tex.darkwood;
    mat.roughness = 0.52;
    mat.metalness = 0;
  } else if (name.includes('grafito') || name.includes('techo') || name.includes('losa')) {
    mat.color = new THREE.Color('#30333d');
    mat.map = tex.roof;
    mat.roughness = 0.72;
    mat.metalness = 0.03;
  } else if (name.includes('cristal') || name.includes('vidrio')) {
    mat.color = new THREE.Color('#7ccfff');
    mat.transparent = true;
    mat.opacity = 0.42;
    mat.roughness = 0.02;
    mat.metalness = 0;
    if ('transmission' in mat) mat.transmission = 0.4;
  } else if (name.includes('agua')) {
    mat.color = new THREE.Color('#00a8ff');
    mat.transparent = true;
    mat.opacity = 0.55;
    mat.roughness = 0.02;
    mat.metalness = 0;
  } else if (name.includes('neón') || name.includes('neon')) {
    mat.toneMapped = false;
  }
}

function prepareModel(root) {
  root.traverse((child) => {
    if (!child.isMesh) return;

    child.castShadow = true;
    child.receiveShadow = true;

    if (Array.isArray(child.material)) child.material.forEach(applyNamedMaterial);
    else applyNamedMaterial(child.material);

    if (child.geometry) {
      child.geometry.computeBoundingBox();
      child.geometry.computeBoundingSphere();
    }
  });
}

function fitModel(root) {
  const box = new THREE.Box3().setFromObject(root);
  if (box.isEmpty()) return;

  const center = box.getCenter(new THREE.Vector3());
  root.position.sub(center);

  const box2 = new THREE.Box3().setFromObject(root);
  const size = box2.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;

  const desiredSize = 7.2;
  root.scale.multiplyScalar(desiredSize / maxDim);

  const finalBox = new THREE.Box3().setFromObject(root);
  root.position.y -= finalBox.min.y;

  const finalBox2 = new THREE.Box3().setFromObject(root);
  const finalSize = finalBox2.getSize(new THREE.Vector3());
  const finalMax = Math.max(finalSize.x, finalSize.y, finalSize.z) || 1;

  const distance = (finalMax / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)))) * 1.35;

  camera.near = Math.max(distance / 1000, 0.01);
  camera.far = distance * 90;
  camera.updateProjectionMatrix();

  camera.position.set(distance * 0.95, distance * 0.62, distance * 0.95);
  controls.target.set(0, finalSize.y * 0.30, 0);
  controls.minDistance = Math.max(distance * 0.13, 0.25);
  controls.maxDistance = distance * 8;
  controls.update();

  initialCamera = { position: camera.position.clone(), target: controls.target.clone() };
  syncMouseLookFromCamera();

  const shadowRange = Math.max(14, finalMax * 3);
  keyLight.shadow.camera.left = -shadowRange;
  keyLight.shadow.camera.right = shadowRange;
  keyLight.shadow.camera.top = shadowRange;
  keyLight.shadow.camera.bottom = -shadowRange;
  keyLight.shadow.camera.updateProjectionMatrix();
}

function setStatus(text, type = 'loading') {
  message.textContent = text;
  statusDot.classList.remove('loading', 'error');
  if (type === 'loading') statusDot.classList.add('loading');
  if (type === 'error') statusDot.classList.add('error');
}

async function loadModel() {
  try {
    setStatus('Cargando Casa_mejor.glb...', 'loading');
    loader.classList.remove('hidden');
    errorBox.classList.add('hidden');

    const gltf = await new GLTFLoader().loadAsync(MODEL_URL);
    model = gltf.scene;
    prepareModel(model);
    scene.add(model);
    fitModel(model);

    loader.classList.add('hidden');
    setStatus('Modelo renderizado con materiales corregidos.', 'ready');
  } catch (err) {
    console.error(err);
    loader.classList.add('hidden');
    errorBox.classList.remove('hidden');
    setStatus('Error al cargar el modelo.', 'error');
  }
}



function syncMouseLookFromCamera() {
  const euler = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ');
  pitch = euler.x;
  yaw = euler.y;
}

function enterMouseLook() {
  if (!mouseLookEnabled) return;
  syncMouseLookFromCamera();
  canvas.requestPointerLock?.();
}

function updatePointerLockState() {
  isPointerLocked = document.pointerLockElement === canvas;
  controls.enabled = !isPointerLocked;
  mouseLookBtn.textContent = isPointerLocked ? 'Mirada mouse: Activa' : 'Mirada mouse: Clic';
}

document.addEventListener('pointerlockchange', updatePointerLockState);

document.addEventListener('mousemove', (event) => {
  if (!isPointerLocked || !mouseLookEnabled) return;

  yaw -= event.movementX * mouseSensitivity;
  pitch -= event.movementY * mouseSensitivity;

  const limit = Math.PI / 2 - 0.06;
  pitch = Math.max(-limit, Math.min(limit, pitch));

  camera.quaternion.setFromEuler(new THREE.Euler(pitch, yaw, 0, 'YXZ'));

  const forward = new THREE.Vector3();
  camera.getWorldDirection(forward);
  controls.target.copy(camera.position).add(forward.multiplyScalar(5));
});

canvas.addEventListener('click', () => {
  enterMouseLook();
});

mouseLookBtn.addEventListener('click', () => {
  enterMouseLook();
});

function updateKeyboardMovement(delta) {
  if (!keyboardMoveEnabled) return;
  if (pressedKeys.size === 0) return;

  const forward = new THREE.Vector3();
  camera.getWorldDirection(forward);
  forward.y = 0;
  if (forward.lengthSq() > 0) forward.normalize();

  const right = new THREE.Vector3();
  right.crossVectors(forward, camera.up).normalize();

  const move = new THREE.Vector3();

  if (pressedKeys.has('arrowup') || pressedKeys.has('w')) move.add(forward);
  if (pressedKeys.has('arrowdown') || pressedKeys.has('s')) move.sub(forward);
  if (pressedKeys.has('arrowright') || pressedKeys.has('d')) move.add(right);
  if (pressedKeys.has('arrowleft') || pressedKeys.has('a')) move.sub(right);
  if (pressedKeys.has('q') || pressedKeys.has('pageup')) move.y += 1;
  if (pressedKeys.has('e') || pressedKeys.has('pagedown')) move.y -= 1;

  if (move.lengthSq() === 0) return;

  move.normalize();

  const fast = pressedKeys.has('shift');
  const speed = fast ? 5.2 : 2.15;
  const step = move.multiplyScalar(speed * delta);

  camera.position.add(step);
  controls.target.add(step);
  controls.update();
}

window.addEventListener('keydown', (event) => {
  const key = event.key.toLowerCase();

  const movementKeys = [
    'arrowup', 'arrowdown', 'arrowleft', 'arrowright',
    'w', 'a', 's', 'd', 'q', 'e', 'pageup', 'pagedown', 'shift'
  ];

  if (movementKeys.includes(key)) {
    event.preventDefault();
    pressedKeys.add(key);
  }
});

window.addEventListener('keyup', (event) => {
  pressedKeys.delete(event.key.toLowerCase());
});

window.addEventListener('blur', () => {
  pressedKeys.clear();
});

function resize() {
  const width = viewerCard.clientWidth;
  const height = viewerCard.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

resetViewBtn.addEventListener('click', () => {
  if (!initialCamera) return;
  camera.position.copy(initialCamera.position);
  controls.target.copy(initialCamera.target);
  controls.update();
  syncMouseLookFromCamera();
});

toggleRotateBtn.addEventListener('click', () => {
  controls.autoRotate = !controls.autoRotate;
  toggleRotateBtn.textContent = `Auto-rotación: ${controls.autoRotate ? 'On' : 'Off'}`;
});

toggleLightsBtn.addEventListener('click', () => {
  extraLightsOn = !extraLightsOn;
  extraLights.visible = extraLightsOn;
  toggleLightsBtn.textContent = `Luces extra: ${extraLightsOn ? 'On' : 'Off'}`;
});


toggleKeyboardMoveBtn.addEventListener('click', () => {
  keyboardMoveEnabled = !keyboardMoveEnabled;
  pressedKeys.clear();
  toggleKeyboardMoveBtn.textContent = `Movimiento libre: ${keyboardMoveEnabled ? 'On' : 'Off'}`;
});

fullscreenBtn.addEventListener('click', async () => {
  if (!document.fullscreenElement) await viewerCard.requestFullscreen?.();
  else await document.exitFullscreen?.();
  resize();
});

window.addEventListener('resize', resize);
document.addEventListener('fullscreenchange', resize);

function animate() {
  requestAnimationFrame(animate);
  const delta = moveClock.getDelta();
  updateKeyboardMovement(delta);
  if (!isPointerLocked) controls.update();
  renderer.render(scene, camera);
}

resize();
animate();
loadModel();
