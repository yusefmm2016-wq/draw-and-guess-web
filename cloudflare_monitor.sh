#!/bin/bash
# سكريبت مراقبة Cloudflare Tunnel - يفحص الرابط باستمرار ويجدده إذا سقط
# يعمل في الخلفية كخدمة مستمرة

PROJECT_DIR="/opt/tgames"
ENV_FILE="$PROJECT_DIR/.env"
LOG_FILE="$PROJECT_DIR/cloudflare_monitor.log"
TUNNEL_LOG="$PROJECT_DIR/cloudflared.log"
CHECK_INTERVAL=30  # فحص كل 30 ثانية
MAX_FAILURES=3     # عدد الفشل قبل إعادة التشغيل
FLASK_PORT=8080    # المنفذ الصحيح لـ Flask

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# دالة للتسجيل
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo -e "$1"
}

# دالة للحصول على الرابط الحالي من .env
get_current_url() {
    grep "^CLOUDFLARE_TUNNEL_URL=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2
}

# دالة لتحديث الرابط في .env
update_env_url() {
    local new_url="$1"
    
    # إزالة أي ألوان أو أحرف خاصة من الرابط
    new_url=$(echo "$new_url" | tr -d '\n' | grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    
    if [ -z "$new_url" ]; then
        log "${RED}❌ رابط غير صالح${NC}"
        return 1
    fi
    
    # تحديث جميع متغيرات الرابط باستخدام # كفاصل بدلاً من |
    sed -i "s#^WEBAPP_URL=.*#WEBAPP_URL=$new_url#" "$ENV_FILE"
    sed -i "s#^GUESS_WHO_WEBAPP_URL=.*#GUESS_WHO_WEBAPP_URL=$new_url#" "$ENV_FILE"
    sed -i "s#^CLOUDFLARE_TUNNEL_URL=.*#CLOUDFLARE_TUNNEL_URL=$new_url#" "$ENV_FILE"
    
    log "${GREEN}✅ تم تحديث الرابط في .env: $new_url${NC}"
}

# دالة لفحص صحة الرابط
check_tunnel_health() {
    local url="$1"
    
    if [ -z "$url" ]; then
        return 1
    fi
    
    # فحص HTTP response
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 "$url" 2>/dev/null)
    
    if [ "$response" = "200" ] || [ "$response" = "302" ] || [ "$response" = "301" ]; then
        return 0
    else
        return 1
    fi
}

# دالة لإيقاف Cloudflare Tunnel الحالي
stop_tunnel() {
    log "${YELLOW}🛑 إيقاف Cloudflare Tunnel الحالي...${NC}"
    pkill -9 -f "cloudflared.*tunnel" 2>/dev/null || true
    pkill -9 -f "./cloudflared.*tunnel" 2>/dev/null || true
    sleep 2
}

