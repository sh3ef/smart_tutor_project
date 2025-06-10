# app.py - التطبيق الرئيسي للمعلم الذكي (مع بناء قواعد البيانات التلقائي)

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
    def check_rag_requirements(): # دالة وهمية إذا فشل التحميل
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
VERSION = "3.1 - Cloud Edition with Enhanced RAG" # تم تحديث الإصدار

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

# قائمة بالتحيات والعبارات العامة التي لا تستدعي بحثًا في المنهج
COMMON_GREETINGS_ETC = [
    "سلام عليكم", "السلام عليكم", "سلام", "مرحبا", "أهلا", "اهلا", "هاي", "hello",
    "كيف حالك", "شخبارك", "ايش اخبارك", "شو اخبارك", "كيفك", "ازيك",
    "شكرا", "شكراً", "يعطيك العافية", "مشكور", "thank you", "thanks",
    "صباح الخير", "مساء الخير", "good morning", "good evening",
    "تمام", "بخير", "الحمد لله"
]


def load_environment_variables_silently():
    """تحميل متغيرات البيئة من Streamlit Secrets بصمت (للاستخدام الداخلي)"""
    try:
        if hasattr(st, 'secrets'):
            project_id = st.secrets.get("GCP_PROJECT_ID")
            location = st.secrets.get("GCP_LOCATION", "us-central1") 
            credentials_json = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            
            if project_id and credentials_json:
                try:
                    if isinstance(credentials_json, str):
                        credentials_dict = json.loads(credentials_json)
                    else:
                        credentials_dict = credentials_json
                        
                    required_keys = ['type', 'project_id', 'private_key', 'client_email']
                    missing_keys = [key for key in required_keys if key not in credentials_dict]
                    
                    if not missing_keys:
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            json.dump(credentials_dict, f)
                            credentials_path = f.name
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                        return project_id, location, credentials_path
                except json.JSONDecodeError:
                    return None, None, None
                except Exception:
                    return None, None, None
        return None, None, None
    except Exception:
        return None, None, None

def check_knowledge_base_status(project_id: str, location: str) -> Dict[str, Any]:
    """فحص حالة قواعد المعرفة وإرجاع معلومات التشخيص"""
    if not KB_MANAGER_AVAILABLE:
        return {
            "available": False,
            "reason": "KnowledgeBaseManager غير متاح",
            "docs_exist": False,
            "dbs_exist": False,
            "missing_docs": [],
            "missing_dbs": []
        }
    
    knowledge_docs_path = "knowledge_base_docs"
    docs_exist = os.path.exists(knowledge_docs_path)
    chroma_dbs_path = "chroma_dbs"
    dbs_exist = os.path.exists(chroma_dbs_path)
    
    missing_docs = []
    missing_dbs = []
    
    for grade_key, grade_info in GRADE_SUBJECTS.items():
        for subject_key, subject_name in grade_info['subjects'].items():
            subject_folder = SUBJECT_FOLDERS.get(subject_key, subject_key)
            
            docs_path = os.path.join(knowledge_docs_path, grade_key, subject_folder)
            if not os.path.exists(docs_path) or not os.listdir(docs_path):
                missing_docs.append(f"{grade_key}/{subject_folder}")
            
            collection_name = f"{grade_key}_{subject_folder.replace(' ', '_').lower()}_coll"
            db_path = os.path.join(chroma_dbs_path, collection_name)
            if not os.path.exists(db_path):
                missing_dbs.append(collection_name)
    
    return {
        "available": True,
        "docs_exist": docs_exist,
        "dbs_exist": dbs_exist,
        "missing_docs": missing_docs,
        "missing_dbs": missing_dbs,
        "docs_path": knowledge_docs_path,
        "dbs_path": chroma_dbs_path
    }

