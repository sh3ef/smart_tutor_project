# app.py - التطبيق الرئيسي للمعلم الذكي (النسخة الآمنة)

import os
import sys
import streamlit as st
import traceback
import json
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List

# إصلاحات النظام
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    import distutils
except ImportError:
    try:
        import setuptools
        sys.modules['distutils'] = setuptools
        print("✅ Fixed distutils with setuptools")
    except ImportError:
        print("⚠️ Neither distutils nor setuptools available, continuing...")
        pass

try:
    import sqlite3
    sqlite_version = sqlite3.sqlite_version_info
    print(f"Current SQLite version: {sqlite3.sqlite_version}")
    
    if sqlite_version < (3, 35, 0):
        try:
            __import__('pysqlite3')
            sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
            print("✅ Successfully replaced sqlite3 with pysqlite3")
        except ImportError:
            print("⚠️ pysqlite3 not available, continuing with system SQLite")
    else:
        print("✅ SQLite version is sufficient")
        
except Exception as e:
    print(f"Warning: SQLite fix failed: {e}")

# تحميل الوحدات المخصصة بأمان
print("🔄 جاري تحميل وحدات المعلم الذكي...")

try:
    print("📦 محاولة استيراد GeminiClientVertexAI...")
    from tutor_ai.gemini_client import GeminiClientVertexAI
    GEMINI_CLIENT_AVAILABLE = True
    print("✅ تم تحميل GeminiClientVertexAI بنجاح")
except Exception as e:
    print(f"❌ فشل تحميل Gemini client: {e}")
    GEMINI_CLIENT_AVAILABLE = False

try:
    print("📦 محاولة استيراد UnifiedPromptEngine...")
    from tutor_ai.prompt_engineering import UnifiedPromptEngine
    PROMPT_ENGINE_AVAILABLE = True
    print("✅ تم تحميل UnifiedPromptEngine بنجاح")
except Exception as e:
    print(f"❌ فشل تحميل Prompt engine: {e}")
    PROMPT_ENGINE_AVAILABLE = False

try:
    print("📦 محاولة استيراد KnowledgeBaseManager...")
    from tutor_ai.knowledge_base_manager import KnowledgeBaseManager, check_rag_requirements
    KB_MANAGER_AVAILABLE = True
    print("✅ تم تحميل KnowledgeBaseManager بنجاح")
except Exception as e:
    print(f"❌ فشل تحميل Knowledge base manager: {e}")
    KB_MANAGER_AVAILABLE = False
    def check_rag_requirements():
        return {"Status": False}

try:
    print("📦 محاولة استيراد save_svg_content_to_file...")
    from tutor_ai.code_executor import save_svg_content_to_file
    CODE_EXECUTOR_AVAILABLE = True
    print("✅ تم تحميل save_svg_content_to_file بنجاح")
except Exception as e:
    print(f"❌ فشل تحميل Code executor: {e}")
    CODE_EXECUTOR_AVAILABLE = False

print("🏁 انتهى تحميل الوحدات:")
print(f"   - Gemini Client: {'✅' if GEMINI_CLIENT_AVAILABLE else '❌'}")
print(f"   - Prompt Engine: {'✅' if PROMPT_ENGINE_AVAILABLE else '❌'}")
print(f"   - Knowledge Base: {'✅' if KB_MANAGER_AVAILABLE else '❌'}")
print(f"   - Code Executor: {'✅' if CODE_EXECUTOR_AVAILABLE else '❌'}")

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="المعلم الذكي السعودي",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# متغيرات التطبيق العامة
APP_TITLE = "🤖 المعلم الذكي السعودي"
VERSION = "3.0 - Secure Edition"

