// app.js
(() => {
    // #1. تهيئة Telegram WebApp
    const tg = window.Telegram?.WebApp || null;

    // 🎯 قائمة الكلمات المحسّنة (متنوعة وصعبة)
    const WORDS_LIST = [
        // كلمات سهلة
        "طائرة", "شجرة", "قمر", "نظارة", "حذاء",
        "طعام", "قلم", "كتاب", "كمبيوتر", "جوال",
        "قطار", "دراجة", "منزل", "سيارة", "قارب",
        "شمس", "نجمة", "وردة", "سمكة", "قطة",
        // كلمات متوسطة
        "أسد", "فيل", "حصان", "طائر", "أرنب",
        "تفاحة", "موزة", "برتقالة", "فراولة", "عنب",
        "كرة", "لعبة", "دمية", "بحر", "جبل",
        "صحراء", "غابة", "مدينة", "جسر", "مطار",
        // كلمات صعبة
        "فيلسوف", "عالم", "مخترع", "مكتشف", "رحالة",
        "قصر", "قلعة", "معبد", "مسجد", "كنيسة",
        "صاروخ", "قمر صناعي", "محطة فضاء", "مركبة فضائية", "كوكب",
        "بركان", "زلزال", "إعصار", "فيضان", "جفاف",
        "موسيقي", "رسام", "شاعر", "كاتب", "ممثل",
        "مختبر", "مكتبة", "متحف", "جامعة", "مدرسة",
        "ميكروسكوب", "تلسكوب", "كاميرا", "هاتف ذكي", "كمبيوتر محمول",
        "روبوت", "ذكاء اصطناعي", "إنترنت", "شبكة", "سحابة",
        "طاقة شمسية", "طاقة متجددة", "بيئة", "تلوث", "حماية",
        "ديمقراطية", "حرية", "عدالة", "مساواة", "سلام",
    ];
    let usedWords = [];
    let aiWord = null;

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
    const shapeOptions = document.getElementById('shapeOptions');
    const shapeIconContainer = btnShapes?.querySelector('.svg');
    const btnSend = document.getElementById('btnSend');
    const brushSizeControl = document.getElementById('brushSizeControl');
    const brushInfo = brushSizeControl?.querySelector('.brush-info');
    const brushCircle = brushSizeControl?.querySelector('div[style*="border-radius: 50%"]');
    // ✅ إضافة محددات DOM للزوم وحجم الخط
    const btnZoomIn = document.getElementById('btnZoomIn');
    const btnZoomOut = document.getElementById('btnZoomOut');
    const btnZoomReset = document.getElementById('btnZoomReset');
    const btnFontSize = document.getElementById('btnFontSize');
    const canvasContainer = document.getElementById('canvasContainer');
    const wordDisplay = document.getElementById('wordDisplay');

    // 🎨 المدخل الجديد لزر الألوان
    const colorInput = document.getElementById('colorInput');
    const colorIconSpan = document.getElementById('colorIconSpan');

    // 🎯 محددات DOM لمربع حوار الكلمات
    const wordDialog = document.getElementById('wordDialog');
    const wordOptionsContainer = document.getElementById('wordOptions');


    // التأكد من وجود اللوحات
    if (!mainCanvas || !tempCanvas) {
        console.error('Canvas elements not found! Please ensure mainCanvas and tempCanvas have the correct ID.');
        return;
    }

    const mainCtx = mainCanvas.getContext('2d', { alpha: false });
    const tempCtx = tempCanvas.getContext('2d', { alpha: true });

    // #3. State
    let drawing = false;
    let tool = 'brush';
    let brushSize = 10;
    const MIN_BRUSH_SIZE = 0.1; // ✅ الحد الأدنى للفرشاة: 0.1px
    const MAX_BRUSH_SIZE = 45;
    let brushColor = '#000000';
    let last = { x: 0, y: 0 };
    const undoStack = [];
    const redoStack = [];
    const MAX_UNDO = 20;
    let brushOpacity = 1.0;
    let shapeStart = { x: 0, y: 0 };
    let selectedShape = null;
    let currentWord = null;
    // ✅ إضافة متغيرات الزوم وحجم الخط
    let currentZoom = 1.0;
    const MIN_ZOOM = 0.1; // زوم لا نهائي (يمكن التصغير حتى 0.1)
    const MAX_ZOOM = 10.0; // زوم لا نهائي (يمكن التكبير حتى 10x)
    const ZOOM_STEP = 0.1;
    let currentFontSize = 18; // حجم الخط الافتراضي
    const MIN_FONT_SIZE = 10;
    const MAX_FONT_SIZE = 50;
    let isPinchZooming = false;
    let lastPinchDistance = 0;

    const SHAPE_ICON_DEFAULT = `<svg fill="currentColor" version="1.1" id="Icons" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"viewBox="0 0 32 32" xml:space="preserve"><g><path d="M22,29c-4.4,0-8-3.6-8-8s3.6-8,8-8s8,3.6,8,8S26.4,29,22,29z"/></g><path d="M12,21c0-3.5,1.8-6.5,4.4-8.3l-3-4.4C12.9,7.5,12,7,11,7S9.1,7.5,8.6,8.3l-6,8.9c-0.7,1-0.7,2.2-0.2,3.2C2.9,21.4,3.9,22,5,22h7.1C12,21.7,12,21.3,12,21z"/><path d="M25,4h-8c-1.4,0-2.5,0.9-2.9,2.1c0.4,0.3,0.7,0.6,0.9,1l3.1,4.6c1.2-0.5,2.5-0.8,3.8-0.8c2.3,0,4.3,0.8,6,2V7C28,5.3,26.7,4,25,4z"/>svg>`;
    const SHAPE_ICON_SQUARE = `<svg width="24" height="24" viewBox="0 0 15 15" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="height: 24px; width: 24px"><path fill-rule="evenodd" clip-rule="evenodd" d="M1 1H1.5H13.5H14V1.5V13.5V14H13.5H1.5H1V13.5V1.5V1ZM2 2V13H13V2H2Z" /></svg>`;
    const SHAPE_ICON_CIRCLE = `<svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="height: 24px; width: 24px"><circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="4" fill="none"/></svg>`;
    const SHAPE_ICON_TRIANGLE = `<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="miter" style="height: 24px; width: 24px"><polygon points="12 3 2.5 21 21.5 21 12 3" fill="none"></polygon></svg>`;

    function updateShapeIcon(shapeType) {
        const shapeIconContainer = btnShapes?.querySelector('.svg');
        if (!shapeIconContainer) return;

        let iconHtml = SHAPE_ICON_DEFAULT;
        if (shapeType === 'square') iconHtml = SHAPE_ICON_SQUARE;
        else if (shapeType === 'circle') iconHtml = SHAPE_ICON_CIRCLE;
        else if (shapeType === 'triangle') iconHtml = SHAPE_ICON_TRIANGLE;

        shapeIconContainer.innerHTML = iconHtml;
    }


    // ****************************
    // #4. وظائف الدعم
    // ****************************

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
        const opacityPercent = Math.round(opacity * 100);
        if (brushCircle) {
            // ✅ إصلاح: الحد الأدنى 5px للعرض المرئي
            const displaySize = Math.max(5, Math.min(40, size));
            brushCircle.style.width = displaySize + 'px';
            brushCircle.style.height = displaySize + 'px';
            brushCircle.style.opacity = opacity;
        }
        if (brushInfo) {
            // ✅ إصلاح: عرض القيمة بدقة (حتى 0.1px)
            const sizeDisplay = size < 1 ? size.toFixed(1) : Math.round(size);
            brushInfo.innerHTML = `${sizeDisplay}px<br/>${opacityPercent}%`;
        }
    }
    function pushUndo() {
        try {
            // ✅ إصلاح: حفظ الحالة الحالية قبل أي تغيير
            const currentState = mainCanvas.toDataURL('image/png');
            if (undoStack.length >= MAX_UNDO) {
                undoStack.shift(); // إزالة أقدم حالة
            }
            undoStack.push(currentState);
            redoStack.length = 0; // مسح redo عند عمل جديد
        } catch (e) { 
            console.warn('undo push failed', e); 
        }
    }
    function doUndo() {
        // ✅ إصلاح: يجب أن يكون هناك على الأقل خطوتين للرجوع
        if (undoStack.length <= 1) {
            tg?.HapticFeedback?.impactOccurred('light');
            return;
        }
        // حفظ الحالة الحالية في redo
        const currentState = mainCanvas.toDataURL('image/png');
        redoStack.push(currentState);
        // إزالة الحالة الحالية من undo
        undoStack.pop();
        // تطبيق الحالة السابقة
        if (undoStack.length > 0) {
            const dataToApply = undoStack[undoStack.length - 1];
            const i = new Image();
            i.onload = () => {
                mainCtx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
                mainCtx.drawImage(i, 0, 0, mainCanvas.width / (window.devicePixelRatio || 1), mainCanvas.height / (window.devicePixelRatio || 1));
                tg?.HapticFeedback?.impactOccurred('light');
            };
            i.onerror = () => {
                console.error('Failed to load undo image');
            };
            i.src = dataToApply;
        }
    }
    function doRedo() {
        if (!redoStack.length) {
            tg?.HapticFeedback?.impactOccurred('light');
            return;
        }
        // حفظ الحالة الحالية في undo
        const currentState = mainCanvas.toDataURL('image/png');
        undoStack.push(currentState);
        // تطبيق الحالة من redo
        const data = redoStack.pop();
        const i = new Image();
        i.onload = () => {
            mainCtx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
            mainCtx.drawImage(i, 0, 0, mainCanvas.width / (window.devicePixelRatio || 1), mainCanvas.height / (window.devicePixelRatio || 1));
            tg?.HapticFeedback?.impactOccurred('light');
        };
        i.onerror = () => {
            console.error('Failed to load redo image');
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
        const ctx = mainCtx;
        const canvasWidth = mainCanvas.width;
        const canvasHeight = mainCanvas.height;
        if (x < 0 || x >= canvasWidth || y < 0 || y >= canvasHeight) return;
        const imgData = ctx.getImageData(0, 0, canvasWidth, canvasHeight);
        const data = imgData.data;
        const pixelIndex = (y * canvasWidth + x) * 4;
        const targetColor = [
            data[pixelIndex],
            data[pixelIndex + 1],
            data[pixelIndex + 2],
            data[pixelIndex + 3]
        ];
        const fillColor = hexToRgb(brushColor);
        if (targetColor.every((val, i) => val === fillColor[i])) return;
        const stack = [[x, y]];

        function getPixelColor(px, py) {
            const i = (py * canvasWidth + px) * 4;
            if (i < 0 || i + 3 >= data.length) return [0, 0, 0, 0];
            return [data[i], data[i + 1], data[i + 2], data[i + 3]];
        }
        function setPixelColor(px, py) {
            const i = (py * canvasWidth + px) * 4;
            data[i] = fillColor[0];
            data[i + 1] = fillColor[1];
            data[i + 2] = fillColor[2];
            data[i + 3] = fillColor[3];
        }
        function colorsMatch(c1, c2) {
            return c1[0] === c2[0] && c1[1] === c2[1] && c1[2] === c2[2] && c1[3] === c2[3];
        }
        while (stack.length) {
            const [cx, cy] = stack.pop();
            if (cx < 0 || cx >= canvasWidth || cy < 0 || cy >= canvasHeight) continue;
            const currentColor = getPixelColor(cx, cy);
            if (colorsMatch(currentColor, targetColor)) {
                setPixelColor(cx, cy);
                stack.push([cx + 1, cy]);
                stack.push([cx - 1, cy]);
                stack.push([cx, cy + 1]);
                stack.push([cx, cy - 1]);
            }
        }
        ctx.putImageData(imgData, 0, 0);
    }
    
    // 🎯 الجديد: اختيار N كلمة عشوائية
    function getRandomWords(list, count) {
        const shuffled = list.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count);
    }

    // 🎯 الجديد: دالة لإنشاء أزرار الكلمات ديناميكياً (بشكل يشبه تصميم الأشكال)
    function generateWordButtons(words) {
        if (!wordOptionsContainer) return;
        wordOptionsContainer.innerHTML = '';
        
        words.forEach(word => {
            const buttonHtml = `
                <div class="word-button" data-word="${word}" style="cursor: pointer;">
                    <div class="word-switch" style="
                        width: 80px; 
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 8px;
                        background-color: var(--tg-theme-button-color, #40a7e3);
                        color: var(--tg-theme-button-text-color, #ffffff);
                        font-weight: bold;
                        font-size: 14px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        transition: background-color 0.15s;
                    ">
                        ${word}
                    </div>
                </div>
            `;
            wordOptionsContainer.insertAdjacentHTML('beforeend', buttonHtml);
        });
    }

    // ****************************
    // #5. وظائف الرسم (لم تتغير)
    // ****************************
    function getPos(e) {
        const rect = tempCanvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        // ✅ إصلاح: حساب الموضع بناءً على الزوم الحالي
        // بعد الزوم، يجب حساب الموضع بناءً على scale الحالي
        const x = (clientX - rect.left) / currentZoom;
        const y = (clientY - rect.top) / currentZoom;
        return { x, y };
    }
    function startDraw(e) {
        if (!e.target.closest('.canvas-container')) return;
        // ✅ منع الرسم عند الزوم بإصبعين
        if (e.touches && e.touches.length >= 2) {
            return; // لا ترسم عندما يكون هناك إصبعين أو أكثر
        }
        if (isPinchZooming) {
            return; // لا ترسم أثناء الزوم
        }
        if (tool === 'fill') {
            const pos = getPos(e);
            floodFill(pos.x, pos.y);
            e.preventDefault();
            return;
        }
        if (tool === 'shape') {
            drawing = true;
            shapeStart = getPos(e);
            tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            e.preventDefault();
            return;
        }
        drawing = true;
        last = getPos(e);
        const mainContext = mainCtx;
        const tempContext = tempCtx;
        mainContext.lineCap = 'round';
        mainContext.lineJoin = 'round';
        // ✅ إصلاح: استخدام الحد الأدنى 0.1px
        mainContext.lineWidth = Math.max(MIN_BRUSH_SIZE, brushSize);
        mainContext.globalAlpha = brushOpacity;
        tempContext.lineCap = 'round';
        tempContext.lineJoin = 'round';
        tempContext.lineWidth = Math.max(MIN_BRUSH_SIZE, brushSize);
        tempContext.globalAlpha = brushOpacity;
        if (tool === 'eraser') {
            mainContext.globalCompositeOperation = 'source-over';
            mainContext.strokeStyle = '#ffffff';
            mainContext.beginPath();
            mainContext.moveTo(last.x, last.y);
            mainContext.lineTo(last.x, last.y);
            mainContext.stroke();
            tempContext.globalCompositeOperation = 'source-over';
            tempContext.strokeStyle = '#ffffff';
            tempContext.beginPath();
            tempContext.moveTo(last.x, last.y);
            tempContext.lineTo(last.x, last.y);
            tempContext.stroke();
        }
        else if (tool === 'brush') {
            mainContext.globalCompositeOperation = 'source-over';
            mainContext.strokeStyle = brushColor;
            mainContext.beginPath();
            mainContext.moveTo(last.x, last.y);
            mainContext.lineTo(last.x, last.y);
            mainContext.stroke();
            tempContext.globalCompositeOperation = 'source-over';
            tempContext.strokeStyle = brushColor;
            tempContext.beginPath();
            tempContext.moveTo(last.x, last.y);
            tempContext.lineTo(last.x, last.y);
            tempContext.stroke();
        }
        mainContext.globalCompositeOperation = 'source-over';
        mainContext.globalAlpha = 1.0;
        tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        e.preventDefault();
    }
    function stopDraw(e) {
        if (!drawing) return;
        if (tool === 'shape') {
            drawing = false;
            const p = getPos(e);
            // ✅ إصلاح: حفظ الحالة قبل رسم الشكل
            pushUndo();
            drawShape(mainCtx, shapeStart.x, shapeStart.y, p.x, p.y, selectedShape);
            tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            // ✅ إبقاء وضع الأشكال نشطاً للسماح بإضافة أشكال أخرى
            // tool يبقى 'shape' للسماح بإضافة المزيد من الأشكال
            e && e.preventDefault();
            return;
        }
        drawing = false;
        // ✅ إصلاح: حفظ الحالة عند انتهاء الرسم
        pushUndo();
        tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        e && e.preventDefault();
    }
    function onMove(e) {
        if (!drawing) return;
        // ✅ منع الرسم عند الزوم بإصبعين
        if (e.touches && e.touches.length >= 2) {
            drawing = false;
            return;
        }
        if (isPinchZooming) {
            drawing = false;
            return;
        }
        const p = getPos(e);
        if (tool === 'shape') {
            tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            drawShape(tempCtx, shapeStart.x, shapeStart.y, p.x, p.y, selectedShape);
            e.preventDefault();
            return;
        }
        tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        const mainContext = mainCtx;
        mainContext.lineCap = 'round';
        mainContext.lineJoin = 'round';
        mainContext.lineWidth = brushSize;
        mainContext.globalAlpha = brushOpacity;
        if (tool === 'eraser') {
            mainContext.globalCompositeOperation = 'source-over';
            mainContext.strokeStyle = '#ffffff';
        } else {
            mainContext.globalCompositeOperation = 'source-over';
            mainContext.strokeStyle = brushColor;
        }
        mainContext.beginPath();
        mainContext.moveTo(last.x, last.y);
        mainContext.lineTo(p.x, p.y);
        mainContext.stroke();
        const tempContext = tempCtx;
        tempContext.lineCap = 'round';
        tempContext.lineJoin = 'round';
        tempContext.lineWidth = brushSize;
        tempContext.globalAlpha = brushOpacity;
        tempContext.globalCompositeOperation = 'source-over';
        tempContext.strokeStyle = (tool === 'eraser') ? '#ffffff' : brushColor;
        tempContext.beginPath();
        tempContext.moveTo(last.x, last.y);
        tempContext.lineTo(p.x, p.y);
        tempContext.stroke();
        mainContext.globalAlpha = 1.0;
        mainContext.globalCompositeOperation = 'source-over';
        last = p;
        e.preventDefault();
    }
    function drawShape(ctx, startX, startY, endX, endY, shapeType) {
        const width = endX - startX;
        const height = endY - startY;
        ctx.lineCap = 'butt';
        ctx.lineJoin = 'miter';
        ctx.lineWidth = Math.max(MIN_BRUSH_SIZE, brushSize);
        ctx.strokeStyle = brushColor;
        ctx.globalAlpha = brushOpacity;
        ctx.beginPath();
        if (shapeType === 'square') {
            ctx.rect(startX, startY, width, height);
        } else if (shapeType === 'circle') {
            const radiusX = Math.abs(width) / 2;
            const radiusY = Math.abs(height) / 2;
            const centerX = startX + width / 2;
            const centerY = startY + height / 2;
            ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
        } else if (shapeType === 'triangle') {
            ctx.moveTo(startX + width / 2, startY);
            ctx.lineTo(startX, startY + height);
            ctx.lineTo(startX + width, startY + height);
            ctx.closePath();
        }
        ctx.stroke();
        ctx.globalAlpha = 1.0;
    }

// 🎯 الجديد: دالة لإنشاء أزرار الكلمات ديناميكياً
    function generateWordButtons(words) {
        if (!wordOptionsContainer) return;
        wordOptionsContainer.innerHTML = '';
        
        words.forEach(word => {
             // ... (HTML لأزرار الكلمات لم يتغير) ...
            const buttonHtml = `
                <div class="word-button" data-word="${word}" style="cursor: pointer; margin: 5px;">
                    <div class="word-switch" style="
                        width: 90px; 
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 8px;
                        background-color: var(--tg-theme-button-color, #40a7e3);
                        color: var(--tg-theme-button-text-color, #ffffff);
                        font-weight: bold;
                        font-size: 14px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        transition: background-color 0.15s;
                    ">
                        ${word}
                    </div>
                </div>
            `;
            wordOptionsContainer.insertAdjacentHTML('beforeend', buttonHtml);
        });
    }

    // 🎯 الجديد: جلب كلمات عشوائية مع تجنب التكرار (قدر الإمكان)
    function getRandomWordsAvoidUsed(list, count) {
        const availableWords = list.filter(word => !usedWords.includes(word));
        
        // إذا استُهلكت جميع الكلمات، يتم إعادة تعيين القائمة
        if (availableWords.length < count) {
            usedWords = []; // إعادة تعيين القائمة المستعملة
            const shuffled = list.sort(() => 0.5 - Math.random());
            return shuffled.slice(0, count);
        }
        
        const shuffled = availableWords.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count);
    }


    // ****************************
    // #6. وظيفة الإرسال إلى Telegram (لم تتغير)
    // ****************************
