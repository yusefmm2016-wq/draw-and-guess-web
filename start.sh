
#!/bin/bash
# سكريبت شامل لتشغيل البوت مع Cloudflare Tunnel
# يقوم بكل شيء تلقائياً: إيقاف العمليات السابقة، تثبيت المتطلبات، تشغيل Tunnel، تشغيل البوت

set -e  # إيقاف عند أي خطأ - معطل لتجنب إيقاف السكريبت عند أخطاء غير حرجة

cd /opt/tgames

# الألوان للرسائل
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 بدء تشغيل البوت مع Cloudflare Tunnel${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ==========================================
# 1. إيقاف جميع العمليات السابقة
# ==========================================
echo -e "${YELLOW}🛑 إيقاف جميع عمليات البوت السابقة...${NC}"
pkill -9 -f "python.*main.py" 2>/dev/null || true
pkill -9 -f "cloudflared.*tunnel" 2>/dev/null || true
sleep 3

# التحقق مرة أخرى
if pgrep -f "python.*main.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  لا يزال هناك عمليات! إيقافها بالقوة...${NC}"
    killall -9 python3 2>/dev/null || true
    sleep 2
fi

if pgrep -f "cloudflared.*tunnel" > /dev/null; then
    echo -e "${YELLOW}⚠️  لا يزال هناك Tunnel! إيقافها...${NC}"
    killall -9 cloudflared 2>/dev/null || true
    sleep 2
fi

echo -e "${GREEN}✅ تم إيقاف جميع العمليات السابقة${NC}"
echo ""

# ==========================================
# 2. التحقق من Python والمتطلبات
# ==========================================
echo -e "${YELLOW}🔍 التحقق من Python والمتطلبات...${NC}"

PYTHON3_CMD=$(command -v python3)
if [ -z "$PYTHON3_CMD" ]; then
    echo -e "${RED}❌ Python3 غير مثبت!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3 موجود: $PYTHON3_CMD${NC}"

# التحقق من المتطلبات
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 تثبيت/تحديث المتطلبات...${NC}"
    
    # استخدام virtual environment إن وجد
    if [ -d "venv" ] && [ -f "venv/bin/pip" ]; then
        ./venv/bin/pip install -q -r requirements.txt 2>/dev/null || {
            echo -e "${YELLOW}⚠️  بعض المتطلبات قد تحتاج تثبيت يدوي${NC}"
        }
        echo -e "${GREEN}✅ المتطلبات جاهزة (venv)${NC}"
    else
        pip3 install -q -r requirements.txt 2>/dev/null || {
            echo -e "${YELLOW}⚠️  بعض المتطلبات قد تحتاج تثبيت يدوي${NC}"
        }
        echo -e "${GREEN}✅ المتطلبات جاهزة${NC}"
    fi
fi

echo ""

# ==========================================
# 3. تثبيت Cloudflare Tunnel (cloudflared)
# ==========================================
echo -e "${YELLOW}🌐 التحقق من Cloudflare Tunnel...${NC}"

if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}📥 cloudflared غير مثبت، جاري التثبيت...${NC}"
    
    # تحديد البنية المعمارية
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        ARCH="amd64"
    elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        ARCH="arm64"
    else
        ARCH="amd64"  # افتراضي
    fi
    
    # تحميل cloudflared
    DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}"
    TEMP_FILE="/tmp/cloudflared"
    
    echo -e "${YELLOW}⬇️  جاري تحميل cloudflared...${NC}"
    if curl -L -o "$TEMP_FILE" "$DOWNLOAD_URL" 2>/dev/null; then
        chmod +x "$TEMP_FILE"
        
        # محاولة التثبيت في /usr/local/bin (يحتاج sudo)
        if sudo mv "$TEMP_FILE" /usr/local/bin/cloudflared 2>/dev/null; then
            echo -e "${GREEN}✅ تم تثبيت cloudflared في /usr/local/bin${NC}"
        # محاولة التثبيت في ~/.local/bin (لا يحتاج sudo)
        elif mkdir -p ~/.local/bin && mv "$TEMP_FILE" ~/.local/bin/cloudflared; then
            export PATH="$HOME/.local/bin:$PATH"
            echo -e "${GREEN}✅ تم تثبيت cloudflared في ~/.local/bin${NC}"
            echo -e "${YELLOW}💡 أضف ~/.local/bin إلى PATH إذا لزم الأمر${NC}"
        else
            # استخدام من المجلد الحالي (الأولوية)
            mv "$TEMP_FILE" ./cloudflared
            chmod +x ./cloudflared
            export PATH="$(pwd):$PATH"
            echo -e "${GREEN}✅ تم تحميل cloudflared في المجلد الحالي (المشروع)${NC}"
        fi
    else
        echo -e "${RED}❌ فشل تحميل cloudflared${NC}"
        echo -e "${YELLOW}⚠️  يمكنك تثبيته يدوياً أو تخطي Tunnel${NC}"
        SKIP_TUNNEL=true
    fi