@st.cache_data(show_spinner=False) # تم إخفاء spinner من هنا
def build_knowledge_bases_if_needed(project_id: str, location: str, force_rebuild: bool = False) -> Dict[str, Any]:
    """بناء قواعد المعرفة إذا لم تكن موجودة"""
    
    status = check_knowledge_base_status(project_id, location)
    
    if not status["available"]:
        return {"success": False, "message": "مدير قواعد المعرفة غير متاح"}
    
    if not status["docs_exist"] or len(status["missing_docs"]) == len(GRADE_SUBJECTS) * len(SUBJECT_FOLDERS):
        return {
            "success": False,
            "message": "لا توجد ملفات منهج دراسي لبناء قواعد المعرفة منها",
            "suggestion": "تأكد من رفع مجلد knowledge_base_docs مع المشروع"
        }
    
    if status["dbs_exist"] and len(status["missing_dbs"]) == 0 and not force_rebuild:
        return {"success": True, "message": "قواعد المعرفة موجودة ولا تحتاج إعادة بناء"}
    
    results = {
        "success": True,
        "built_databases": [],
        "failed_databases": [],
        "skipped_databases": []
    }
    
    total_subjects = sum(len(grade_info['subjects']) for grade_info in GRADE_SUBJECTS.values())
    current_progress = 0
    
    progress_bar = st.progress(0.0) # تأكد من أن القيمة الأولية هي float
    status_text = st.empty()
    
    for grade_key, grade_info in GRADE_SUBJECTS.items():
        for subject_key, subject_name in grade_info['subjects'].items():
            current_progress += 1
            progress = float(current_progress) / total_subjects # تأكد من أن القسمة float
            
            subject_folder = SUBJECT_FOLDERS.get(subject_key, subject_key)
            collection_name = f"{grade_key}_{subject_folder.replace(' ', '_').lower().replace('الدراسات_الاسلامية', 'islamic_studies')}_coll" # توحيد اسم المجموعة
            
            status_text.text(f"جاري بناء قاعدة المعرفة: {grade_info['name']} - {subject_name}")
            progress_bar.progress(progress)
            
            docs_path = os.path.join("knowledge_base_docs", grade_key, subject_folder)
            if not os.path.exists(docs_path) or not os.listdir(docs_path):
                results["skipped_databases"].append({"name": collection_name, "reason": "لا توجد مستندات"})
                continue
            
            db_path = os.path.join("chroma_dbs", collection_name)
            if os.path.exists(db_path) and not force_rebuild:
                results["skipped_databases"].append({"name": collection_name, "reason": "موجودة مسبقاً"})
                continue
            
            try:
                kb_manager = KnowledgeBaseManager(
                    grade_folder_name=grade_key,
                    subject_folder_name=subject_folder,
                    project_id=project_id,
                    location=location,
                    force_recreate=force_rebuild 
                )
                
                if kb_manager.embedding_function and kb_manager.db:
                    if kb_manager.build_knowledge_base():
                        results["built_databases"].append(collection_name)
                    else:
                        results["failed_databases"].append({"name": collection_name, "reason": "فشل البناء"})
                else:
                    results["failed_databases"].append({"name": collection_name, "reason": "فشل تهيئة المدير"})
            except Exception as e:
                results["failed_databases"].append({"name": collection_name, "reason": f"خطأ: {str(e)}"})
    
    progress_bar.progress(1.0)
    status_text.text("اكتمل بناء قواعد المعرفة!")
    
    import time
    time.sleep(2)
    progress_bar.empty()
    status_text.empty()
    
    return results

@st.cache_resource
def initialize_gemini_client(project_id: str, location: str):
    """تهيئة عميل Gemini مع التخزين المؤقت"""
    if not GEMINI_CLIENT_AVAILABLE:
        return None
    try:
        client = GeminiClientVertexAI(project_id=project_id, location=location, model_name="gemini-1.5-flash-001") # استخدام النموذج الأحدث
        if client.model:
            return client
        return None
    except Exception as e:
        st.error(f"❌ فشل تهيئة عميل Gemini: {e}")
        return None

@st.cache_resource
def initialize_knowledge_base(project_id: str, location: str, grade_key: str, subject_key: str):
    """تهيئة قاعدة المعرفة مع التخزين المؤقت"""
    if not KB_MANAGER_AVAILABLE:
        return None
    try:
        subject_folder = SUBJECT_FOLDERS.get(subject_key, subject_key)
        kb_manager = KnowledgeBaseManager(
            grade_folder_name=grade_key,
            subject_folder_name=subject_folder,
            project_id=project_id,
            location=location
        )
        # التأكد من أن db مهيأ
        if kb_manager.db:
            return kb_manager
        else:
            print(f"⚠️ فشل تهيئة قاعدة بيانات ChromaDB لـ {grade_key}/{subject_folder}")
            return None # أو kb_manager إذا كنت تريد السماح ببنائها لاحقًا
    except Exception as e:
        print(f"❌ فشل تهيئة قاعدة المعرفة لـ {grade_key}/{subject_key}: {e}")
        return None