# إعدادات الصفوف والمواد
GRADE_SUBJECTS = {
    'grade_1': {
        'name': 'الصف الأول الابتدائي',
        'subjects': {
            'arabic': 'لغتي الجميلة',
            'math': 'الرياضيات',
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية'
        }
    },
    'grade_2': {
        'name': 'الصف الثاني الابتدائي',
        'subjects': {
            'arabic': 'لغتي الجميلة',
            'math': 'الرياضيات',
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية'
        }
    },
    'grade_3': {
        'name': 'الصف الثالث الابتدائي',
        'subjects': {
            'arabic': 'لغتي الجميلة',
            'math': 'الرياضيات',
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية'
        }
    },
    'grade_4': {
        'name': 'الصف الرابع الابتدائي',
        'subjects': {
            'arabic': 'لغتي الجميلة',
            'math': 'الرياضيات',
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية'
        }
    },
    'grade_5': {
        'name': 'الصف الخامس الابتدائي',
        'subjects': {
            'arabic': 'لغتي الجميلة',
            'math': 'الرياضيات',
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية'
        }
    },
    'grade_6': {
        'name': 'الصف السادس الابتدائي',
        'subjects': {
            'arabic': 'لغتي الجميلة',
            'math': 'الرياضيات',
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية'
        }
    }
}

SUBJECT_FOLDERS = {
    'arabic': 'lughati',
    'math': 'Math',
    'science': 'Science',
    'islamic': 'الدراسات الاسلامية',
    'english': 'English'
}

def load_environment_variables():
    """تحميل متغيرات البيئة من Streamlit Secrets فقط (آمن)"""
    try:
        # عرض معلومات debugging للمستخدم
        st.write("🔍 **تشخيص النظام:**")
        
        # القراءة من Streamlit Secrets فقط
        try:
            if hasattr(st, 'secrets'):
                st.success("✅ وحدة Streamlit Secrets متاحة")
                
                # عرض المفاتيح المتاحة (بدون القيم الحساسة)
                try:
                    available_keys = list(st.secrets.keys())
                    st.write(f"📋 المفاتيح المتاحة في Secrets: {available_keys}")
                    print(f"DEBUG: Available secret keys: {available_keys}")
                except Exception as e:
                    st.warning(f"⚠️ لا يمكن قراءة قائمة المفاتيح: {e}")
                
                # قراءة المتغيرات المطلوبة
                project_id = st.secrets.get("GCP_PROJECT_ID")
                location = st.secrets.get("GCP_LOCATION", "us-central1") 
                credentials_json = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                
                if project_id:
                    st.success(f"✅ GCP_PROJECT_ID موجود: {project_id}")
                else:
                    st.error("❌ GCP_PROJECT_ID غير موجود في Secrets")
                
                if credentials_json:
                    st.success("✅ GOOGLE_APPLICATION_CREDENTIALS_JSON موجود")
                    
                    # التحقق من صحة JSON
                    try:
                        if isinstance(credentials_json, str):
                            credentials_dict = json.loads(credentials_json)
                        else:
                            credentials_dict = credentials_json
                            
                        # التحقق من المفاتيح المطلوبة
                        required_keys = ['type', 'project_id', 'private_key', 'client_email']
                        missing_keys = [key for key in required_keys if key not in credentials_dict]
                        
                        if missing_keys:
                            st.error(f"❌ مفاتيح مفقودة في بيانات الاعتماد: {missing_keys}")
                        else:
                            st.success("✅ بيانات الاعتماد JSON صالحة")
                            st.write(f"🏢 Project ID في الـ JSON: {credentials_dict.get('project_id')}")
                            st.write(f"📧 Client Email: {credentials_dict.get('client_email')}")
                            
                            # إنشاء ملف مؤقت للمفاتيح
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                                json.dump(credentials_dict, f)
                                credentials_path = f.name
                            
                            # تعيين متغير البيئة
                            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                            st.success(f"✅ تم إنشاء ملف مفاتيح مؤقت: {credentials_path}")
                            
                    except json.JSONDecodeError as e:
                        st.error(f"❌ خطأ في تحليل JSON: {e}")
                        credentials_path = None
                    except Exception as e:
                        st.error(f"❌ خطأ في معالجة بيانات الاعتماد: {e}")
                        credentials_path = None
                else:
                    st.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON غير موجود في Secrets")
                    credentials_path = None
                    
            else:
                st.error("❌ وحدة Streamlit Secrets غير متاحة")
                return None, None, None
                    
        except Exception as e:
            st.error(f"⚠️ فشل قراءة Streamlit secrets: {e}")
            return None, None, None
       
        if not project_id:
            st.error("❌ لم يتم تعيين GCP_PROJECT_ID في Streamlit Secrets")
            st.info("💡 يرجى إضافة المتغيرات المطلوبة في Streamlit Cloud Secrets")
            
            # عرض مثال على التنسيق المطلوب
            st.code('''
GCP_PROJECT_ID = "your-project-id"
GCP_LOCATION = "us-central1"
GOOGLE_APPLICATION_CREDENTIALS_JSON = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "service-account@your-project.iam.gserviceaccount.com"
}
"""
            ''', language='toml')
            
            return None, None, None
           
        # التحقق النهائي
        if not credentials_path:
            st.warning("⚠️ لم يتم العثور على بيانات الاعتماد")
        else:
            if os.path.exists(credentials_path):
                st.success(f"✅ ملف بيانات الاعتماد موجود: {credentials_path}")
            else:
                st.error(f"❌ ملف بيانات الاعتماد غير موجود: {credentials_path}")
           
        return project_id, location, credentials_path
       
    except Exception as e:
        st.error(f"❌ خطأ في تحميل متغيرات البيئة: {e}")
        return None, None, None

