# tutor_ai/code_executor.py
import os
import traceback
import streamlit as st

def save_svg_content_to_file(svg_content_string: str, output_svg_path: str) -> bool:
    """
    يحفظ سلسلة نصية تحتوي على كود SVG إلى ملف .svg.
    """
    if not svg_content_string:
        st.error("CODE_SAVER (SVG): لم يتم توفير محتوى SVG ليتم حفظه.")
        print("خطأ CODE_SAVER (SVG): لم يتم توفير محتوى SVG.")
        return False

    print(f"CODE_SAVER (SVG): سيتم محاولة حفظ محتوى SVG في: {output_svg_path}")

    try:
        output_dir = os.path.dirname(output_svg_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"CODE_SAVER (SVG): تم إنشاء المجلد: {output_dir}")

        with open(output_svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content_string)
        
        if os.path.exists(output_svg_path) and os.path.getsize(output_svg_path) > 50: 
            print(f"CODE_SAVER (SVG): تم حفظ ملف SVG بنجاح: {output_svg_path}, الحجم: {os.path.getsize(output_svg_path)} بايت")
            return True
        else:
            st.error("فشل حفظ ملف SVG أو أن الملف الناتج فارغ/صغير جدًا.")
            if os.path.exists(output_svg_path): print(f"CODE_SAVER (SVG) خطأ: ملف SVG صغير/فارغ: {output_svg_path}, الحجم: {os.path.getsize(output_svg_path)}")
            else: print(f"CODE_SAVER (SVG) خطأ: لم يتم إنشاء ملف SVG: {output_svg_path}")
            return False

    except Exception as e:
        st.error(f"حدث خطأ فادح أثناء حفظ ملف SVG: {e}")
        print(f"CODE_SAVER (SVG) خطأ فادح أثناء حفظ الملف: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("code_executor.py تم تشغيله مباشرة (عادة للاختبارات).")
    test_svg_content = '<svg width="100" height="100"><circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" /></svg>'
    test_dir = "generated_svg_test"
    if not os.path.exists(test_dir): os.makedirs(test_dir)
    test_path = os.path.join(test_dir, "test_save.svg")
    if save_svg_content_to_file(test_svg_content, test_path):
        print(f"اختبار الحفظ نجح، تم إنشاء الملف: {test_path}")
    else:
        print(f"اختبار الحفظ فشل.")