@st.cache_resource
def initialize_prompt_engine():
    """تهيئة محرك البرومبت"""
    if not PROMPT_ENGINE_AVAILABLE:
        return None
    return UnifiedPromptEngine()

def retrieve_context(kb_manager: Optional[KnowledgeBaseManager], query: str, k_results: int = 3) -> str:
    """استرجاع السياق من قاعدة المعرفة"""
    if not kb_manager or not hasattr(kb_manager, 'db') or not kb_manager.db:
        print(f"⚠️ محاولة استرجاع السياق مع kb_manager غير صالح أو db غير مهيأ.")
        return ""
    try:
        docs = kb_manager.search_documents(query, k_results)
        if docs:
            context_parts = []
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"[مصدر {i} من المنهج]: {doc.page_content}") # توضيح مصدر السياق
            return "\n\n".join(context_parts)
        return ""
    except Exception as e:
        print(f"⚠️ خطأ في استرجاع السياق: {e}")
        return ""

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
    if 'knowledge_bases_built' not in st.session_state:
        st.session_state.knowledge_bases_built = False

def display_sidebar():
    """عرض الشريط الجانبي"""
    with st.sidebar:
        st.title("⚙️ إعدادات المعلم الذكي")
        grade_options = list(GRADE_SUBJECTS.keys())
        grade_display = [GRADE_SUBJECTS[g]['name'] for g in grade_options]
        current_grade_idx = grade_options.index(st.session_state.selected_grade) if st.session_state.selected_grade in grade_options else 0
        selected_grade_idx = st.selectbox(
            "📚 اختر الصف الدراسي:", range(len(grade_display)),
            format_func=lambda x: grade_display[x], index=current_grade_idx, key="grade_selector"
        )
        selected_grade = grade_options[selected_grade_idx]
        
        subjects = GRADE_SUBJECTS[selected_grade]['subjects']
        subject_options = list(subjects.keys())
        subject_display = list(subjects.values())
        current_subject_idx = subject_options.index(st.session_state.selected_subject) if st.session_state.selected_subject in subject_options else 0
        selected_subject_idx = st.selectbox(
            "📖 اختر المادة:", range(len(subject_display)),
            format_func=lambda x: subject_display[x], index=current_subject_idx, key="subject_selector"
        )
        selected_subject = subject_options[selected_subject_idx]
        
        if st.session_state.selected_grade != selected_grade or st.session_state.selected_subject != selected_subject:
            st.session_state.selected_grade = selected_grade
            st.session_state.selected_subject = selected_subject
            # مسح ذاكرة التخزين المؤقت للموارد التي تعتمد على الصف والمادة
            st.cache_resource.clear() # يفضل استهداف دوال محددة إذا أمكن
            st.rerun()
        
        st.divider()
        st.subheader("💬 التحكم في المحادثة")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 محادثة جديدة", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_started = False
                st.rerun()
        with col2:
            if st.button("📤 تصدير المحادثة", use_container_width=True):
                export_conversation()
        
        if st.session_state.messages:
            st.subheader("📊 إحصائيات المحادثة")
            user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            assistant_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
            st.metric("عدد أسئلتك", user_messages)
            st.metric("عدد إجابات المعلم", assistant_messages)
        
        st.divider()
        st.subheader("ℹ️ حالة النظام")
        status_items = [
            ("Gemini Client", GEMINI_CLIENT_AVAILABLE),
            ("Prompt Engine", PROMPT_ENGINE_AVAILABLE),
            ("Knowledge Base", KB_MANAGER_AVAILABLE),
            ("Code Executor", CODE_EXECUTOR_AVAILABLE)
        ]
        for name, available in status_items:
            st.write(f"{'✅' if available else '❌'} {name}")
            
        if KB_MANAGER_AVAILABLE:
            project_id, location, _ = load_environment_variables_silently()
            if project_id:
                kb_status = check_knowledge_base_status(project_id, location)
                st.write(f"📚 ملفات المنهج: {'✅' if kb_status['docs_exist'] else '❌'}")
                st.write(f"🗄️ قواعد البيانات: {'✅' if kb_status['dbs_exist'] and not kb_status['missing_dbs'] else '⚠️' if kb_status['missing_dbs'] else '❌'}")
                if kb_status['missing_dbs']:
                    st.warning(f"{len(kb_status['missing_dbs'])} قاعدة بيانات مفقودة أو تحتاج بناء.")
        
        if KB_MANAGER_AVAILABLE and st.button("🔍 فحص متطلبات RAG", key="check_rag_req_button"):
            with st.spinner("جاري فحص المتطلبات..."):
                try:
                    requirements = check_rag_requirements()
                    for req, available in requirements.items():
                        st.write(f"{'✅' if available else '❌'} {req}")
                except Exception as e:
                    st.error(f"خطأ في فحص المتطلبات: {e}")
        return selected_grade, selected_subject