@st.cache_resource
def initialize_gemini_client(project_id: str, location: str):
    """تهيئة عميل Gemini مع التخزين المؤقت"""
    if not GEMINI_CLIENT_AVAILABLE:
        st.error("❌ وحدة Gemini Client غير متاحة")
        return None
        
    try:
        client = GeminiClientVertexAI(
            project_id=project_id,
            location=location,
            model_name="gemini-2.0-flash"
        )
        if client.model:
            return client
        return None
    except Exception as e:
        st.error(f"❌ فشل تهيئة عميل Gemini: {e}")
        return None

@st.cache_resource
def initialize_prompt_engine():
    """تهيئة محرك البرومبت"""
    if not PROMPT_ENGINE_AVAILABLE:
        st.error("❌ وحدة محرك البرومبت غير متاحة")
        return None
    return UnifiedPromptEngine()

def initialize_session_state():
    """تهيئة حالة الجلسة للمحادثة المستمرة"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
   
    if 'selected_grade' not in st.session_state:
        st.session_state.selected_grade = 'grade_1'
   
    if 'selected_subject' not in st.session_state:
        st.session_state.selected_subject = 'arabic'
   
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False

def display_sidebar():
    """عرض الشريط الجانبي"""
    with st.sidebar:
        st.title("⚙️ إعدادات المعلم الذكي")
       
        # اختيار الصف
        grade_options = list(GRADE_SUBJECTS.keys())
        grade_display = [GRADE_SUBJECTS[g]['name'] for g in grade_options]
       
        current_grade_idx = grade_options.index(st.session_state.selected_grade) if st.session_state.selected_grade in grade_options else 0
       
        selected_grade_idx = st.selectbox(
            "📚 اختر الصف الدراسي:",
            range(len(grade_display)),
            format_func=lambda x: grade_display[x],
            index=current_grade_idx,
            key="grade_selector"
        )
        selected_grade = grade_options[selected_grade_idx]
       
        # اختيار المادة
        subjects = GRADE_SUBJECTS[selected_grade]['subjects']
        subject_options = list(subjects.keys())
        subject_display = list(subjects.values())
       
        current_subject_idx = subject_options.index(st.session_state.selected_subject) if st.session_state.selected_subject in subject_options else 0
       
        selected_subject_idx = st.selectbox(
            "📖 اختر المادة:",
            range(len(subject_display)),
            format_func=lambda x: subject_display[x],
            index=current_subject_idx,
            key="subject_selector"
        )
        selected_subject = subject_options[selected_subject_idx]
       
        # تحديث session state
        if st.session_state.selected_grade != selected_grade or st.session_state.selected_subject != selected_subject:
            st.session_state.selected_grade = selected_grade
            st.session_state.selected_subject = selected_subject
            st.rerun()
       
        st.divider()
       
        # أزرار التحكم في المحادثة
        st.subheader("💬 التحكم في المحادثة")
       
        col1, col2 = st.columns(2)
       
        with col1:
            if st.button("🆕 محادثة جديدة", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_started = False
                st.rerun()
       
        # عرض معلومات النظام
        st.divider()
        st.subheader("ℹ️ معلومات النظام")
        
        # فحص حالة الوحدات
        status_items = [
            ("Gemini Client", GEMINI_CLIENT_AVAILABLE),
            ("Prompt Engine", PROMPT_ENGINE_AVAILABLE),
            ("Knowledge Base", KB_MANAGER_AVAILABLE),
            ("Code Executor", CODE_EXECUTOR_AVAILABLE)
        ]
        
        for name, available in status_items:
            status = "✅" if available else "❌"
            st.write(f"{status} {name}")
       
        return selected_grade, selected_subject

def process_user_question(question: str, gemini_client, prompt_engine, grade_key: str, subject_key: str):
    """معالجة سؤال المستخدم وإرجاع الإجابة"""
   
    # إنشاء البرومبت المخصص
    if prompt_engine:
        specialized_prompt = prompt_engine.get_specialized_prompt(
            question=question,
            app_subject_key=subject_key,
            grade_key=grade_key,
            retrieved_context_str=None
        )
    else:
        # برومبت بسيط إذا لم يكن محرك البرومبت متاحاً
        specialized_prompt = f"أنت معلم للصف {grade_key} في مادة {subject_key}. اشرح للطفل: {question}"
   
    # إرسال الطلب لـ Gemini
    if gemini_client:
        response = gemini_client.query_for_explanation_and_svg(specialized_prompt)
    else:
        # رد افتراضي إذا لم يكن Gemini متاحاً
        response = {
            "text_explanation": "عذرًا، المعلم الذكي غير جاهز حالياً. يرجى المحاولة لاحقاً.",
            "svg_code": None,
            "quality_scores": {},
            "quality_issues": ["المعلم الذكي غير متاح"]
        }
   
    return {
        'explanation': response.get("text_explanation", "عذرًا، لم أتمكن من إنتاج شرح مناسب."),
        'svg_code': response.get("svg_code"),
        'quality_scores': response.get("quality_scores", {}),
        'quality_issues': response.get("quality_issues", []),
        'search_status': 'not_found'
    }

def add_message(role: str, content: str, **kwargs):
    """إضافة رسالة جديدة للمحادثة"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "id": len(st.session_state.messages),
        **kwargs
    }
    st.session_state.messages.append(message)

