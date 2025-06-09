const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
camera.position.set(0, 2, 5);

const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Свет
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 7.5);
scene.add(light);

// Управление
const controls = new THREE.OrbitControls(camera, renderer.domElement);

// Raycasting
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let clickable = [];

// Загрузка OBJ
const loader = new THREE.OBJLoader();

loader.load('/static/models/Насос.obj', function(obj) {
    scene.add(obj);

    // Обход всех мешей
    obj.traverse(child => {
        if (child.isMesh) {
            // Например, вентиль имеет имя valve_1
            if (child.name.includes("valve")) {
                clickable.push(child);
            }
        }
    });
}, undefined, function(err) {
    console.error('Ошибка загрузки модели', err);
});

// Клик мыши
window.addEventListener('click', (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(clickable);
    if (intersects.length > 0) {
        const clicked = intersects[0].object;
        clicked.rotation.y += Math.PI / 2;
        console.log("Клик по вентилю:", clicked.name);
    }
});

// Анимация
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();