else
    echo -e "${GREEN}✅ cloudflared مثبت بالفعل${NC}"
fi

echo ""

# ==========================================
# 4. تشغيل البوت أولاً (ليبدأ Flask)
# ==========================================
echo -e "${YELLOW}🤖 تشغيل البوت (ليبدأ Flask)...${NC}"

# تحميل متغيرات البيئة من .env إذا كان موجوداً
if [ -f .env ]; then
    set -a
    . .env  # استخدام . بدلاً من source للتوافق
    set +a
    echo -e "${GREEN}✅ تم تحميل متغيرات البيئة من .env${NC}"
fi

# استخدام virtual environment إن وجد
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
    echo -e "${GREEN}✅ استخدام virtual environment${NC}"
else
    PYTHON_CMD="python3"
    echo -e "${YELLOW}⚠️  استخدام Python3 النظامي (يفضل استخدام venv)${NC}"
fi

# تشغيل البوت في الخلفية
nohup $PYTHON_CMD main.py > bot.log 2>&1 &
BOT_PID=$!
echo -e "${GREEN}✅ تم بدء البوت (PID: $BOT_PID)${NC}"

# انتظار Flask ليعمل على المنفذ 8080
PORT=8080
FLASK_RUNNING=false
echo -e "${YELLOW}⏳ انتظار Flask ليعمل على المنفذ $PORT...${NC}"

for i in {1..15}; do
    sleep 2
    if nc -z localhost $PORT 2>/dev/null || curl -s http://localhost:$PORT > /dev/null 2>&1; then
        FLASK_RUNNING=true
        echo -e "${GREEN}✅ Flask يعمل الآن على المنفذ $PORT${NC}"
        break
    fi
    echo -e "${YELLOW}   محاولة $i/15: انتظار Flask...${NC}"
done

if [ "$FLASK_RUNNING" != "true" ]; then
    echo -e "${YELLOW}⚠️  Flask لم يبدأ بعد، لكن سنستمر...${NC}"
fi

echo ""

# ==========================================
# 5. تشغيل Cloudflare Tunnel (بعد Flask)
# ==========================================
TUNNEL_URL=""
TUNNEL_PID=""