def display_message(message: Dict, is_new: bool = False):
    """عرض رسالة واحدة في المحادثة"""
   
    if message["role"] == "user":
        # رسالة المستخدم
        with st.chat_message("user", avatar="👤"):
            st.write(f"**أنت:** {message['content']}")
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")
   
    elif message["role"] == "assistant":
        # رسالة المساعد
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
           
            # عرض الشرح النصي
            if 'explanation' in message:
                st.write(message['explanation'])
           
            # عرض الرسم SVG إذا كان موجوداً
            if 'svg_code' in message and message['svg_code']:
                st.subheader("🎨 الرسم التوضيحي:")
               
                col1, col2 = st.columns([3, 1])
               
                with col1:
                    try:
                        st.components.v1.html(
                            f"""
                            <div style="display: flex; justify-content: center; align-items: center;
                                        background-color: white; padding: 20px; border-radius: 10px;
                                        border: 2px solid #e0e0e0;">
                                {message['svg_code']}
                            </div>
                            """,
                            height=400
                        )
                    except Exception as e:
                        st.error(f"❌ خطأ في عرض الرسم: {e}")
               
                with col2:
                    st.write("💾 **خيارات الحفظ:**")
                   
                    # تحميل SVG
                    st.download_button(
                        label="⬇️ تحميل SVG",
                        data=message['svg_code'],
                        file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                        mime="image/svg+xml",
                        key=f"download_svg_{message.get('id', 'unknown')}"
                    )
           
            # عرض الوقت
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")

