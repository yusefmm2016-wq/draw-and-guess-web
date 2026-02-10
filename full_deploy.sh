#!/bin/bash
# سكريبت شامل للنشر الكامل - يرفع الملفات ويصبها ويشغلها

set -e

SERVER="root@72.62.151.100"
PASSWORD="Hgukd+123123"
PROJECT_DIR="/opt/tgames"
LOCAL_DIR="/sdcard/TGames"

# ألوان
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 بدء النشر الكامل على السيرفر${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# تثبيت sshpass إذا لم يكن موجوداً
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}📥 تثبيت sshpass...${NC}"
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y sshpass > /dev/null 2>&1 || {
        echo -e "${YELLOW}⚠️  sshpass غير متوفر، سيتم طلب كلمة المرور يدوياً${NC}"
        USE_SSHPASS=false
    }
    USE_SSHPASS=true
else
    USE_SSHPASS=true
fi

# 1. رفع الملفات
echo -e "${YELLOW}📤 رفع الملفات إلى السيرفر...${NC}"

if [ "$USE_SSHPASS" = true ]; then
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" "mkdir -p $PROJECT_DIR" 2>/dev/null
    sshpass -p "$PASSWORD" scp -r -o StrictHostKeyChecking=no "$LOCAL_DIR"/* "$SERVER:$PROJECT_DIR/" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  محاولة رفع بدون sshpass...${NC}"
        scp -r "$LOCAL_DIR"/* "$SERVER:$PROJECT_DIR/" || {
            echo -e "${RED}❌ فشل رفع الملفات${NC}"
            exit 1
        }
    }
else
    ssh -o StrictHostKeyChecking=no "$SERVER" "mkdir -p $PROJECT_DIR"
    scp -r "$LOCAL_DIR"/* "$SERVER:$PROJECT_DIR/" || {
        echo -e "${RED}❌ فشل رفع الملفات${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✅ تم رفع الملفات${NC}"
echo ""

# 2. تثبيت وتشغيل على السيرفر
echo -e "${YELLOW}⚙️  تثبيت وتشغيل على السيرفر...${NC}"

if [ "$USE_SSHPASS" = true ]; then
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
        set -e
        
        PROJECT_DIR="/opt/tgames"
        PROJECT_NAME="tgames-bot"
        SERVICE_FILE="/etc/systemd/system/${PROJECT_NAME}.service"
        
        cd "$PROJECT_DIR"
        
        # تثبيت Python و pip إذا لم يكونا موجودين
        if ! command -v python3 &> /dev/null; then
            apt-get update -qq
            apt-get install -y python3 python3-pip python3-venv
        fi
        
        # تثبيت pip3 إذا لم يكن موجوداً
        if ! command -v pip3 &> /dev/null; then
            apt-get update -qq
            apt-get install -y python3-pip
        fi
        
        # تثبيت المتطلبات
        python3 -m pip install -q --upgrade pip || pip3 install -q --upgrade pip
        python3 -m pip install -q -r requirements.txt || pip3 install -q -r requirements.txt
        
        # إنشاء systemd service
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegram Games Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        # تفعيل وتشغيل
        systemctl daemon-reload
        systemctl stop "$PROJECT_NAME" 2>/dev/null || true
        sleep 2
        systemctl enable "$PROJECT_NAME"
        systemctl start "$PROJECT_NAME"
        
        sleep 5
        
        # التحقق
        if systemctl is-active --quiet "$PROJECT_NAME"; then
            echo "✅ تم التثبيت والتشغيل بنجاح!"
            systemctl status "$PROJECT_NAME" --no-pager -l
        else
            echo "❌ فشل التشغيل!"
            journalctl -u "$PROJECT_NAME" -n 30 --no-pager
            exit 1
        fi
ENDSSH
else
    ssh -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
        set -e
        
        PROJECT_DIR="/opt/tgames"
        PROJECT_NAME="tgames-bot"
        SERVICE_FILE="/etc/systemd/system/${PROJECT_NAME}.service"
        
        cd "$PROJECT_DIR"
        
        # تثبيت Python و pip إذا لم يكونا موجودين
        if ! command -v python3 &> /dev/null; then
            apt-get update -qq
            apt-get install -y python3 python3-pip python3-venv
        fi
        
        # تثبيت pip3 إذا لم يكن موجوداً
        if ! command -v pip3 &> /dev/null; then
            apt-get update -qq
            apt-get install -y python3-pip
        fi
        
        # تثبيت المتطلبات
        python3 -m pip install -q --upgrade pip || pip3 install -q --upgrade pip
        python3 -m pip install -q -r requirements.txt || pip3 install -q -r requirements.txt
        
        # إنشاء systemd service
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegram Games Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        # تفعيل وتشغيل
        systemctl daemon-reload
        systemctl stop "$PROJECT_NAME" 2>/dev/null || true
        sleep 2
        systemctl enable "$PROJECT_NAME"
        systemctl start "$PROJECT_NAME"
        
        sleep 5
        
        # التحقق
        if systemctl is-active --quiet "$PROJECT_NAME"; then
            echo "✅ تم التثبيت والتشغيل بنجاح!"
            systemctl status "$PROJECT_NAME" --no-pager -l
        else
            echo "❌ فشل التشغيل!"
            journalctl -u "$PROJECT_NAME" -n 30 --no-pager
            exit 1
        fi
ENDSSH
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ اكتمل النشر بنجاح!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 للتحقق من الحالة:${NC}"
echo "  ssh $SERVER 'systemctl status tgames-bot'"
echo ""
echo -e "${BLUE}📄 لعرض السجلات:${NC}"
echo "  ssh $SERVER 'journalctl -u tgames-bot -f'"