def process_user_question(question: str, gemini_client, kb_manager: Optional[KnowledgeBaseManager], prompt_engine, grade_key: str, subject_key: str):
    """معالجة سؤال المستخدم وإرجاع الإجابة"""
    normalized_question = question.strip().lower()
    context = ""
    search_status = "kb_unavailable" 

    is_common_phrase = False
    # تحقق أكثر دقة للتحيات والعبارات العامة
    for phrase_parts in [p.lower().split() for p in COMMON_GREETINGS_ETC]:
        q_parts = normalized_question.split()
        if len(q_parts) <= len(phrase_parts) + 2: # اسمح بكلمة أو اثنتين إضافيتين
            match = True
            for i, p_part in enumerate(phrase_parts):
                if i >= len(q_parts) or q_parts[i] != p_part:
                    match = False
                    break
            if match:
                is_common_phrase = True
                break
    
    if is_common_phrase:
        search_status = "not_searched_greeting"
    elif kb_manager and hasattr(kb_manager, 'db') and kb_manager.db:
        with st.spinner("🔍 البحث في المنهج الدراسي..."):
            context = retrieve_context(kb_manager, question)
            if context:
                search_status = "found"
            else:
                search_status = "not_found" 
    
    if prompt_engine:
        specialized_prompt = prompt_engine.get_specialized_prompt(
            question=question,
            app_subject_key=subject_key,
            grade_key=grade_key,
            retrieved_context_str=context if context else None,
            search_status=search_status # تمرير حالة البحث إلى محرك البرومبت
        )
    else:
        specialized_prompt = f"أنت معلم للصف {GRADE_SUBJECTS[grade_key]['name']} في مادة {GRADE_SUBJECTS[grade_key]['subjects'][subject_key]}. اشرح للطفل: {question}"
        if context:
            specialized_prompt += f"\n\nاستعن بالمعلومات التالية من المنهج: {context}"
   
    if gemini_client:
        response = gemini_client.query_for_explanation_and_svg(specialized_prompt)
    else:
        response = {
            "text_explanation": "عذرًا، المعلم الذكي غير جاهز حالياً. يرجى المحاولة لاحقاً.",
            "svg_code": None, "quality_scores": {}, "quality_issues": ["المعلم الذكي غير متاح"]
        }
   
    return {
        'explanation': response.get("text_explanation", "عذرًا، لم أتمكن من إنتاج شرح مناسب."),
        'svg_code': response.get("svg_code"),
        'quality_scores': response.get("quality_scores", {}),
        'quality_issues': response.get("quality_issues", []),
        'search_status': search_status
    }

def add_message(role: str, content: str, **kwargs):
    """إضافة رسالة جديدة للمحادثة"""
    message_id = len(st.session_state.messages)
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "id": message_id,
        **kwargs  # يتضمن search_status, svg_code, إلخ للمساعد
    }
    st.session_state.messages.append(message)