def main():
    """الدالة الرئيسية للتطبيق"""
   
    # تهيئة حالة الجلسة
    initialize_session_state()
   
    st.title(APP_TITLE)
    st.markdown(f"**الإصدار:** {VERSION} | **مخصص للمرحلة الابتدائية**")
   
    # عرض حالة النظام
    if not GEMINI_CLIENT_AVAILABLE:
        st.error("❌ وحدة Gemini Client غير متاحة")
   
    # تحميل متغيرات البيئة
    project_id, location, credentials_path = load_environment_variables()
    if not project_id:
        st.stop()
   
    # عرض الشريط الجانبي
    selected_grade, selected_subject = display_sidebar()
   
    # تهيئة المكونات
    with st.spinner("🔄 جاري تهيئة المعلم الذكي..."):
        gemini_client = initialize_gemini_client(project_id, location)
        if not gemini_client and GEMINI_CLIENT_AVAILABLE:
            st.error("❌ فشل تهيئة عميل Gemini")
            st.stop()
       
        prompt_engine = initialize_prompt_engine()
   
    # عرض رسالة الترحيب إذا لم تبدأ المحادثة
    if not st.session_state.conversation_started:
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
            st.write(f"أهلاً وسهلاً! أنا معلمك الذكي للصف {GRADE_SUBJECTS[selected_grade]['name']} في مادة {GRADE_SUBJECTS[selected_grade]['subjects'][selected_subject]}.")
            if GEMINI_CLIENT_AVAILABLE and gemini_client:
                st.write("اسألني أي سؤال وسأجيبك بشرح مبسط ورسم توضيحي! 😊")
            else:
                st.write("حالياً، النظام في مرحلة الإعداد. يرجى المحاولة لاحقاً.")
       
        st.session_state.conversation_started = True
   
    # عرض المحادثة السابقة
    for message in st.session_state.messages:
        display_message(message)
   
    # مربع إدخال السؤال الجديد
    if prompt := st.chat_input("اكتب سؤالك هنا... 💭"):
        # إضافة سؤال المستخدم
        add_message("user", prompt)
        display_message(st.session_state.messages[-1])
       
        # معالجة السؤال وإنتاج الإجابة
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
           
            with st.spinner("🤖 المعلم الذكي يفكر في الإجابة..."):
                try:
                    # معالجة السؤال
                    response_data = process_user_question(
                        prompt, gemini_client, prompt_engine,
                        selected_grade, selected_subject
                    )
                   
                    # عرض الشرح
                    st.write(response_data['explanation'])
                   
                    # عرض الرسم إذا كان موجوداً
                    if response_data['svg_code']:
                        st.subheader("🎨 الرسم التوضيحي:")
                       
                        col1, col2 = st.columns([3, 1])
                       
                        with col1:
                            try:
                                st.components.v1.html(
                                    f"""
                                    <div style="display: flex; justify-content: center; align-items: center;
                                                background-color: white; padding: 20px; border-radius: 10px;
                                                border: 2px solid #e0e0e0;">
                                        {response_data['svg_code']}
                                    </div>
                                    """,
                                    height=400
                                )
                            except Exception as e:
                                st.error(f"❌ خطأ في عرض الرسم: {e}")
                       
                        with col2:
                            st.write("💾 **خيارات الحفظ:**")
                            st.download_button(
                                label="⬇️ تحميل SVG",
                                data=response_data['svg_code'],
                                file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                                mime="image/svg+xml",
                                key=f"download_svg_new"
                            )
                   
                    # إضافة إجابة المساعد للمحادثة
                    add_message("assistant", "", **response_data)
                   
                except Exception as e:
                    error_msg = f"❌ حدث خطأ: {e}"
                    st.error(error_msg)
                    add_message("assistant", error_msg)
   
    # قسم المساعدة
    with st.expander("❓ كيفية استخدام المعلم الذكي"):
        st.markdown("""
        ### 🎯 نصائح للحصول على أفضل إجابة:
       
        **للغة العربية:**
        - "علمني حرف الألف مع أمثلة"
        - "ما هي حركات الحروف؟"
       
        **للرياضيات:**
        - "اشرح لي جمع 2+3 بالرسم"
        - "ما هو الشكل المربع؟"
       
        **للعلوم:**
        - "ما هي أجزاء النبات؟"
        - "اشرح لي الحواس الخمس"
        """)
   
    # معلومات إضافية في التذييل
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💡 المعلم الذكي السعودي - مدعوم بتقنية Gemini AI<br>
    🎯 مخصص للمرحلة الابتدائية - منهج المملكة العربية السعودية<br>
    🔐 آمن ومحمي - جميع البيانات الحساسة في Streamlit Secrets
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()