if [ "$SKIP_TUNNEL" != "true" ] && command -v cloudflared &> /dev/null; then
    # التحقق مرة أخرى من أن Flask يعمل قبل بدء Tunnel
    if [ "$FLASK_RUNNING" != "true" ]; then
        echo -e "${YELLOW}⏳ انتظار إضافي لبدء Flask...${NC}"
        sleep 5
        if nc -z localhost $PORT 2>/dev/null || curl -s http://localhost:$PORT > /dev/null 2>&1; then
            FLASK_RUNNING=true
            echo -e "${GREEN}✅ Flask يعمل الآن${NC}"
        else
            echo -e "${RED}❌ Flask لا يزال غير متاح. قد يفشل Tunnel.${NC}"
        fi
    fi
    
    echo -e "${YELLOW}🚇 بدء Cloudflare Tunnel للمنفذ $PORT (HTTPS/SSL مضمون)...${NC}"
    
    # إيقاف أي عملية cloudflared قديمة
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    sleep 2

    # حذف الملفات القديمة
    rm -f /tmp/tunnel_url.txt
    rm -f ./cloudflared.log 2>/dev/null || true
    rm -f /tmp/cloudflared.log 2>/dev/null || true
    
    # تحديد مسار cloudflared - الأولوية للملف في المشروع
    CLOUDFLARE_CMD="./cloudflared"
    if [ ! -f "./cloudflared" ]; then
        if command -v cloudflared &> /dev/null; then
            CLOUDFLARE_CMD="cloudflared"
        else
            echo -e "${RED}❌ cloudflared غير موجود!${NC}"
            SKIP_TUNNEL=true
        fi
    fi
    
    if [ "$SKIP_TUNNEL" != "true" ]; then
        echo -e "${GREEN}✅ استخدام: $CLOUDFLARE_CMD${NC}"
    fi
    
    # تحديد مسار الملف (مع خيارات بديلة)
    CLOUDFLARE_LOG="./cloudflared.log"
    if ! touch "$CLOUDFLARE_LOG" 2>/dev/null; then
        CLOUDFLARE_LOG="/tmp/cloudflared.log"
    fi
    
    if ! touch "$CLOUDFLARE_LOG" 2>/dev/null; then
        # إذا فشل إنشاء الملف في /tmp، نستخدم المجلد الحالي
        CLOUDFLARE_LOG="./cloudflared.log"
        if ! touch "$CLOUDFLARE_LOG" 2>/dev/null; then
            # إذا فشل أيضاً، نستخدم ملف مؤقت
            CLOUDFLARE_LOG="cloudflared_$$.log"
            touch "$CLOUDFLARE_LOG" 2>/dev/null || {
                echo -e "${RED}❌ فشل إنشاء ملف السجلات${NC}"
                CLOUDFLARE_LOG=""
            }
        fi
    fi
    
    # تشغيل Cloudflare Tunnel
    # cloudflared يوفر HTTPS/SSL تلقائياً - مثالي لـ Telegram WebApp
    # الصيغة: cloudflared tunnel --url http://localhost:PORT
    if [ -z "$CLOUDFLARE_LOG" ]; then
        echo -e "${YELLOW}⚠️  سيتم تشغيل Tunnel بدون حفظ السجلات${NC}"
        # تشغيل بدون حفظ في ملف
        nohup $CLOUDFLARE_CMD tunnel --url http://localhost:$PORT > /dev/null 2>&1 &
        TUNNEL_PID=$!
        SKIP_TUNNEL_LOG=true
    else
        # تشغيل Tunnel في الخلفية مع حفظ المخرجات
        # مسح الملف القديم أولاً
        > "$CLOUDFLARE_LOG"
        nohup $CLOUDFLARE_CMD tunnel --url http://localhost:$PORT >> "$CLOUDFLARE_LOG" 2>&1 &
        TUNNEL_PID=$!
        SKIP_TUNNEL_LOG=false
        echo -e "${GREEN}✅ تم بدء cloudflared في الخلفية (PID: $TUNNEL_PID)${NC}"
        echo -e "${BLUE}📄 السجلات: $CLOUDFLARE_LOG${NC}"
    fi
    
    # انتظار وإنشاء Tunnel - نقرأ المخرجات مباشرة
    echo -e "${YELLOW}⏳ انتظار إنشاء Tunnel مع HTTPS/SSL (قد يستغرق 10-30 ثانية)...${NC}"
    
    # محاولات متعددة لقراءة الرابط من المخرجات
    TUNNEL_URL=""
    if [ "$SKIP_TUNNEL_LOG" != "true" ] && [ -n "$CLOUDFLARE_LOG" ]; then
        for attempt in $(seq 1 30); do
            sleep 2
            
            # التحقق من وجود الملف قبل القراءة
            if [ ! -f "$CLOUDFLARE_LOG" ]; then
                echo -e "${YELLOW}   محاولة $attempt/30: انتظار إنشاء ملف السجلات...${NC}"
                continue
            fi
            
            # التحقق من أن الملف غير فارغ
            if [ ! -s "$CLOUDFLARE_LOG" ]; then
                echo -e "${YELLOW}   محاولة $attempt/30: انتظار كتابة السجلات...${NC}"
                continue
            fi
            
            # البحث عن رابط HTTPS في المخرجات - عدة أنماط
            # النمط 1: البحث المباشر عن trycloudflare.com
            TUNNEL_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CLOUDFLARE_LOG" 2>/dev/null | head -1)
            
            if [ -n "$TUNNEL_URL" ]; then
                echo -e "${GREEN}✅ تم العثور على الرابط في المحاولة $attempt${NC}"
                break
            fi
            
            # النمط 2: البحث في السطور التي تحتوي على "Visit it at"
            TUNNEL_URL=$(grep -A 2 "Visit it at" "$CLOUDFLARE_LOG" 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)
            if [ -n "$TUNNEL_URL" ]; then
                echo -e "${GREEN}✅ تم العثور على الرابط في المحاولة $attempt${NC}"
                break
            fi
            
            # النمط 3: البحث في السطور التي تحتوي على "Your quick Tunnel"
            TUNNEL_URL=$(grep -A 2 "Your quick Tunnel" "$CLOUDFLARE_LOG" 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)
            if [ -n "$TUNNEL_URL" ]; then
                echo -e "${GREEN}✅ تم العثور على الرابط في المحاولة $attempt${NC}"
                break
            fi
            
            # النمط 4: البحث في أي سطر يحتوي على trycloudflare.com
            TUNNEL_URL=$(grep "trycloudflare.com" "$CLOUDFLARE_LOG" 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)
            if [ -n "$TUNNEL_URL" ]; then
                echo -e "${GREEN}✅ تم العثور على الرابط في المحاولة $attempt${NC}"
                break
            fi

            # النمط 5: البحث في آخر 50 سطر (للحالات التي قد لا تظهر فيها الأنماط السابقة بوضوح)
            TUNNEL_URL=$(tail -50 "$CLOUDFLARE_LOG" 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)
            if [ -n "$TUNNEL_URL" ]; then
                echo -e "${GREEN}✅ تم العثور على الرابط في المحاولة $attempt${NC}"
                break
            fi
            
            if [ $((attempt % 5)) -eq 0 ]; then
                echo -e "${YELLOW}   محاولة $attempt/30: لا يزال البحث عن الرابط...${NC}"
            fi
            done
    else
        # إذا لم نتمكن من حفظ السجلات، نعطي تعليمات يدوية
        echo -e "${YELLOW}⚠️  لم يتم حفظ السجلات - شغّل Tunnel يدوياً للحصول على الرابط${NC}"
        echo -e "${YELLOW}💡 شغّل: $CLOUDFLARE_CMD tunnel --url http://localhost:$PORT${NC}"
    fi
    
    if [ -n "$TUNNEL_URL" ]; then
        echo -e "${GREEN}✅ تم إنشاء Tunnel بنجاح!${NC}"
        echo -e "${BLUE}🔗 الرابط: $TUNNEL_URL${NC}"
        
        # حفظ الرابط في .env
        if [ -f .env ]; then
            # تحديث أو إضافة WEBAPP_URL
            if grep -q "WEBAPP_URL=" .env; then
                sed -i "s|WEBAPP_URL=.*|WEBAPP_URL=$TUNNEL_URL|" .env
            else
                echo "WEBAPP_URL=$TUNNEL_URL" >> .env
            fi
            
            # تحديث أو إضافة GUESS_WHO_WEBAPP_URL
            if grep -q "GUESS_WHO_WEBAPP_URL=" .env; then
                sed -i "s|GUESS_WHO_WEBAPP_URL=.*|GUESS_WHO_WEBAPP_URL=$TUNNEL_URL|" .env
            else
                echo "GUESS_WHO_WEBAPP_URL=$TUNNEL_URL" >> .env
            fi
            
            # إضافة CLOUDFLARE_TUNNEL_URL
            if grep -q "CLOUDFLARE_TUNNEL_URL=" .env; then
                sed -i "s|CLOUDFLARE_TUNNEL_URL=.*|CLOUDFLARE_TUNNEL_URL=$TUNNEL_URL|" .env
            else
                echo "CLOUDFLARE_TUNNEL_URL=$TUNNEL_URL" >> .env
            fi
            
            echo -e "${GREEN}💾 تم حفظ الرابط في .env${NC}"
        else
            # إنشاء ملف .env جديد
            cat > .env << EOF