def export_conversation():
    """تصدير المحادثة إلى نص"""
    if not st.session_state.messages:
        st.warning("لا توجد محادثة للتصدير")
        return
    conv_text = f"محادثة مع المعلم الذكي السعودي\n"
    conv_text += f"الصف: {GRADE_SUBJECTS[st.session_state.selected_grade]['name']}\n"
    conv_text += f"المادة: {GRADE_SUBJECTS[st.session_state.selected_grade]['subjects'][st.session_state.selected_subject]}\n"
    conv_text += f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    conv_text += "="*50 + "\n\n"
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            conv_text += f"👤 أنت ({msg['timestamp']}):\n{msg['content']}\n\n"
        elif msg["role"] == "assistant":
            conv_text += f"🤖 المعلم الذكي ({msg['timestamp']}):\n"
            if 'explanation' in msg: conv_text += f"{msg['explanation']}\n"
            if 'svg_code' in msg and msg['svg_code']: conv_text += "[تم إنتاج رسم توضيحي SVG]\n"
            conv_text += "\n"
    st.download_button(
        label="📄 تحميل المحادثة كنص", data=conv_text,
        file_name=f"محادثة_المعلم_الذكي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

def display_message(message: Dict, is_new: bool = False):
    """عرض رسالة واحدة في المحادثة"""
    avatar_map = {"user": "👤", "assistant": "🤖"}
    with st.chat_message(message["role"], avatar=avatar_map.get(message["role"])):
        if message["role"] == "user":
            st.write(f"**أنت:** {message['content']}")
        elif message["role"] == "assistant":
            st.write("**المعلم الذكي:**")
            
            # عرض حالة البحث المعدلة
            if 'search_status' in message:
                status = message['search_status']
                if status == 'found':
                    st.success("✅ تم العثور على معلومات ذات صلة من المنهج الدراسي لهذه المادة.")
                elif status == 'not_found':
                    st.info("ℹ️ لم يتم العثور على معلومات محددة في المنهج الدراسي لهذه المادة. سأجيب بناءً على معرفتي العامة.")
                elif status == 'not_searched_greeting':
                    pass # لا نعرض شيئًا للتحيات، الرد نفسه كافٍ
                elif status == 'kb_unavailable':
                    st.warning("⚠️ قاعدة المعرفة لهذه المادة غير متاحة حاليًا أو لم يتم بناؤها بعد.")
                elif status == 'error': # للتعامل مع أخطاء المعالجة
                     pass # الخطأ نفسه سيُعرض في explanation
            
            if 'explanation' in message: st.write(message['explanation'])
            if 'svg_code' in message and message['svg_code']:
                st.subheader("🎨 الرسم التوضيحي:")
                col1, col2 = st.columns([3, 1])
                with col1:
                    try:
                        st.components.v1.html(
                            f"""<div style="display: flex; justify-content: center; align-items: center;
                                        background-color: white; padding: 20px; border-radius: 10px;
                                        border: 2px solid #e0e0e0;">{message['svg_code']}</div>""", height=400)
                    except Exception as e: st.error(f"❌ خطأ في عرض الرسم: {e}")
                with col2:
                    st.write("💾 **خيارات الحفظ:**")
                    st.download_button(
                        label="⬇️ تحميل SVG", data=message['svg_code'],
                        file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{message.get('id', 'default')}.svg",
                        mime="image/svg+xml", key=f"download_svg_{message.get('id', 'unknown')}_{datetime.now().timestamp()}" # مفتاح فريد جداً
                    )
            if 'quality_scores' in message and message['quality_scores']:
                with st.expander("📊 تقييم جودة الإجابة"):
                    col_q1, col_q2 = st.columns(2)
                    with col_q1: st.metric("جودة الشرح", f"{message['quality_scores'].get('explanation', 0)}%")
                    with col_q2: st.metric("جودة الرسم", f"{message['quality_scores'].get('svg', 0)}%")
                    if 'quality_issues' in message and message['quality_issues']:
                        st.write("**ملاحظات للتحسين:**")
                        for issue in message['quality_issues']: st.write(f"• {issue}")
        if 'timestamp' in message: st.caption(f"🕒 {message['timestamp']}")

def main():
    """الدالة الرئيسية للتطبيق"""
    initialize_session_state()
    st.title(APP_TITLE)
    st.markdown(f"**الإصدار:** {VERSION} | **مخصص للمرحلة الابتدائية**")
   
    project_id, location, _ = load_environment_variables_silently()
    if not project_id:
        st.error("❌ لم يتم تعيين بيانات Google Cloud في Streamlit Secrets. يرجى مراجعة إعدادات النشر.")
        st.stop()
    
    if not st.session_state.knowledge_bases_built:
        st.info("🔄 جاري فحص قواعد المعرفة...")
        kb_status = check_knowledge_base_status(project_id, location)
        
        if not kb_status["docs_exist"]:
            st.warning("⚠️ لا توجد ملفات منهج دراسي (مجلد knowledge_base_docs). سيعمل المعلم الذكي بالمعرفة العامة فقط.")
            st.session_state.knowledge_bases_built = True # نعتبره "مبني" لتجنب الفحص المتكرر
        elif kb_status["missing_dbs"]:
            st.warning(f"⚠️ {len(kb_status['missing_dbs'])} قاعدة بيانات مفقودة أو تحتاج إلى بناء. جاري البناء التلقائي...")
            with st.spinner("🏗️ جاري بناء قواعد المعرفة... قد يستغرق هذا بضع دقائق في المرة الأولى أو عند تغيير المواد."):
                build_result = build_knowledge_bases_if_needed(project_id, location, force_rebuild=False) # يمكن جعل force_rebuild=True للاختبار
                if build_result["success"]:
                    if build_result.get("built_databases"): st.success(f"✅ تم بناء {len(build_result['built_databases'])} قاعدة معرفة بنجاح!")
                    if build_result.get("failed_databases"): st.warning(f"⚠️ فشل بناء {len(build_result['failed_databases'])} قاعدة معرفة.")
                else:
                    st.error(f"❌ {build_result.get('message', 'فشل بناء قواعد المعرفة.')}")
                    if "suggestion" in build_result: st.info(f"💡 {build_result['suggestion']}")
            st.session_state.knowledge_bases_built = True
        else:
            st.success("✅ قواعد المعرفة جاهزة!")
            st.session_state.knowledge_bases_built = True
   
    selected_grade, selected_subject = display_sidebar()
   
    # إعادة تهيئة المكونات عند تغيير الصف أو المادة (يتم التعامل معها عبر st.cache_resource.clear() في الشريط الجانبي)
    # ولكن من الجيد التأكد من استدعائها هنا أيضًا إذا لم يتم مسح ذاكرة التخزين المؤقت
    # قد نحتاج إلى ربط مفاتيح ذاكرة التخزين المؤقت بالصف والمادة بشكل أوضح
    
    with st.spinner("🔄 جاري تهيئة المعلم الذكي..."):
        gemini_client = initialize_gemini_client(project_id, location)
        if not gemini_client and GEMINI_CLIENT_AVAILABLE:
            st.error("❌ فشل تهيئة عميل Gemini. قد تكون هناك مشكلة في الاتصال أو بيانات الاعتماد.")
            st.stop()
        
        # التأكد من أن kb_manager يتم تهيئته بشكل صحيح بعد تغيير المادة
        kb_manager = initialize_knowledge_base(project_id, location, selected_grade, selected_subject)
        prompt_engine = initialize_prompt_engine()

    if not st.session_state.conversation_started:
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
            st.write(f"أهلاً وسهلاً! أنا معلمك الذكي للصف {GRADE_SUBJECTS[selected_grade]['name']} في مادة {GRADE_SUBJECTS[selected_grade]['subjects'][selected_subject]}.")
            if GEMINI_CLIENT_AVAILABLE and gemini_client:
                st.write("اسألني أي سؤال وسأجيبك بشرح مبسط ورسم توضيحي! 😊")
            else:
                st.write("حالياً، النظام في مرحلة الإعداد. يرجى المحاولة لاحقاً أو التأكد من إعدادات الاتصال.")
        st.session_state.conversation_started = True
   
    for message in st.session_state.messages:
        display_message(message)
   
    if prompt := st.chat_input("اكتب سؤالك هنا... 💭"):
        add_message("user", prompt)
        display_message(st.session_state.messages[-1]) # عرض سؤال المستخدم فورًا
       
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
            with st.spinner("🤖 المعلم الذكي يفكر في الإجابة..."):
                try:
                    response_data = process_user_question(
                        prompt, gemini_client, kb_manager, prompt_engine,
                        selected_grade, selected_subject
                    )
                    
                    status = response_data['search_status']
                    if status == 'found':
                        st.success("✅ تم العثور على معلومات ذات صلة من المنهج الدراسي لهذه المادة.")
                    elif status == 'not_found':
                        st.info("ℹ️ لم يتم العثور على معلومات محددة في المنهج الدراسي لهذه المادة. سأجيب بناءً على معرفتي العامة.")
                    elif status == 'not_searched_greeting':
                        pass
                    elif status == 'kb_unavailable':
                        st.warning("⚠️ قاعدة المعرفة لهذه المادة غير متاحة حاليًا أو لم يتم بناؤها بعد.")
                   
                    st.write(response_data['explanation'])
                    if response_data['svg_code']:
                        st.subheader("🎨 الرسم التوضيحي:")
                        col1_resp, col2_resp = st.columns([3, 1])
                        with col1_resp:
                            try:
                                st.components.v1.html(
                                    f"""<div style="display: flex; justify-content: center; align-items: center;
                                                background-color: white; padding: 20px; border-radius: 10px;
                                                border: 2px solid #e0e0e0;">{response_data['svg_code']}</div>""", height=400)
                            except Exception as e_svg_display: st.error(f"❌ خطأ في عرض الرسم: {e_svg_display}")
                        with col2_resp:
                            st.write("💾 **خيارات الحفظ:**")
                            st.download_button(
                                label="⬇️ تحميل SVG", data=response_data['svg_code'],
                                file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}_new.svg",
                                mime="image/svg+xml", key=f"download_svg_new_{len(st.session_state.messages)}_{datetime.now().timestamp()}"
                            )
                    if response_data['quality_scores']:
                        with st.expander("📊 تقييم جودة الإجابة"):
                            col_qs1, col_qs2 = st.columns(2)
                            with col_qs1: st.metric("جودة الشرح", f"{response_data['quality_scores'].get('explanation', 0)}%")
                            with col_qs2: st.metric("جودة الرسم", f"{response_data['quality_scores'].get('svg', 0)}%")
                    
                    add_message("assistant", "", **response_data)
                   
                except Exception as e_proc:
                    error_msg = f"❌ حدث خطأ أثناء معالجة طلبك: {e_proc}"
                    st.error(error_msg)
                    traceback.print_exc() # لطباعة الخطأ في الطرفية للمطور
                    add_message("assistant", error_msg, search_status="error")
   
    with st.expander("❓ كيفية استخدام المعلم الذكي"):
        st.markdown("""
        ### 🎯 نصائح للحصول على أفضل إجابة:
        **للغة العربية:** "علمني حرف الألف مع أمثلة", "ما هي حركات الحروف؟"
        **للرياضيات:** "اشرح لي جمع 2+3 بالرسم", "ما هو الشكل المربع؟"
        **للعلوم:** "ما هي أجزاء النبات؟", "اشرح لي الحواس الخمس"
        **للتربية الإسلامية:** "علمني كيفية الوضوء", "ما هي أركان الإسلام؟"
        **للغة الإنجليزية:** "Teach me the letter A", "What colors do you know?"
        ### 💡 ميزات المحادثة المستمرة:
        - **يتذكر**: جميع أسئلتك وإجاباتي السابقة في هذه الجلسة.
        - **يتطور**: يمكنك البناء على الأسئلة السابقة.
        - **يحفظ**: يمكنك تصدير المحادثة كاملة.
        - **ينظف**: يمكنك بدء محادثة جديدة في أي وقت.
        """)
   
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💡 المعلم الذكي السعودي - مدعوم بتقنية Gemini AI و RAG<br>
    🎯 مخصص للمرحلة الابتدائية - منهج المملكة العربية السعودية<br>
    🔐 آمن ومحمي - جميع البيانات الحساسة في Streamlit Secrets<br>
    💬 يحفظ تاريخ محادثتك ويتذكر الأسئلة السابقة (في نفس الجلسة)
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