function sendToTelegram() {
    // ⚠️ نستخدم 'tg' المعرف في النطاق الخارجي (الجزء #1)
    const telegramApp = window.Telegram?.WebApp || null;
    if (!tg) { 
        alert('⚠️ لم يتم اكتشاف بيئة تيليجرام.');
        return;
    }

    if (!currentWord) {
            tg.showAlert('⚠️ يجب اختيار كلمة للرسم أولاً.');
            return;
        }
    
    // منع النقر المزدوج أثناء الرفع
    btnSend.removeEventListener('click', sendToTelegram);

    // مفتاح API الخاص بك من ImgBB
    const IMGBB_API_KEY = "139076adc49c3adbfb9a56a6792a5c7a";
    
    // 1. استخراج الصورة من mainCanvas
    const dataURL = mainCanvas.toDataURL('image/jpeg', 0.8);
    const base64Image = dataURL.replace(/^data:image\/[^;]+;base64,/, '');

    // 2. إظهار حالة التحميل
    tg.MainButton.setText('جاري الرفع...').show().disable();
    tg.HapticFeedback?.impactOccurred('medium');

    // 3. رفع الصورة إلى ImgBB
    fetch(`https://api.imgbb.com/1/upload?key=${IMGBB_API_KEY}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `image=${encodeURIComponent(base64Image)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const imageUrl = data.data.url;
            
            // 4. إرسال رابط الصورة باستخدام البادئة المتوقعة من البوت
            const MESSAGE_PREFIX = "DOODLE_URL::"; 
            const messageToSend = `${MESSAGE_PREFIX}${imageUrl}::${currentWord}`;
            tg.sendData(messageToSend);
            
            tg.showAlert('✅ تم إرسال الرابط بنجاح إلى البوت!');
            
        } else {
            tg.showAlert('❌ فشل الرفع إلى ImgBB: ' + (data.error?.message || 'خطأ غير معروف.'));
        }
    })
    .catch(error => {
        tg.showAlert('❌ خطأ في الاتصال بالخادم (ImgBB): ' + error.message);
        console.error("Fetch Error:", error);
    })
    .finally(() => {
        // إعادة تفعيل الزر وإخفاء زر Telegram
        tg.MainButton.hide();
        btnSend.addEventListener('click', sendToTelegram); // إعادة معالج الحدث
    });
}


    // ****************************
    // #7. معالجات الأحداث (ربط أدوات التحكم)
    // ****************************

    tempCanvas.addEventListener('mousedown', startDraw);
    tempCanvas.addEventListener('touchstart', startDraw, { passive: false });
    window.addEventListener('mouseup', stopDraw);
    window.addEventListener('touchend', stopDraw, { passive: false });
    tempCanvas.addEventListener('mousemove', onMove);
    tempCanvas.addEventListener('touchmove', onMove, { passive: false });

    if (btnPencil) {
        btnPencil.addEventListener('click', () => {
            tool = 'brush';
            btnPencil.querySelector('.circle-switch').classList.add('active');
            btnEraser?.classList.remove('active');
            btnFill?.classList.remove('active');
            btnShapes?.classList.remove('active');
            selectedShape = null;
            updateShapeIcon(selectedShape);
        });
    }
    if (btnEraser) {
        btnEraser.addEventListener('click', () => {
            tool = 'eraser';
            btnEraser.classList.add('active');
            btnPencil?.querySelector('.circle-switch').classList.remove('active');
            btnFill?.classList.remove('active');
            btnShapes?.classList.remove('active');
            selectedShape = null;
            updateShapeIcon(selectedShape);
        });
    }
    if (btnFill) {
        btnFill.addEventListener('click', () => {
            tool = 'fill';
            btnFill.classList.add('active');
            btnPencil?.querySelector('.circle-switch').classList.remove('active');
            btnEraser?.classList.remove('active');
            btnShapes?.classList.remove('active');
            selectedShape = null;
            updateShapeIcon(selectedShape);
        });
    }
    if (btnUndo) btnUndo.addEventListener('click', () => doUndo());
    if (btnRedo) btnRedo.addEventListener('click', () => doRedo());
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            pushUndo();
            mainCtx.fillStyle = '#ffffff';
            mainCtx.fillRect(0, 0, mainCanvas.width / (window.devicePixelRatio || 1), mainCanvas.height / (window.devicePixelRatio || 1));
        });
    }
    // ✅ إعادة برمجة زر الأشكال بالكامل - 3 أشكال فقط (دائرة، مربع، مثلث)
    if (btnShapes) {
        btnShapes.addEventListener('click', () => {
            // ✅ إبقاء وضع الأشكال نشطاً بعد اختيار شكل
            if (selectedShape) {
                // إذا كان هناك شكل محدد، نبقيه نشطاً
                tool = 'shape';
                btnShapes.classList.add('active');
                btnPencil?.querySelector('.circle-switch').classList.remove('active');
                btnEraser?.classList.remove('active');
                btnFill?.classList.remove('active');
            } else {
                // إذا لم يكن هناك شكل محدد، نفتح مربع الحوار
                if (shapeDialog) {
                    shapeDialog.style.display = 'block';
                }
            }
        });
    }
    if (shapeOptions) {
        shapeOptions.addEventListener('click', (e) => {
            const shapeButton = e.target.closest('.shape-button');
            if (shapeButton) {
                const newShape = shapeButton.getAttribute('data-shape');
                // ✅ إصلاح: تعيين الشكل و tool
                selectedShape = newShape;
                tool = 'shape';
                updateShapeIcon(newShape);
                // ✅ إغلاق مربع الحوار
                if (shapeDialog) {
                    shapeDialog.style.display = 'none';
                }
                // ✅ تفعيل زر الأشكال
                btnShapes?.classList.add('active');
                btnPencil?.querySelector('.circle-switch').classList.remove('active');
                btnEraser?.classList.remove('active');
                btnFill?.classList.remove('active');
                // ✅ إبقاء tool = 'shape' للسماح بإضافة أشكال متعددة
            }
        });
    }

    if (wordBox) {
        wordBox.addEventListener('click', () => {
            if (wordDialog) {
                // ✅ تقليل عدد الكلمات المعروضة إلى 4 فقط
                const randomWords = getRandomWordsAvoidUsed(WORDS_LIST, 4);
                generateWordButtons(randomWords);
                wordDialog.style.display = 'block';
            }
        });
    }

    // 🎯 منطق اختيار الكلمة
    if (wordOptionsContainer) {
        wordOptionsContainer.addEventListener('click', (e) => {
            const wordButton = e.target.closest('.word-button');
            if (wordButton) {
                const newWord = wordButton.getAttribute('data-word');
                currentWord = newWord;
                
                // إضافة الكلمة إلى قائمة الكلمات المستعملة
                if (!usedWords.includes(newWord)) {
                    usedWords.push(newWord);
                }

                if (wordBox) {
                    wordBox.innerHTML = `${currentWord}`;
                    wordBox.style.display = 'block';
                }

                if (wordDialog) {
                    wordDialog.style.display = 'none';
                }

                pushUndo();
                mainCtx.fillStyle = '#ffffff';
                mainCtx.fillRect(0, 0, mainCanvas.width / (window.devicePixelRatio || 1), mainCanvas.height / (window.devicePixelRatio || 1));

                tg?.HapticFeedback?.notificationOccurred('success');
            }
        });
    }

    // إخفاء مربعات الحوار عند بدء الرسم
    tempCanvas.addEventListener('mousedown', () => {
        if (shapeDialog && shapeDialog.style.display !== 'none' && tool !== 'shape') {
            shapeDialog.style.display = 'none';
            btnShapes?.classList.remove('active');
            // ✅ إصلاح: لا نعيد tool إلى 'brush' إذا كان المستخدم يريد إضافة أشكال متعددة
            // tool = 'brush'; // تم إزالة هذا السطر للسماح بإضافة أشكال متعددة
        }
        if (wordDialog && wordDialog.style.display !== 'none') {
            wordDialog.style.display = 'none';
        }
    });

    if (btnSend) btnSend.addEventListener('click', sendToTelegram);
    if (colorInput) {
        colorInput.addEventListener('input', (e) => {
            brushColor = e.target.value;
            if (brushCircle) {
                brushCircle.style.background = brushColor;
            }
            if (colorIconSpan) {
                colorIconSpan.style.color = brushColor;
            }
        });
    }
    
    // ✅ إضافة معالجات أحداث الزوم
    function updateZoom() {
        if (canvasContainer) {
            const currentTransform = canvasContainer.style.transform.match(/translateX\(-50%\)\s+translate\(([^)]+)\)\s+scale\(([^)]+)\)/);
            const translate = currentTransform ? currentTransform[1] : '0px, 250.39px';
            canvasContainer.style.transform = `translateX(-50%) translate(${translate}) scale(${currentZoom})`;
        }
    }
    
    // ✅ دالة حساب المسافة بين إصبعين
    function getPinchDistance(e) {
        if (e.touches && e.touches.length === 2) {
            const touch1 = e.touches[0];
            const touch2 = e.touches[1];
            const dx = touch2.clientX - touch1.clientX;
            const dy = touch2.clientY - touch1.clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }
        return 0;
    }
    
    // ✅ معالج pinch-to-zoom
    canvasContainer?.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
            isPinchZooming = true;
            lastPinchDistance = getPinchDistance(e);
            drawing = false; // إيقاف الرسم فوراً عند لمس إصبعين
            e.preventDefault();
        } else if (e.touches.length === 1 && !isPinchZooming) {
            // السماح بالرسم فقط عند إصبع واحد وليس أثناء الزوم
            isPinchZooming = false;
        }
    }, { passive: false });
    
    canvasContainer?.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2) {
            isPinchZooming = true;
            drawing = false; // منع الرسم عند لمس إصبعين
            const currentDistance = getPinchDistance(e);
            if (lastPinchDistance > 0) {
                const scaleChange = currentDistance / lastPinchDistance;
                currentZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, currentZoom * scaleChange));
                updateZoom();
            }
            lastPinchDistance = currentDistance;
            e.preventDefault();
        } else if (e.touches.length === 1 && isPinchZooming) {
            // إذا أصبح إصبع واحد فقط بعد الزوم، نوقف الزوم
            isPinchZooming = false;
            lastPinchDistance = 0;
        }
    }, { passive: false });
    
    canvasContainer?.addEventListener('touchend', (e) => {
        if (e.touches.length < 2) {
            // إيقاف الزوم عند فك أحد الإصبعين
            isPinchZooming = false;
            lastPinchDistance = 0;
            drawing = false; // إيقاف الرسم الحالي
        }
    }, { passive: false });
    
    if (btnZoomIn) {
        btnZoomIn.addEventListener('click', () => {
            if (currentZoom < MAX_ZOOM) {
                currentZoom = Math.min(MAX_ZOOM, currentZoom + ZOOM_STEP);
                updateZoom();
                tg?.HapticFeedback?.impactOccurred('light');
            }
        });
    }
    
    if (btnZoomOut) {
        btnZoomOut.addEventListener('click', () => {
            if (currentZoom > MIN_ZOOM) {
                currentZoom = Math.max(MIN_ZOOM, currentZoom - ZOOM_STEP);
                updateZoom();
                tg?.HapticFeedback?.impactOccurred('light');
            }
        });
    }
    
    if (btnZoomReset) {
        btnZoomReset.addEventListener('click', () => {
            currentZoom = 1.0;
            updateZoom();
            tg?.HapticFeedback?.impactOccurred('medium');
        });
    }
    
    // ✅ إنشاء نافذة شريط حجم الخط
    const fontSizeDialog = document.createElement('div');
    fontSizeDialog.id = 'fontSizeDialog';
    fontSizeDialog.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10000;
        background-color: var(--tg-theme-secondary-bg-color, #f1f1f1);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        display: none;
        text-align: center;
        min-width: 250px;
    `;
    fontSizeDialog.innerHTML = `
        <h3 style="color: var(--tg-theme-text-color, #000); margin-top: 0; margin-bottom: 20px;">تغيير حجم الخط</h3>
        <input type="range" id="fontSizeSlider" min="${MIN_FONT_SIZE}" max="${MAX_FONT_SIZE}" value="${currentFontSize}" 
               style="width: 100%; height: 8px; margin: 20px 0;">
        <div id="fontSizeValue" style="color: var(--tg-theme-text-color, #000); font-size: 18px; margin: 10px 0;">
            ${currentFontSize}px
        </div>
        <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px;">
            <button id="fontSizeCancel" style="
                background-color: var(--tg-theme-hint-color, #999);
                color: var(--tg-theme-button-text-color, #fff);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                cursor: pointer;
            ">إلغاء</button>
            <button id="fontSizeConfirm" style="
                background-color: var(--tg-theme-button-color, #40a7e3);
                color: var(--tg-theme-button-text-color, #fff);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                cursor: pointer;
            ">موافق</button>
        </div>
    `;
    document.body.appendChild(fontSizeDialog);
    
    const fontSizeSlider = document.getElementById('fontSizeSlider');
    const fontSizeValue = document.getElementById('fontSizeValue');
    const fontSizeConfirm = document.getElementById('fontSizeConfirm');
    const fontSizeCancel = document.getElementById('fontSizeCancel');
    
    // ✅ معالج تغيير حجم الخط
    if (btnFontSize) {
        btnFontSize.addEventListener('click', () => {
            fontSizeSlider.value = currentFontSize;
            fontSizeValue.textContent = `${currentFontSize}px`;
            fontSizeDialog.style.display = 'block';
            tg?.HapticFeedback?.impactOccurred('light');
        });
    }
    
    if (fontSizeSlider) {
        fontSizeSlider.addEventListener('input', (e) => {
            const newSize = parseInt(e.target.value);
            fontSizeValue.textContent = `${newSize}px`;
            if (wordDisplay) {
                wordDisplay.style.fontSize = `${newSize}px`;
            }
        });
    }
    
    if (fontSizeConfirm) {
        fontSizeConfirm.addEventListener('click', () => {
            currentFontSize = parseInt(fontSizeSlider.value);
            // ✅ تحديث حجم الخط للكلمة المعروضة
            if (wordDisplay) {
                wordDisplay.style.fontSize = `${currentFontSize}px`;
                // ✅ حفظ حجم الخط في localStorage
                localStorage.setItem('drawAndGuessFontSize', currentFontSize.toString());
            }
            // ✅ ربط حجم الخط بحجم الفرشاة (خط الرسم)
            // حجم الخط يؤثر على عرض الخط عند الرسم
            // يمكن ربطه بـ brushSize أو استخدامه مباشرة
            // سنربطه بـ brushSize: كلما زاد حجم الخط، يزيد حجم الفرشاة قليلاً
            const minBrushSize = 5;
            const maxBrushSize = 45;
            const fontSizeToBrushRatio = 0.8; // نسبة تحويل حجم الخط لحجم الفرشاة
            const suggestedBrushSize = Math.max(minBrushSize, Math.min(maxBrushSize, currentFontSize * fontSizeToBrushRatio));
            brushSize = suggestedBrushSize;
            updateBrushIndicator(brushSize, brushOpacity);
            fontSizeDialog.style.display = 'none';
            tg?.HapticFeedback?.notificationOccurred('success');
        });
    }
    
    if (fontSizeCancel) {
        fontSizeCancel.addEventListener('click', () => {
            if (wordDisplay) {
                wordDisplay.style.fontSize = `${currentFontSize}px`;
            }
            fontSizeDialog.style.display = 'none';
        });
    }
    
    // إخفاء نافذة حجم الخط عند النقر خارجها
    document.addEventListener('click', (e) => {
        if (fontSizeDialog && fontSizeDialog.style.display !== 'none') {
            if (!fontSizeDialog.contains(e.target) && e.target !== btnFontSize) {
                if (wordDisplay) {
                    wordDisplay.style.fontSize = `${currentFontSize}px`;
                }
                fontSizeDialog.style.display = 'none';
            }
        }
    });
    let isResizing = false;
    let startY = 0;
    let startX = 0;
    let initialBrushSize = brushSize;
    let initialBrushOpacity = brushOpacity;
    if (brushSizeControl) {
        brushSizeControl.addEventListener('mousedown', (e) => {
            isResizing = true;
            startY = e.clientY;
            startX = e.clientX;
            initialBrushSize = brushSize;
            initialBrushOpacity = brushOpacity;
            e.preventDefault();
        });
        window.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const deltaY = startY - e.clientY;
            const deltaX = e.clientX - startX;
            brushSize = Math.max(MIN_BRUSH_SIZE, Math.min(MAX_BRUSH_SIZE, initialBrushSize + deltaY / 2));
            let newOpacity = initialBrushOpacity + deltaX / 300;
            brushOpacity = Math.max(0, Math.min(1.0, newOpacity));
            updateBrushIndicator(brushSize, brushOpacity);
            e.preventDefault();
        });
        window.addEventListener('mouseup', () => {
            isResizing = false;
        });
    }

    // ****************************
    // #9. التهيئة (Initialization) المُحدَّثة
    // ****************************

    fixCanvas();
    pushUndo();
    updateBrushIndicator(brushSize, brushOpacity);

    btnPencil?.querySelector('.circle-switch')?.classList.add('active');
    
    // ✅ تحميل حجم الخط المحفوظ عند التهيئة
    const savedFontSize = localStorage.getItem('drawAndGuessFontSize');
    if (savedFontSize && wordDisplay) {
        currentFontSize = parseInt(savedFontSize);
        wordDisplay.style.fontSize = `${currentFontSize}px`;
    }

    window.addEventListener('resize', () => {
        const img = mainCanvas.toDataURL();
        fixCanvas();
        const i = new Image();
        i.onload = () => mainCtx.drawImage(i, 0, 0, mainCanvas.width / (window.devicePixelRatio || 1), mainCanvas.height / (window.devicePixelRatio || 1));
        i.src = img;
    });
    if (brushCircle) {
        brushCircle.style.background = brushColor;
    }
    if (colorIconSpan) {
        colorIconSpan.style.color = brushColor;
    }

    try {
        if (tg) {
            tg.expand && tg.expand();
            const canvasContainer = document.querySelector('.canvas-container');
            if (canvasContainer) {
                canvasContainer.classList.add('tg-scaled');
            }
            
            // 🎯 الجديد: إخفاء زر عرض الكلمة عند البدء، وسيتم عرضه بعد أول اختيار
            if (wordBox) wordBox.style.display = 'none';

        }

        // 🎯 الأهم: عرض مربع حوار الكلمات تلقائياً عند التهيئة
if (wordDialog && WORDS_LIST.length >= 4) {
        // ✅ تقليل عدد الكلمات المعروضة إلى 4 فقط
        const initialWords = getRandomWordsAvoidUsed(WORDS_LIST, 4);
        generateWordButtons(initialWords);
        wordDialog.style.display = 'block';
    } else if (wordBox) {
         currentWord = WORDS_LIST[0] || 'ارسم وخمن ⚙️';
         wordBox.innerHTML = `${currentWord} ⚙️`;
         wordBox.style.display = 'block';
    }


    } catch(e){
        console.warn('init error', e);
    }

})();