WEBAPP_URL=$TUNNEL_URL
GUESS_WHO_WEBAPP_URL=$TUNNEL_URL
CLOUDFLARE_TUNNEL_URL=$TUNNEL_URL
EOF
            echo -e "${GREEN}💾 تم إنشاء ملف .env جديد${NC}"
        fi
        
        # تصدير متغيرات البيئة للجلسة الحالية
        export WEBAPP_URL="$TUNNEL_URL"
        export GUESS_WHO_WEBAPP_URL="$TUNNEL_URL"
        export CLOUDFLARE_TUNNEL_URL="$TUNNEL_URL"
        
        echo -e "${GREEN}🔄 تم تعيين متغيرات البيئة${NC}"
    else
        echo -e "${YELLOW}⚠️  لم يتم العثور على رابط Tunnel تلقائياً${NC}"
        echo -e "${YELLOW}💡 تحقق من $CLOUDFLARE_LOG يدوياً${NC}"
        echo -e "${YELLOW}💡 أو شغّل: $CLOUDFLARE_CMD tunnel --url http://localhost:$PORT${NC}"
    fi
    
    echo ""
else
    echo -e "${YELLOW}⚠️  تخطي Cloudflare Tunnel${NC}"
    echo ""
fi

# ==========================================
# 6. التحقق من أن البوت يعمل
# ==========================================
sleep 3

