# env_loader.py
# بديل لـ dotenv - قراءة متغيرات البيئة من ملف .env يدوياً
import os

def load_env_file(filepath='.env'):
    """
    قراءة متغيرات البيئة من ملف .env
    يدعم التعليقات والمسافات الفارغة
    """
    if not os.path.exists(filepath):
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # تجاهل الأسطر الفارغة والتعليقات
            if not line or line.startswith('#'):
                continue
            
            # تقسيم السطر إلى key و value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # إزالة علامات الاقتباس إذا كانت موجودة
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # تعيين المتغير في البيئة (نعيد الكتابة للتحديث)
                if key and value:
                    os.environ[key] = value

# تحميل ملف .env تلقائياً عند استيراد الوحدة
load_env_file()

