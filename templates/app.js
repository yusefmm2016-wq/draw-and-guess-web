// app.js
(() => {
    // #1. تهيئة Telegram WebApp
    const tg = window.Telegram?.WebApp || null;

    let currentWord = null;

    // #2. محددات DOM المُحدَّثة
    const mainCanvas = document.getElementById('mainCanvas');
    const tempCanvas = document.getElementById('tempCanvas');
    const wordBox = document.querySelector('.word');
    const btnPencil = document.getElementById('toolPencil');
    const btnEraser = document.getElementById('toolEraser');
    const btnFill = document.getElementById('toolFill');
    const btnUndo = document.getElementById('btnUndo');
    const btnRedo = document.getElementById('btnRedo');
    const btnClear = document.getElementById('btnClear');
    const btnShapes = document.getElementById('toolShapes');
    const shapeDialog = document.getElementById('shapeDialog');
    const btnCloseShapeDialog = document.getElementById('closeShapeDialog');
    const shapeOptions = document.getElementById('shapeOptions');
    const btnSend = document.getElementById('btnSend');
    const brushSizeControl = document.getElementById('brushSizeControl');
    const brushInfo = brushSizeControl?.querySelector('.brush-info');
    const brushCircle = brushSizeControl?.querySelector('div[style*="border-radius: 50%"]');
    const btnZoomIn = document.getElementById('btnZoomIn');
    const btnZoomOut = document.getElementById('btnZoomOut');
    const btnZoomReset = document.getElementById('btnZoomReset');
    const canvasContainer = document.getElementById('canvasContainer');
    const colorInput = document.getElementById('colorInput');
    const colorIconSpan = document.getElementById('colorIconSpan');
    const saveWordDialog = document.getElementById('saveWordDialog');
    const customWordInput = document.getElementById('customWordInput');
    const confirmSaveBtn = document.getElementById('confirmSaveBtn');
    const cancelSaveBtn = document.getElementById('cancelSaveBtn');
    const thicknessSlider = document.getElementById('thicknessSlider');
    const thicknessValueDisplay = document.getElementById('thicknessValueDisplay');
    const thicknessToggleBtn = document.getElementById('thicknessToggleBtn');
    const thicknessSliderContainer = document.getElementById('thicknessSliderContainer');

    let hideSliderTimeout = null;
    let isDraggingToggle = false;
    let togglePos = { x: 0, y: 0 };
    let toggleStartPos = { x: 0, y: 0 };
    let toggleMoveThreshold = 5;
    let hasMovedToggle = false;

    function showSlider() {
        if (thicknessSliderContainer) {
            thicknessSliderContainer.style.display = 'flex';
            setTimeout(() => {
                thicknessSliderContainer.style.opacity = '1';
            }, 10);
        }
        resetHideTimer();
    }

    function hideSlider() {
        if (thicknessSliderContainer) {
            thicknessSliderContainer.style.opacity = '0';
            setTimeout(() => {
                if (thicknessSliderContainer.style.opacity === '0') {
                    thicknessSliderContainer.style.display = 'none';
                }
            }, 300);
        }
    }

    function resetHideTimer() {
        if (hideSliderTimeout) clearTimeout(hideSliderTimeout);
        hideSliderTimeout = setTimeout(hideSlider, 3000);
    }

    if (thicknessToggleBtn) {
        const startToggleDrag = (e) => {
            const touch = e.touches ? e.touches[0] : e;
            isDraggingToggle = true;
            hasMovedToggle = false;
            toggleStartPos = { x: touch.clientX, y: touch.clientY };
            
            const rect = thicknessToggleBtn.getBoundingClientRect();
            togglePos = {
                offsetX: touch.clientX - rect.left,
                offsetY: touch.clientY - rect.top
            };
            
            thicknessToggleBtn.style.transition = 'none';
            e.stopPropagation();
        };

        const moveToggleDrag = (e) => {
            if (!isDraggingToggle) return;
            const touch = e.touches ? e.touches[0] : e;
            
            const dx = touch.clientX - toggleStartPos.x;
            const dy = touch.clientY - toggleStartPos.y;
            if (Math.sqrt(dx*dx + dy*dy) > toggleMoveThreshold) {
                hasMovedToggle = true;
            }

            let newX = touch.clientX - togglePos.offsetX;
            let newY = touch.clientY - togglePos.offsetY;

            // Keep within viewport
            newX = Math.max(0, Math.min(window.innerWidth - 45, newX));
            newY = Math.max(0, Math.min(window.innerHeight - 45, newY));

            thicknessToggleBtn.style.left = newX + 'px';
            thicknessToggleBtn.style.top = newY + 'px';
            thicknessToggleBtn.style.right = 'auto';
            thicknessToggleBtn.style.bottom = 'auto';
            thicknessToggleBtn.style.transform = 'none';

            // Update container position relative to toggle
            if (thicknessSliderContainer) {
                thicknessSliderContainer.style.left = (newX - 60) + 'px';
                thicknessSliderContainer.style.top = (newY + 22) + 'px';
                thicknessSliderContainer.style.right = 'auto';
                thicknessSliderContainer.style.transform = 'translateY(-50%)';
            }
            
            e.preventDefault();
            e.stopPropagation();
        };

        const stopToggleDrag = (e) => {
            if (!isDraggingToggle) return;
            isDraggingToggle = false;
            thicknessToggleBtn.style.transition = 'opacity 0.3s, transform 0.2s';
            
            if (!hasMovedToggle) {
                // It was a click, not a drag
                if (thicknessSliderContainer.style.display === 'flex' && thicknessSliderContainer.style.opacity !== '0') {
                    hideSlider();
                } else {
                    showSlider();
                }
            }
            e.stopPropagation();
        };

        thicknessToggleBtn.addEventListener('mousedown', startToggleDrag);
        window.addEventListener('mousemove', moveToggleDrag);
        window.addEventListener('mouseup', stopToggleDrag);

        thicknessToggleBtn.addEventListener('touchstart', startToggleDrag, {passive: false});
        window.addEventListener('touchmove', moveToggleDrag, {passive: false});
        window.addEventListener('touchend', stopToggleDrag, {passive: false});
    }

    if (thicknessSliderContainer) {
        thicknessSliderContainer.addEventListener('touchstart', (e) => {
            resetHideTimer();
            e.stopPropagation();
        }, {passive: true});
        thicknessSliderContainer.addEventListener('mousedown', (e) => {
            resetHideTimer();
            e.stopPropagation();
        });
    }

    if (!mainCanvas || !tempCanvas) return;

    const mainCtx = mainCanvas.getContext('2d', { alpha: false });
    const tempCtx = tempCanvas.getContext('2d', { alpha: true });

    let drawing = false;
    let tool = 'brush'; // القلم مفعل افتراضياً
    let brushSize = 10;
    const MIN_BRUSH_SIZE = 0.1;
    const MAX_BRUSH_SIZE = 45;
    let brushColor = '#000000';
    let last = { x: 0, y: 0 };
    const undoStack = [];
    const redoStack = [];
    const MAX_UNDO = 20;
    let brushOpacity = 1.0;
    let shapeStart = { x: 0, y: 0 };
    let shapeLastPos = { x: 0, y: 0 }; // Cache last move position for touchend
    let selectedShape = null;
    let currentZoom = 1.0;
    const MIN_ZOOM = 0.1;
    const MAX_ZOOM = 10.0;
    const ZOOM_STEP = 0.1;
    let isPinchZooming = false;
    let lastPinchDistance = 0;

    const SHAPE_ICON_DEFAULT = `<svg fill="currentColor" version="1.1" id="Icons" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"viewBox="0 0 32 32" xml:space="preserve"><g><path d="M22,29c-4.4,0-8-3.6-8-8s3.6-8,8-8s8,3.6,8,8S26.4,29,22,29z"/></g><path d="M12,21c0-3.5,1.8-6.5,4.4-8.3l-3-4.4C12.9,7.5,12,7,11,7S9.1,7.5,8.6,8.3l-6,8.9c-0.7,1-0.7,2.2-0.2,3.2C2.9,21.4,3.9,22,5,22h7.1C12,21.7,12,21.3,12,21z"/><path d="M25,4h-8c-1.4,0-2.5,0.9-2.9,2.1c0.4,0.3,0.7,0.6,0.9,1l3.1,4.6c1.2-0.5,2.5-0.8,3.8-0.8c2.3,0,4.3,0.8,6,2V7C28,5.3,26.7,4,25,4z"/>svg>`;
    const SHAPE_ICON_SQUARE = `<svg width="24" height="24" viewBox="0 0 15 15" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="height: 24px; width: 24px"><path fill-rule="evenodd" clip-rule="evenodd" d="M1 1H1.5H13.5H14V1.5V13.5V14H13.5H1.5H1V13.5V1.5V1ZM2 2V13H13V2H2Z" /></svg>`;
    const SHAPE_ICON_CIRCLE = `<svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="height: 24px; width: 24px"><circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="4" fill="none"/></svg>`;
    const SHAPE_ICON_TRIANGLE = `<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="miter" style="height: 24px; width: 24px"><polygon points="12 3 2.5 21 21.5 21 12 3" fill="none"></polygon></svg>`;

    function updateShapeIcon(shapeType) {
        const container = btnShapes?.querySelector('.svg');
        if (!container) return;
        let iconHtml = SHAPE_ICON_DEFAULT;
        if (shapeType === 'square') iconHtml = SHAPE_ICON_SQUARE;
        else if (shapeType === 'circle') iconHtml = SHAPE_ICON_CIRCLE;
        else if (shapeType === 'triangle') iconHtml = SHAPE_ICON_TRIANGLE;
        container.innerHTML = iconHtml;
    }

    function fixCanvas() {
        const ratio = window.devicePixelRatio || 1;
        const size = 500;
        mainCanvas.width = size * ratio;
        mainCanvas.height = size * ratio;
        mainCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
        tempCanvas.width = size * ratio;
        tempCanvas.height = size * ratio;
        tempCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
        mainCtx.fillStyle = '#ffffff';
        mainCtx.fillRect(0, 0, mainCanvas.width / ratio, mainCanvas.height / ratio);
    }

    function updateBrushIndicator(size, opacity) {
        if (brushCircle) {
            brushCircle.style.width = size + 'px';
            brushCircle.style.height = size + 'px';
            brushCircle.style.opacity = opacity;
        }
        if (brushInfo) {
            brushInfo.innerHTML = `${Math.round(size)}px<br/>${Math.round(opacity * 100)}%`;
        }
        if (thicknessSlider) {
            thicknessSlider.value = size;
        }
        if (thicknessValueDisplay) {
            thicknessValueDisplay.innerText = Math.round(size) + 'px';
        }
    }

    function pushUndo() {
        if (undoStack.length >= MAX_UNDO) undoStack.shift();
        undoStack.push(mainCanvas.toDataURL('image/png'));
        redoStack.length = 0;
    }

    function doUndo() {
        if (undoStack.length <= 1) return;
        redoStack.push(undoStack.pop());
        const data = undoStack[undoStack.length - 1];
        const i = new Image();
        i.onload = () => {
            mainCtx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
            mainCtx.drawImage(i, 0, 0, 500, 500);
            tg?.HapticFeedback?.impactOccurred('light');
        };
        i.src = data;
    }

    function doRedo() {
        if (!redoStack.length) return;
        const data = redoStack.pop();
        undoStack.push(data);
        const i = new Image();
        i.onload = () => {
            mainCtx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
            mainCtx.drawImage(i, 0, 0, 500, 500);
            tg?.HapticFeedback?.impactOccurred('light');
        };
        i.src = data;
    }

    function hexToRgb(hex) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return [r, g, b, 255];
    }

    function floodFill(startX, startY) {
        pushUndo();
        const ratio = window.devicePixelRatio || 1;
        const x = Math.round(startX * ratio);
        const y = Math.round(startY * ratio);
        const canvasWidth = mainCanvas.width;
        const canvasHeight = mainCanvas.height;
        const imgData = mainCtx.getImageData(0, 0, canvasWidth, canvasHeight);
        const data = imgData.data;
        const pixelIndex = (y * canvasWidth + x) * 4;
        const targetColor = [data[pixelIndex], data[pixelIndex+1], data[pixelIndex+2], data[pixelIndex+3]];
        const fillColor = hexToRgb(brushColor);
        if (targetColor.every((v, i) => v === fillColor[i])) return;
        const stack = [[x, y]];
        while (stack.length) {
            const [cx, cy] = stack.pop();
            if (cx < 0 || cx >= canvasWidth || cy < 0 || cy >= canvasHeight) continue;
            const i = (cy * canvasWidth + cx) * 4;
            if (data[i] === targetColor[0] && data[i+1] === targetColor[1] && data[i+2] === targetColor[2] && data[i+3] === targetColor[3]) {
                data[i] = fillColor[0]; data[i+1] = fillColor[1]; data[i+2] = fillColor[2]; data[i+3] = fillColor[3];
                stack.push([cx+1, cy], [cx-1, cy], [cx, cy+1], [cx, cy-1]);
            }
        }
        mainCtx.putImageData(imgData, 0, 0);
    }

    function getPos(e) {
        const rect = tempCanvas.getBoundingClientRect();
        let clientX, clientY;
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        return { 
            x: (clientX - rect.left) / currentZoom, 
            y: (clientY - rect.top) / currentZoom 
        };
    }

    function startDraw(e) {
        hideSlider();
        // التحقق من أن النقر تم داخل حاوية الكانفاس وليس خارجها
        if (!e.target.closest('.canvas-container') || (e.touches && e.touches.length >= 2) || isPinchZooming) return;
        
        // منع التفاعل إذا كان يتم النقر فوق شريط الأدوات (رغم أنه خارج الحاوية تقنياً)
        if (e.target.closest('.controls')) return;

        if (tool === 'fill') {
            const p = getPos(e); floodFill(p.x, p.y);
            e.preventDefault(); return;
        }
        
        drawing = true;
        if (tool === 'shape') {
            shapeStart = getPos(e);
            tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        } else {
            last = getPos(e);
            mainCtx.lineWidth = tempCtx.lineWidth = brushSize;
            mainCtx.strokeStyle = tempCtx.strokeStyle = (tool === 'eraser' ? '#ffffff' : brushColor);
            mainCtx.lineCap = 'round';
            mainCtx.lineJoin = 'round';
            mainCtx.beginPath(); mainCtx.moveTo(last.x, last.y); mainCtx.lineTo(last.x, last.y); mainCtx.stroke();
        }
        e.preventDefault();
    }

    function stopDraw(e) {
        if (!drawing) return;
        
        let p = getPos(e); 
        if (isNaN(p.x) || isNaN(p.y)) {
            p = shapeLastPos;
        }
        
        if (tool === 'shape' && selectedShape) {
            mainCtx.save();
            mainCtx.lineWidth = brushSize;
            mainCtx.strokeStyle = brushColor;
            mainCtx.lineCap = 'round';
            mainCtx.lineJoin = 'round';
            drawShape(mainCtx, shapeStart.x, shapeStart.y, p.x, p.y, selectedShape);
            mainCtx.restore();
            
            pushUndo();
        } else {
            pushUndo();
        }
        
        drawing = false;
        tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        if (e && e.cancelable) e.preventDefault();
    }

    function onMove(e) {
        if (!drawing || (e.touches && e.touches.length >= 2) || isPinchZooming) return;
        const p = getPos(e);
        if (!isNaN(p.x) && !isNaN(p.y)) {
            shapeLastPos = p;
        }
        
        mainCtx.lineWidth = tempCtx.lineWidth = brushSize;
        mainCtx.strokeStyle = tempCtx.strokeStyle = (tool === 'eraser' ? '#ffffff' : brushColor);
        mainCtx.lineCap = 'round';
        mainCtx.lineJoin = 'round';
        if (tool === 'shape') {
            tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            drawShape(tempCtx, shapeStart.x, shapeStart.y, p.x, p.y, selectedShape);
        } else {
            mainCtx.beginPath(); mainCtx.moveTo(last.x, last.y); mainCtx.lineTo(p.x, p.y); mainCtx.stroke();
            tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            tempCtx.beginPath(); tempCtx.moveTo(last.x, last.y); tempCtx.lineTo(p.x, p.y); tempCtx.stroke();
            last = p;
        }
        e.preventDefault();
    }

    function drawShape(ctx, sx, sy, ex, ey, type) {
        const w = ex - sx;
        const h = ey - sy;
        const centerX = sx + w / 2;
        const centerY = sy + h / 2;
        const radiusX = Math.abs(w / 2);
        const radiusY = Math.abs(h / 2);

        ctx.beginPath();
        switch (type) {
            case 'square':
                ctx.rect(sx, sy, w, h);
                break;
            case 'circle':
                ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
                break;
            case 'triangle':
                ctx.moveTo(centerX, sy);
                ctx.lineTo(sx, ey);
                ctx.lineTo(ex, ey);
                ctx.closePath();
                break;
            case 'line':
                ctx.moveTo(sx, sy);
                ctx.lineTo(ex, ey);
                break;
            case 'ellipse':
                ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
                break;
            case 'pentagon':
                for (let i = 0; i < 5; i++) {
                    const angle = (i * 2 * Math.PI / 5) - Math.PI / 2;
                    ctx.lineTo(centerX + radiusX * Math.cos(angle), centerY + radiusY * Math.sin(angle));
                }
                ctx.closePath();
                break;
            case 'hexagon':
                for (let i = 0; i < 6; i++) {
                    const angle = (i * 2 * Math.PI / 6) - Math.PI / 2;
                    ctx.lineTo(centerX + radiusX * Math.cos(angle), centerY + radiusY * Math.sin(angle));
                }
                ctx.closePath();
                break;
            case 'star':
                for (let i = 0; i < 10; i++) {
                    const angle = (i * Math.PI / 5) - Math.PI / 2;
                    const r = (i % 2 === 0) ? radiusX : radiusX * 0.4;
                    ctx.lineTo(centerX + r * Math.cos(angle), centerY + r * Math.sin(angle));
                }
                ctx.closePath();
                break;
            case 'arrow':
                const headlen = Math.min(20, Math.sqrt(w*w + h*h) * 0.2);
                const angle = Math.atan2(h, w);
                ctx.moveTo(sx, sy);
                ctx.lineTo(ex, ey);
                ctx.lineTo(ex - headlen * Math.cos(angle - Math.PI / 6), ey - headlen * Math.sin(angle - Math.PI / 6));
                ctx.moveTo(ex, ey);
                ctx.lineTo(ex - headlen * Math.cos(angle + Math.PI / 6), ey - headlen * Math.sin(angle + Math.PI / 6));
                break;
            case 'diamond':
                ctx.moveTo(centerX, sy);
                ctx.lineTo(ex, centerY);
                ctx.lineTo(centerX, ey);
                ctx.lineTo(sx, centerY);
                ctx.closePath();
                break;
            case 'cloud':
                ctx.moveTo(sx + radiusX * 0.4, centerY);
                ctx.bezierCurveTo(sx, centerY - radiusY, sx + radiusX * 0.8, sy, centerX, sy);
                ctx.bezierCurveTo(ex - radiusX * 0.8, sy, ex, centerY - radiusY, ex, centerY);
                ctx.bezierCurveTo(ex, ey, ex - radiusX, ey, centerX, ey);
                ctx.bezierCurveTo(sx + radiusX, ey, sx, ey, sx + radiusX * 0.4, centerY);
                break;
            case 'heart':
                ctx.moveTo(centerX, sy + radiusY * 0.4);
                ctx.bezierCurveTo(centerX, sy, sx, sy, sx, centerY);
                ctx.bezierCurveTo(sx, centerY + radiusY * 0.6, centerX, ey, centerX, ey);
                ctx.bezierCurveTo(centerX, ey, ex, centerY + radiusY * 0.6, ex, centerY);
                ctx.bezierCurveTo(ex, sy, centerX, sy, centerX, sy + radiusY * 0.4);
                break;
            case 'moon':
                ctx.arc(centerX, centerY, radiusX, 0.5 * Math.PI, 1.5 * Math.PI);
                ctx.quadraticCurveTo(centerX + radiusX * 0.5, centerY, centerX, centerY + radiusX);
                break;
            case 'cross':
                ctx.moveTo(centerX, sy); ctx.lineTo(centerX, ey);
                ctx.moveTo(sx, centerY); ctx.lineTo(ex, centerY);
                break;
            case 'bolt':
                ctx.moveTo(centerX + radiusX * 0.2, sy);
                ctx.lineTo(sx + radiusX * 0.2, centerY + radiusY * 0.1);
                ctx.lineTo(centerX, centerY + radiusY * 0.1);
                ctx.lineTo(centerX - radiusX * 0.2, ey);
                ctx.lineTo(ex - radiusX * 0.2, centerY - radiusY * 0.1);
                ctx.lineTo(centerX, centerY - radiusY * 0.1);
                ctx.closePath();
                break;
            case 'rhombus':
                ctx.moveTo(centerX, sy);
                ctx.lineTo(ex, centerY);
                ctx.lineTo(centerX, ey);
                ctx.lineTo(sx, centerY);
                ctx.closePath();
                break;
            case 'parallelogram':
                const pOffset = Math.abs(w) * 0.25 * (w > 0 ? 1 : -1);
                ctx.moveTo(sx + pOffset, sy);
                ctx.lineTo(ex, sy);
                ctx.lineTo(ex - pOffset, ey);
                ctx.lineTo(sx, ey);
                ctx.closePath();
                break;
            case 'trapezoid':
                const tOffset = Math.abs(w) * 0.2 * (w > 0 ? 1 : -1);
                ctx.moveTo(sx + tOffset, sy);
                ctx.lineTo(ex - tOffset, sy);
                ctx.lineTo(ex, ey);
                ctx.lineTo(sx, ey);
                ctx.closePath();
                break;
            case 'plus':
                const pSize = Math.min(Math.abs(w), Math.abs(h)) * 0.1;
                ctx.moveTo(centerX - pSize, sy); ctx.lineTo(centerX + pSize, sy);
                ctx.lineTo(centerX + pSize, centerY - pSize); ctx.lineTo(ex, centerY - pSize);
                ctx.lineTo(ex, centerY + pSize); ctx.lineTo(centerX + pSize, centerY + pSize);
                ctx.lineTo(centerX + pSize, ey); ctx.lineTo(centerX - pSize, ey);
                ctx.lineTo(centerX - pSize, centerY + pSize); ctx.lineTo(sx, centerY + pSize);
                ctx.lineTo(sx, centerY - pSize); ctx.lineTo(centerX - pSize, centerY - pSize);
                ctx.closePath();
                break;
            case 'X':
                const xSize = Math.min(Math.abs(w), Math.abs(h)) * 0.1;
                ctx.moveTo(sx, sy + xSize); ctx.lineTo(sx + xSize, sy);
                ctx.lineTo(centerX, centerY - xSize); ctx.lineTo(ex - xSize, sy);
                ctx.lineTo(ex, sy + xSize); ctx.lineTo(centerX + xSize, centerY);
                ctx.lineTo(ex, ey - xSize); ctx.lineTo(ex - xSize, ey);
                ctx.lineTo(centerX, centerY + xSize); ctx.lineTo(sx + xSize, ey);
                ctx.lineTo(sx, ey - xSize); ctx.lineTo(centerX - xSize, centerY);
                ctx.closePath();
                break;
            case 'ring':
                ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
                ctx.moveTo(centerX + radiusX * 0.6, centerY);
                ctx.ellipse(centerX, centerY, radiusX * 0.6, radiusY * 0.6, 0, 0, 2 * Math.PI);
                break;
            case 'leaf':
                ctx.moveTo(sx, ey);
                ctx.bezierCurveTo(sx, sy, centerX, sy, ex, sy);
                ctx.bezierCurveTo(ex, ey, centerX, ey, sx, ey);
                ctx.moveTo(sx, ey);
                ctx.lineTo(ex, sy);
                break;
            case 'drop':
                ctx.moveTo(centerX, sy);
                ctx.bezierCurveTo(sx, centerY, sx, ey, centerX, ey);
                ctx.bezierCurveTo(ex, ey, ex, centerY, centerX, sy);
                break;
            case 'pacman':
                const angleOffset = 0.2 * Math.PI;
                ctx.moveTo(centerX, centerY);
                ctx.arc(centerX, centerY, radiusX, angleOffset, 2 * Math.PI - angleOffset);
                ctx.closePath();
                break;
            case 'shield':
                ctx.moveTo(centerX, sy);
                ctx.quadraticCurveTo(ex, sy, ex, centerY);
                ctx.quadraticCurveTo(ex, ey, centerX, ey);
                ctx.quadraticCurveTo(sx, ey, sx, centerY);
                ctx.quadraticCurveTo(sx, sy, centerX, sy);
                ctx.moveTo(sx, centerY - radiusY * 0.2);
                ctx.bezierCurveTo(sx, ey, ex, ey, ex, centerY - radiusY * 0.2);
                break;
        }
        ctx.stroke();
    }

    function showSaveWordDialog() {
        if (!saveWordDialog) return;
        saveWordDialog.style.display = 'block';
        customWordInput.value = '';
        customWordInput.focus();
    }

    function sendToTelegram() {
        if (!tg) { alert('⚠️ لم يتم اكتشاف بيئة تيليجرام.'); return; }
        if (!currentWord) { showSaveWordDialog(); return; }
        const dataURL = mainCanvas.toDataURL('image/jpeg', 0.8);
        const base64Image = dataURL.replace(/^data:image\/[^;]+;base64,/, '');
        tg.MainButton.setText('جاري الرفع...').show().disable();
        fetch(`https://api.imgbb.com/1/upload?key=139076adc49c3adbfb9a56a6792a5c7a`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `image=${encodeURIComponent(base64Image)}`
        })
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                tg.sendData(`DOODLE_URL::${d.data.url}::${currentWord}`);
            } else {
                tg.showAlert('❌ فشل رفع الصورة.');
                tg.MainButton.hide();
            }
        });
    }

    function clearActiveTools() {
        btnPencil.classList.remove('active');
        btnEraser.classList.remove('active');
        btnFill.classList.remove('active');
        btnShapes.classList.remove('active');
    }

    if (confirmSaveBtn) confirmSaveBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const word = customWordInput.value.trim();
        if (!word) { tg?.showAlert('⚠️ يرجى إدخال اسم ما رسمته.'); return; }
        currentWord = word;
        saveWordDialog.style.display = 'none';
        sendToTelegram();
    });

    if (cancelSaveBtn) cancelSaveBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        saveWordDialog.style.display = 'none';
    });

    const setupTool = (el, action) => {
        if (!el) return;
        const handler = (e) => {
            e.preventDefault();
            e.stopPropagation();
            action();
        };
        el.addEventListener('click', handler);
        el.addEventListener('touchstart', handler, {passive: false});
    };

    setupTool(btnPencil, () => { tool = 'brush'; clearActiveTools(); btnPencil.classList.add('active'); });
    setupTool(btnEraser, () => { tool = 'eraser'; clearActiveTools(); btnEraser.classList.add('active'); });
    setupTool(btnFill, () => { tool = 'fill'; clearActiveTools(); btnFill.classList.add('active'); });
    setupTool(btnUndo, doUndo);
    setupTool(btnRedo, doRedo);
    setupTool(btnClear, () => { if (confirm('هل أنت متأكد من مسح اللوحة؟')) { fixCanvas(); pushUndo(); } });
    setupTool(btnShapes, () => shapeDialog.style.display = (shapeDialog.style.display === 'none' ? 'block' : 'none'));
    if (btnCloseShapeDialog) {
        setupTool(btnCloseShapeDialog, () => shapeDialog.style.display = 'none');
    }
    
    if (shapeOptions) {
        shapeOptions.addEventListener('touchstart', (e) => {
            e.stopPropagation();
        }, { passive: true });
        shapeOptions.addEventListener('touchmove', (e) => {
            e.stopPropagation();
        }, { passive: true });
        shapeOptions.addEventListener('touchend', (e) => {
            e.stopPropagation();
        }, { passive: true });
        shapeOptions.addEventListener('mousedown', (e) => {
            e.stopPropagation();
        });
        shapeOptions.addEventListener('mousemove', (e) => {
            e.stopPropagation();
        });
        shapeOptions.addEventListener('mouseup', (e) => {
            e.stopPropagation();
        });
        shapeOptions.addEventListener('wheel', (e) => {
            e.stopPropagation();
        }, { passive: false });
    }

    shapeDialog?.addEventListener('touchstart', (e) => {
        if (e.target === shapeDialog) return;
        e.stopPropagation();
    }, { passive: true });
    shapeDialog?.addEventListener('touchmove', (e) => {
        if (e.target === shapeDialog) return;
        e.stopPropagation();
    }, { passive: true });

    shapeOptions?.addEventListener('click', (e) => {
        const btn = e.target.closest('.shape-button');
        if (btn) {
            e.preventDefault();
            e.stopPropagation();
            selectedShape = btn.dataset.shape;
            tool = 'shape';
            clearActiveTools();
            btnShapes.classList.add('active');
            updateShapeIcon(selectedShape);
            shapeDialog.style.display = 'none';
        }
    });

    setupTool(btnSend, showSaveWordDialog);

    colorInput?.addEventListener('input', (e) => { brushColor = e.target.value; colorIconSpan.style.color = brushColor; });
    
    if (thicknessSlider) {
        thicknessSlider.addEventListener('input', (e) => {
            brushSize = parseInt(e.target.value);
            if (thicknessValueDisplay) thicknessValueDisplay.innerText = brushSize + 'px';
            updateBrushIndicator(brushSize, brushOpacity);
        });
    }

    setupTool(btnZoomIn, () => { currentZoom = Math.min(MAX_ZOOM, currentZoom + ZOOM_STEP); canvasContainer.style.transform = `translateX(-50%) translate(0px, 250.39px) scale(${currentZoom})`; });
    setupTool(btnZoomOut, () => { currentZoom = Math.max(MIN_ZOOM, currentZoom - ZOOM_STEP); canvasContainer.style.transform = `translateX(-50%) translate(0px, 250.39px) scale(${currentZoom})`; });
    setupTool(btnZoomReset, () => { currentZoom = 1.0; canvasContainer.style.transform = `translateX(-50%) translate(0px, 250.39px) scale(1)`; });

    brushSizeControl?.addEventListener('touchstart', (e) => {
        if (!e.touches || e.touches.length === 0) return;
        const startY = e.touches[0].clientY;
        const startSize = brushSize;
        const moveHandler = (moveEvent) => {
            if (!moveEvent.touches || moveEvent.touches.length === 0) return;
            const diff = startY - moveEvent.touches[0].clientY;
            brushSize = Math.max(MIN_BRUSH_SIZE, Math.min(MAX_BRUSH_SIZE, startSize + diff / 5));
            updateBrushIndicator(brushSize, brushOpacity);
        };
        const endHandler = () => {
            window.removeEventListener('touchmove', moveHandler);
            window.removeEventListener('touchend', endHandler);
        };
        window.addEventListener('touchmove', moveHandler);
        window.addEventListener('touchend', endHandler);
    });

    // أحداث الرسم الأساسية
    tempCanvas.addEventListener('mousedown', startDraw);
    tempCanvas.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', stopDraw);
    
    tempCanvas.addEventListener('touchstart', startDraw, { passive: false });
    tempCanvas.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', stopDraw, { passive: false });

    // التهيئة
    fixCanvas();
    pushUndo();
    
    // تفعيل القلم افتراضياً عند البدء
    clearActiveTools();
    btnPencil.classList.add('active');
    tool = 'brush';
    
    if (tg) {
        tg.ready();
        tg.expand();
    }
})();
// ==============================
// Eyedropper Tool
// ==============================
let isEyedropperActive = false;
const btnEyedropper = document.getElementById("btnEyedropper");
btnEyedropper.addEventListener("click", () => {
    isEyedropperActive = true;
    btnEyedropper.classList.add("active");
    alert("🎨 اضغط على أي لون داخل اللوحة لنسخه");
});

mainCanvas.addEventListener("click", (e) => {
    if(!isEyedropperActive) return;
    const rect = mainCanvas.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) * (mainCanvas.width / rect.width));
    const y = Math.floor((e.clientY - rect.top) * (mainCanvas.height / rect.height));
    const pixel = mainCanvas.getContext("2d").getImageData(x, y, 1, 1).data;
    const pickedColor =
        "#" +
        pixel[0].toString(16).padStart(2,"0") +
        pixel[1].toString(16).padStart(2,"0") +
        pixel[2].toString(16).padStart(2,"0");
    brushColor = pickedColor;
    isEyedropperActive = false;
    btnEyedropper.classList.remove("active");
});