# التحقق من أن البوت يعمل
if ps -p $BOT_PID > /dev/null 2>&1; then
    INSTANCE_COUNT=$(pgrep -f "python3 main.py" | grep -v grep | wc -l)
    
    if [ "$INSTANCE_COUNT" -eq "1" ]; then
        echo -e "${GREEN}✅ البوت يعمل الآن!${NC}"
        echo -e "${BLUE}📊 PID: $BOT_PID${NC}"
        echo -e "${BLUE}📄 Logs: tail -f /opt/tgames/bot.log${NC}"
        
        if [ -n "$TUNNEL_PID" ]; then
            echo -e "${BLUE}🌐 Tunnel PID: $TUNNEL_PID${NC}"
        fi
        
        echo ""
        echo -e "${BLUE}🔍 آخر 10 أسطر من الـ logs:${NC}"
        tail -10 bot.log | grep -E "(Application started|تم تسجيل|ERROR|🚀|✅)" || tail -10 bot.log
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ تم تشغيل كل شيء بنجاح!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}📝 معلومات مهمة:${NC}"
        echo -e "  • البوت: PID $BOT_PID"
        if [ -n "$TUNNEL_PID" ]; then
            echo -e "  • Tunnel: PID $TUNNEL_PID"
            if [ -n "$TUNNEL_URL" ]; then
                echo -e "  • رابط WebApp: $TUNNEL_URL"
            fi
        fi
        echo -e "  • Logs: tail -f /opt/tgames/bot.log"
        echo -e "  • Tunnel Logs: tail -f /tmp/cloudflared.log"
        echo ""
        echo -e "${YELLOW}💡 للإيقاف: ./stop.sh${NC}"
        
    elif [ "$INSTANCE_COUNT" -gt "1" ]; then
        echo -e "${RED}❌ خطأ! هناك $INSTANCE_COUNT instances تعمل!${NC}"
        echo -e "${YELLOW}🛑 إيقافها جميعاً...${NC}"
        pkill -9 -f "python3 main.py"
        sleep 3
        echo -e "${RED}❌ فشل! تحقق من bot.log${NC}"
        tail -20 bot.log
        exit 1
    else
        echo -e "${RED}❌ فشل تشغيل البوت!${NC}"
        echo -e "${YELLOW}📄 تحقق من bot.log:${NC}"
        tail -20 bot.log
        exit 1
    fi
else
    echo -e "${RED}❌ فشل تشغيل البوت!${NC}"
    echo -e "${YELLOW}📄 تحقق من bot.log:${NC}"
    tail -20 bot.log
    exit 1
fi
