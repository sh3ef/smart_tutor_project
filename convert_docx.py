#!/usr/bin/env python3
"""
حذف ملفات docx بعد التحويل للمعلم الذكي السعودي
يحذف جميع ملفات .docx من مجلدات المشروع بعد التأكد من وجود ملفات .txt المقابلة
"""

import os
from pathlib import Path

def confirm_deletion():
    """طلب تأكيد من المستخدم قبل الحذف"""
    print("⚠️  تحذير: ستتم إزالة جميع ملفات .docx من المشروع نهائياً!")
    print("تأكد من أن التحويل إلى .txt تم بنجاح قبل المتابعة.")
    
    while True:
        response = input("\nهل أنت متأكد من المتابعة؟ (نعم/لا): ").lower().strip()
        if response in ['نعم', 'yes', 'y', 'ن']:
            return True
        elif response in ['لا', 'no', 'n', 'ل']:
            return False
        else:
            print("يرجى الإجابة بـ 'نعم' أو 'لا'")

def check_txt_exists(docx_file: Path) -> bool:
    """التحقق من وجود ملف txt مقابل لملف docx"""
    txt_file = docx_file.with_suffix('.txt')
    return txt_file.exists()

def delete_docx_files_safely():
    """حذف ملفات docx بأمان مع التحقق من وجود ملفات txt"""
    
    # البحث عن مجلد knowledge_base_docs
    project_root = Path(".")
    knowledge_base_dir = project_root / "knowledge_base_docs"
    
    if not knowledge_base_dir.exists():
        print(f"❌ مجلد {knowledge_base_dir} غير موجود")
        return
    
    # البحث عن جميع ملفات docx
    docx_files = list(knowledge_base_dir.rglob("*.docx"))
    
    if not docx_files:
        print("✅ لم يتم العثور على ملفات .docx للحذف")
        return
    
    print(f"🔍 تم العثور على {len(docx_files)} ملف .docx")
    
    # فحص وجود ملفات txt المقابلة
    print("\n🔍 فحص وجود ملفات .txt المقابلة...")
    safe_to_delete = []
    missing_txt = []
    
    for docx_file in docx_files:
        if check_txt_exists(docx_file):
            safe_to_delete.append(docx_file)
            print(f"✅ {docx_file.name} → يوجد ملف .txt مقابل")
        else:
            missing_txt.append(docx_file)
            print(f"⚠️  {docx_file.name} → لا يوجد ملف .txt مقابل!")
    
    # عرض النتائج
    print(f"\n📊 النتائج:")
    print(f"✅ آمن للحذف: {len(safe_to_delete)} ملف")
    print(f"⚠️  غير آمن للحذف: {len(missing_txt)} ملف")
    
    if missing_txt:
        print(f"\n❌ ملفات بدون نسخة .txt:")
        for file in missing_txt:
            relative_path = file.relative_to(knowledge_base_dir)
            print(f"   📄 {relative_path}")
        print(f"\n💡 قم بتحويل هذه الملفات أولاً قبل الحذف!")
        
        # خيار حذف الآمنة فقط
        if safe_to_delete:
            print(f"\n🤔 هل تريد حذف الملفات الآمنة فقط ({len(safe_to_delete)} ملف)؟")
            if confirm_deletion():
                delete_files(safe_to_delete, knowledge_base_dir)
        return
    
    # جميع الملفات آمنة للحذف
    print(f"\n✅ جميع ملفات .docx لها نسخ .txt مقابلة")
    print(f"📂 الملفات المرشحة للحذف:")
    
    for docx_file in safe_to_delete:
        relative_path = docx_file.relative_to(knowledge_base_dir)
        print(f"   📄 {relative_path}")
    
    # طلب التأكيد والحذف
    if confirm_deletion():
        delete_files(safe_to_delete, knowledge_base_dir)
    else:
        print("❌ تم إلغاء عملية الحذف")

def delete_files(files_to_delete: list, base_dir: Path):
    """حذف الملفات المحددة"""
    print(f"\n🗑️  بدء حذف {len(files_to_delete)} ملف...")
    
    deleted_count = 0
    failed_count = 0
    
    for docx_file in files_to_delete:
        try:
            # حذف الملف
            docx_file.unlink()
            
            relative_path = docx_file.relative_to(base_dir)
            print(f"🗑️  تم حذف: {relative_path}")
            deleted_count += 1
            
        except Exception as e:
            relative_path = docx_file.relative_to(base_dir)
            print(f"❌ فشل حذف {relative_path}: {e}")
            failed_count += 1
    
    # عرض النتائج النهائية
    print(f"\n🎉 انتهت عملية الحذف!")
    print(f"✅ تم حذف: {deleted_count} ملف")
    if failed_count > 0:
        print(f"❌ فشل حذف: {failed_count} ملف")
    
    print(f"\n💡 الخطوات التالية:")
    print(f"1. تحقق من أن الملفات المحذوفة لم تعد موجودة")
    print(f"2. ارفع التغييرات على GitHub:")
    print(f"   git add .")
    print(f"   git commit -m 'Remove original docx files after conversion to txt'")
    print(f"   git push")

def main():
    """الدالة الرئيسية"""
    print("🗑️  حذف ملفات docx للمعلم الذكي السعودي")
    print("=" * 50)
    print("هذا الكود سيحذف جميع ملفات .docx من مجلدات المشروع")
    print("بعد التأكد من وجود ملفات .txt مقابلة لها")
    print("=" * 50)
    
    # تشغيل عملية الحذف الآمنة
    delete_docx_files_safely()

if __name__ == "__main__":
    main()