# دالة لبدء Cloudflare Tunnel جديد واستخراج الرابط
start_new_tunnel() {
    log "${BLUE}🚀 بدء Cloudflare Tunnel جديد...${NC}"
    
    # حذف ملف السجل القديم
    > "$TUNNEL_LOG"
    
    # تحديد مسار cloudflared - الأولوية للملف في المشروع
    CLOUDFLARE_CMD="$PROJECT_DIR/cloudflared"
    if [ ! -f "$CLOUDFLARE_CMD" ]; then
        if command -v cloudflared &> /dev/null; then
            CLOUDFLARE_CMD="cloudflared"
        else
            log "${RED}❌ cloudflared غير موجود!${NC}"
            return 1
        fi
    fi
    
    log "${GREEN}✅ استخدام: $CLOUDFLARE_CMD${NC}"
    
    # تشغيل Tunnel في الخلفية من داخل المشروع
    cd "$PROJECT_DIR"
    nohup "$CLOUDFLARE_CMD" tunnel --url http://localhost:$FLASK_PORT > "$TUNNEL_LOG" 2>&1 &
    
    # انتظار ظهور الرابط في السجل
    local max_wait=30
    local waited=0
    local new_url=""
    
    while [ $waited -lt $max_wait ]; do
        sleep 2
        waited=$((waited + 2))
        
        # استخراج الرابط من السجل
        new_url=$(grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" "$TUNNEL_LOG" 2>/dev/null | head -1)
        
        if [ -n "$new_url" ]; then
            log "${GREEN}✅ تم الحصول على رابط جديد: $new_url${NC}"
            echo "$new_url"
            return 0
        fi
    done
    
    log "${RED}❌ فشل في الحصول على رابط جديد${NC}"
    return 1
}

# دالة لإعادة تشغيل البوت
restart_bot() {
    log "${YELLOW}🔄 إعادة تشغيل البوت لتحميل الرابط الجديد...${NC}"
    
    # إيقاف البوت
    pkill -9 -f "python.*main.py" 2>/dev/null || true
    sleep 2
    
    # تشغيل البوت
    cd "$PROJECT_DIR"
    nohup python3 main.py > bot.log 2>&1 &
    
    sleep 3
    
    if pgrep -f "python.*main.py" > /dev/null; then
        log "${GREEN}✅ تم إعادة تشغيل البوت بنجاح${NC}"
        return 0
    else
        log "${RED}❌ فشل في إعادة تشغيل البوت${NC}"
        return 1
    fi
}

# دالة لإعادة إنشاء Tunnel وتحديث البوت
recreate_tunnel() {
    log "${YELLOW}🔧 إعادة إنشاء Cloudflare Tunnel...${NC}"
    
    # إيقاف Tunnel الحالي
    stop_tunnel
    
    # بدء Tunnel جديد
    local new_url=$(start_new_tunnel)
    
    if [ -n "$new_url" ]; then
        # تحديث .env
        update_env_url "$new_url"
        
        # إعادة تشغيل البوت
        restart_bot
        
        log "${GREEN}✅ تم تجديد Tunnel بنجاح!${NC}"
        return 0
    else
        log "${RED}❌ فشل في تجديد Tunnel${NC}"
        return 1
    fi
}

# الدالة الرئيسية للمراقبة
monitor_loop() {
    local failure_count=0
    
    log "${BLUE}========================================${NC}"
    log "${BLUE}🔍 بدء مراقبة Cloudflare Tunnel${NC}"
    log "${BLUE}========================================${NC}"
    
    while true; do
        local current_url=$(get_current_url)
        
        if [ -z "$current_url" ]; then
            log "${YELLOW}⚠️ لا يوجد رابط Tunnel، إنشاء رابط جديد...${NC}"
            recreate_tunnel
            failure_count=0
            sleep $CHECK_INTERVAL
            continue
        fi
        
        # فحص صحة الرابط
        if check_tunnel_health "$current_url"; then
            if [ $failure_count -gt 0 ]; then
                log "${GREEN}✅ الرابط عاد للعمل: $current_url${NC}"
            fi
            failure_count=0
        else
            failure_count=$((failure_count + 1))
            log "${YELLOW}⚠️ فشل فحص الرابط ($failure_count/$MAX_FAILURES): $current_url${NC}"
            
            if [ $failure_count -ge $MAX_FAILURES ]; then
                log "${RED}❌ الرابط سقط! إعادة إنشاء Tunnel...${NC}"
                recreate_tunnel
                failure_count=0
            fi
        fi
        
        sleep $CHECK_INTERVAL
    done
}

# التحقق من المعاملات
case "$1" in
    start)
        # تشغيل في الخلفية
        log "${GREEN}🚀 تشغيل المراقب في الخلفية...${NC}"
        nohup "$0" run > /dev/null 2>&1 &
        echo "✅ تم تشغيل المراقب (PID: $!)"
        ;;
    stop)
        log "${RED}🛑 إيقاف المراقب...${NC}"
        pkill -f "cloudflare_monitor.sh run" 2>/dev/null || true
        echo "✅ تم إيقاف المراقب"
        ;;
    status)
        if pgrep -f "cloudflare_monitor.sh run" > /dev/null; then
            echo "✅ المراقب يعمل"
            echo "📄 آخر 10 أسطر من السجل:"
            tail -10 "$LOG_FILE" 2>/dev/null || echo "لا يوجد سجل"
        else
            echo "❌ المراقب متوقف"
        fi
        ;;
    check)
        # فحص فوري
        current_url=$(get_current_url)
        echo "🔗 الرابط الحالي: $current_url"
        if check_tunnel_health "$current_url"; then
            echo "✅ الرابط يعمل بشكل صحيح"
        else
            echo "❌ الرابط لا يعمل"
        fi
        ;;
    renew)
        # تجديد فوري
        recreate_tunnel
        ;;
    run)
        # تشغيل المراقبة (للاستخدام الداخلي)
        monitor_loop
        ;;
    *)
        echo "استخدام: $0 {start|stop|status|check|renew}"
        echo ""
        echo "  start  - تشغيل المراقب في الخلفية"
        echo "  stop   - إيقاف المراقب"
        echo "  status - عرض حالة المراقب"
        echo "  check  - فحص الرابط الحالي"
        echo "  renew  - تجديد الرابط فوراً"
        exit 1
        ;;
esac

