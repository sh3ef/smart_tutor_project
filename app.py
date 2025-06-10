# app.py - التطبيق الرئيسي للمعلم الذكي (مع بناء قواعد البيانات التلقائي) - محدث

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
VERSION = "3.1 - Cloud Edition المحدث"

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

def load_environment_variables_silently():
    """تحميل متغيرات البيئة من Streamlit Secrets بصمت (للاستخدام الداخلي)"""
    try:
        # القراءة من Streamlit Secrets فقط
        if hasattr(st, 'secrets'):
            # قراءة المتغيرات المطلوبة
            project_id = st.secrets.get("GCP_PROJECT_ID")
            location = st.secrets.get("GCP_LOCATION", "us-central1") 
            credentials_json = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            
            if project_id and credentials_json:
                # التحقق من صحة JSON
                try:
                    if isinstance(credentials_json, str):
                        credentials_dict = json.loads(credentials_json)
                    else:
                        credentials_dict = credentials_json
                        
                    # التحقق من المفاتيح المطلوبة
                    required_keys = ['type', 'project_id', 'private_key', 'client_email']
                    missing_keys = [key for key in required_keys if key not in credentials_dict]
                    
                    if not missing_keys:
                        # إنشاء ملف مؤقت للمفاتيح
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            json.dump(credentials_dict, f)
                            credentials_path = f.name
                        
                        # تعيين متغير البيئة
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
    
    # فحص وجود مجلد knowledge_base_docs
    knowledge_docs_path = "knowledge_base_docs"
    docs_exist = os.path.exists(knowledge_docs_path)
    
    # فحص وجود مجلد chroma_dbs
    chroma_dbs_path = "chroma_dbs"
    dbs_exist = os.path.exists(chroma_dbs_path)
    
    missing_docs = []
    missing_dbs = []
    
    # فحص تفصيلي للملفات والقواعد المطلوبة
    for grade_key, grade_info in GRADE_SUBJECTS.items():
        for subject_key, subject_name in grade_info['subjects'].items():
            subject_folder = SUBJECT_FOLDERS.get(subject_key, subject_key)
            
            # فحص مجلد المستندات
            docs_path = os.path.join(knowledge_docs_path, grade_key, subject_folder)
            if not os.path.exists(docs_path) or not os.listdir(docs_path):
                missing_docs.append(f"{grade_key}/{subject_folder}")
            
            # فحص قاعدة البيانات
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

@st.cache_data
def build_knowledge_bases_if_needed(project_id: str, location: str, force_rebuild: bool = False) -> Dict[str, Any]:
    """بناء قواعد المعرفة إذا لم تكن موجودة"""
    
    status = check_knowledge_base_status(project_id, location)
    
    if not status["available"]:
        return {"success": False, "message": "مدير قواعد المعرفة غير متاح"}
    
    # إذا لم تكن هناك مستندات أساساً، لا يمكن البناء
    if not status["docs_exist"] or len(status["missing_docs"]) == len(GRADE_SUBJECTS) * len(SUBJECT_FOLDERS):
        return {
            "success": False,
            "message": "لا توجد ملفات منهج دراسي لبناء قواعد المعرفة منها",
            "suggestion": "تأكد من رفع مجلد knowledge_base_docs مع المشروع"
        }
    
    # إذا كانت قواعد البيانات موجودة ولم يُطلب إعادة البناء
    if status["dbs_exist"] and len(status["missing_dbs"]) == 0 and not force_rebuild:
        return {"success": True, "message": "قواعد المعرفة موجودة ولا تحتاج إعادة بناء"}
    
    # بناء قواعد المعرفة المفقودة
    results = {
        "success": True,
        "built_databases": [],
        "failed_databases": [],
        "skipped_databases": []
    }
    
    total_subjects = sum(len(grade_info['subjects']) for grade_info in GRADE_SUBJECTS.values())
    current_progress = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for grade_key, grade_info in GRADE_SUBJECTS.items():
        for subject_key, subject_name in grade_info['subjects'].items():
            current_progress += 1
            progress = current_progress / total_subjects
            
            subject_folder = SUBJECT_FOLDERS.get(subject_key, subject_key)
            collection_name = f"{grade_key}_{subject_folder.replace(' ', '_').lower()}_coll"
            
            status_text.text(f"جاري بناء قاعدة المعرفة: {grade_info['name']} - {subject_name}")
            progress_bar.progress(progress)
            
            # تحقق من وجود المستندات لهذه المادة
            docs_path = os.path.join("knowledge_base_docs", grade_key, subject_folder)
            if not os.path.exists(docs_path) or not os.listdir(docs_path):
                results["skipped_databases"].append({
                    "name": collection_name,
                    "reason": "لا توجد مستندات"
                })
                continue
            
            # تحقق من وجود قاعدة البيانات
            db_path = os.path.join("chroma_dbs", collection_name)
            if os.path.exists(db_path) and not force_rebuild:
                results["skipped_databases"].append({
                    "name": collection_name,
                    "reason": "موجودة مسبقاً"
                })
                continue
            
            try:
                # إنشاء مدير قاعدة المعرفة
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
                        results["failed_databases"].append({
                            "name": collection_name,
                            "reason": "فشل البناء"
                        })
                else:
                    results["failed_databases"].append({
                        "name": collection_name,
                        "reason": "فشل تهيئة المدير"
                    })
                    
            except Exception as e:
                results["failed_databases"].append({
                    "name": collection_name,
                    "reason": f"خطأ: {str(e)}"
                })
    
    progress_bar.progress(1.0)
    status_text.text("اكتمل بناء قواعد المعرفة!")
    
    # تنظيف شريط التقدم بعد قليل
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
        return kb_manager
    except Exception as e:
        print(f"❌ فشل تهيئة قاعدة المعرفة: {e}")
        return None

@st.cache_resource
def initialize_prompt_engine():
    """تهيئة محرك البرومبت"""
    if not PROMPT_ENGINE_AVAILABLE:
        return None
    return UnifiedPromptEngine()

def retrieve_context(kb_manager: Optional[any], query: str, k_results: int = 3) -> str:
    """استرجاع السياق من قاعدة المعرفة"""
    if not kb_manager or not hasattr(kb_manager, 'db') or not kb_manager.db:
        return ""
   
    try:
        docs = kb_manager.search_documents(query, k_results)
        if docs:
            context_parts = []
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"[مصدر {i}]: {doc.page_content}")
            return "\n\n".join(context_parts)
        return ""
    except Exception as e:
        print(f"⚠️ خطأ في استرجاع السياق: {e}")
        return ""

def should_search_in_curriculum(question: str, subject_key: str) -> bool:
    """
    تحديد ما إذا كان السؤال يحتاج البحث في المنهج أم لا
    """
    # أسئلة عامة لا تحتاج بحث في المنهج
    general_greetings = [
        "السلام عليكم", "مرحبا", "أهلا", "صباح الخير", 
        "مساء الخير", "كيف حالك", "أهلاً وسهلاً", "حياك الله",
        "وعليكم السلام", "شكرا", "شكراً"
    ]
    
    # أسئلة شخصية عامة
    personal_questions = [
        "ما اسمك", "من أنت", "ماذا تفعل", "كيف يمكنك مساعدتي",
        "هل أنت ذكي", "كم عمرك"
    ]
    
    question_lower = question.lower().strip()
    
    # فحص التحيات
    for greeting in general_greetings:
        if greeting in question_lower:
            return False
    
    # فحص الأسئلة الشخصية        
    for personal in personal_questions:
        if personal in question_lower:
            return False
    
    # كلمات مفاتيح تشير لمحتوى تعليمي حقيقي
    educational_keywords = {
        'arabic': ['حرف', 'كلمة', 'جملة', 'قراءة', 'كتابة', 'إملاء', 'نحو', 'شعر', 'نص', 'قصة'],
        'math': ['رقم', 'عدد', 'جمع', 'طرح', 'ضرب', 'قسمة', 'شكل', 'هندسة', 'حساب', 'مسألة', 'عملية'],
        'science': ['نبات', 'حيوان', 'ماء', 'هواء', 'تجربة', 'علم', 'طبيعة', 'جسم', 'كائن', 'بيئة'],
        'islamic': ['صلاة', 'وضوء', 'دعاء', 'قرآن', 'سورة', 'حديث', 'أركان', 'إيمان', 'إسلام'],
        'english': ['letter', 'word', 'alphabet', 'english', 'انجليزي', 'انجليزية']
    }
    
    subject_keywords = educational_keywords.get(subject_key, [])
    for keyword in subject_keywords:
        if keyword in question_lower:
            return True
    
    # إذا كان السؤال طويل ومعقد، احتمال أنه تعليمي
    if len(question.split()) > 5:
        return True
        
    return False

def should_generate_svg(question: str, explanation: str, subject_key: str) -> bool:
    """
    تحديد ما إذا كان السؤال/الشرح يحتاج رسماً توضيحياً
    """
    # أسئلة لا تحتاج رسم
    no_svg_patterns = [
        "السلام عليكم", "مرحبا", "أهلا", "شكرا", "ما اسمك", 
        "من أنت", "كيف حالك", "صباح الخير", "مساء الخير",
        "وعليكم السلام", "حياك الله", "أهلاً وسهلاً", "شكراً"
    ]
    
    question_lower = question.lower().strip()
    
    # فحص الأنماط التي لا تحتاج رسم
    for pattern in no_svg_patterns:
        if pattern in question_lower:
            return False
    
    # كلمات تشير لحاجة للرسم
    svg_needed_keywords = {
        'general': ['ارسم', 'وضح', 'اشرح', 'كيف يبدو', 'شكل', 'صورة', 'مخطط'],
        'arabic': ['حرف', 'احرف', 'كلمة', 'كلمات'],
        'math': ['رقم', 'ارقام', 'شكل هندسي', 'مثلث', 'دائرة', 'مربع', 'جمع', 'طرح', 'عملية'],
        'science': ['نبات', 'حيوان', 'اجزاء', 'دورة', 'تجربة', 'كائن'],
        'islamic': ['وضوء', 'صلاة', 'اركان'],
        'english': ['letter', 'alphabet', 'حرف انجليزي']
    }
    
    # فحص الكلمات العامة
    for keyword in svg_needed_keywords['general']:
        if keyword in question_lower:
            return True
    
    # فحص الكلمات الخاصة بالمادة
    subject_keywords = svg_needed_keywords.get(subject_key, [])
    for keyword in subject_keywords:
        if keyword in question_lower:
            return True
    
    # إذا كان الشرح يحتوي على مفاهيم بصرية
    visual_concepts = [
        'شكل', 'لون', 'حجم', 'مكان', 'أجزاء', 'ترتيب', 'خطوات'
    ]
    
    for concept in visual_concepts:
        if concept in explanation.lower():
            return True
    
    return False

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

def process_user_question(question: str, gemini_client, kb_manager, prompt_engine, grade_key: str, subject_key: str):
    """معالجة سؤال المستخدم وإرجاع الإجابة - محدثة"""
   
    # تحديد ما إذا كان يجب البحث في المنهج
    should_search = should_search_in_curriculum(question, subject_key)
    
    # استرجاع السياق من قاعدة المعرفة
    context = ""
    search_status = "not_searched"
   
    if should_search and kb_manager and hasattr(kb_manager, 'db') and kb_manager.db:
        with st.spinner("🔍 البحث في المنهج الدراسي..."):
            context = retrieve_context(kb_manager, question)
            if context:
                search_status = "found"
            else:
                search_status = "not_found"
    else:
        search_status = "not_needed"
   
    # إنشاء البرومبت المخصص
    if prompt_engine:
        specialized_prompt = prompt_engine.get_specialized_prompt(
            question=question,
            app_subject_key=subject_key,
            grade_key=grade_key,
            retrieved_context_str=context if context else None
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
    
    # تحديد ما إذا كان يجب الاحتفاظ بالرسم
    explanation = response.get("text_explanation", "")
    needs_svg = should_generate_svg(question, explanation, subject_key)
    
    if not needs_svg:
        response["svg_code"] = None
   
    return {
        'explanation': explanation,
        'svg_code': response.get("svg_code") if needs_svg else None,
        'quality_scores': response.get("quality_scores", {}),
        'quality_issues': response.get("quality_issues", []),
        'search_status': search_status
    }

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
       
        with col2:
            if st.button("📤 تصدير المحادثة", use_container_width=True):
                export_conversation()
       
        # إحصائيات المحادثة
        if st.session_state.messages:
            st.subheader("📊 إحصائيات المحادثة")
            user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            assistant_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
           
            st.metric("عدد أسئلتك", user_messages)
            st.metric("عدد إجابات المعلم", assistant_messages)
       
        st.divider()
       
        # عرض معلومات النظام
        st.subheader("ℹ️ حالة النظام")
        
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
            
        # عرض حالة قواعد المعرفة إذا كانت متاحة
        if KB_MANAGER_AVAILABLE:
            project_id, location, _ = load_environment_variables_silently()
            if project_id:
                kb_status = check_knowledge_base_status(project_id, location)
                
                st.write(f"📚 ملفات المنهج: {'✅' if kb_status['docs_exist'] else '❌'}")
                st.write(f"🗄️ قواعد البيانات: {'✅' if kb_status['dbs_exist'] else '❌'}")
                
                if kb_status['missing_dbs']:
                    st.warning(f"⚠️ {len(kb_status['missing_dbs'])} قاعدة بيانات مفقودة")
       
        if KB_MANAGER_AVAILABLE and st.button("🔍 فحص متطلبات RAG"):
            with st.spinner("جاري فحص المتطلبات..."):
                try:
                    requirements = check_rag_requirements()
                    for req, available in requirements.items():
                        status = "✅" if available else "❌"
                        st.write(f"{status} {req}")
                except Exception as e:
                    st.error(f"خطأ في فحص المتطلبات: {e}")
       
        return selected_grade, selected_subject

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

def export_conversation():
    """تصدير المحادثة إلى نص"""
    if not st.session_state.messages:
        st.warning("لا توجد محادثة للتصدير")
        return
   
    conversation_text = f"محادثة مع المعلم الذكي السعودي\n"
    conversation_text += f"الصف: {GRADE_SUBJECTS[st.session_state.selected_grade]['name']}\n"
    conversation_text += f"المادة: {GRADE_SUBJECTS[st.session_state.selected_grade]['subjects'][st.session_state.selected_subject]}\n"
    conversation_text += f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    conversation_text += "="*50 + "\n\n"
   
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            conversation_text += f"👤 أنت ({msg['timestamp']}):\n{msg['content']}\n\n"
        elif msg["role"] == "assistant":
            conversation_text += f"🤖 المعلم الذكي ({msg['timestamp']}):\n"
            if 'explanation' in msg:
                conversation_text += f"{msg['explanation']}\n"
            if 'svg_code' in msg and msg['svg_code']:
                conversation_text += "[تم إنتاج رسم توضيحي SVG]\n"
            conversation_text += "\n"
   
    st.download_button(
        label="📄 تحميل المحادثة كنص",
        data=conversation_text,
        file_name=f"محادثة_المعلم_الذكي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

def display_message(message: Dict, is_new: bool = False):
    """عرض رسالة واحدة في المحادثة - محدثة"""
   
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
           
            # عرض حالة البحث المحدثة
            if 'search_status' in message:
                if message['search_status'] == 'found':
                    st.success("✅ تم العثور على معلومات ذات صلة من المنهج الدراسي")
                elif message['search_status'] == 'not_found':
                    st.info("ℹ️ تم البحث في المنهج ولم يتم العثور على معلومات محددة، الاعتماد على المعرفة العامة")
                elif message['search_status'] == 'not_needed':
                    st.info("💬 سؤال عام - لا يحتاج بحث في المنهج")
           
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
            elif 'svg_code' in message and message['svg_code'] is None:
                # إشارة بسيطة أن الرسم لم يكن مطلوباً
                pass  # لا نعرض شيئاً
           
            # عرض معلومات الجودة إذا كانت متاحة
            if 'quality_scores' in message and message['quality_scores']:
                with st.expander("📊 تقييم جودة الإجابة"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("جودة الشرح", f"{message['quality_scores'].get('explanation', 0)}%")
                    with col2:
                        if message.get('svg_code'):
                            st.metric("جودة الرسم", f"{message['quality_scores'].get('svg', 0)}%")
                        else:
                            st.info("لا يحتاج رسماً توضيحياً")
                   
                    if 'quality_issues' in message and message['quality_issues']:
                        st.write("**ملاحظات للتحسين:**")
                        for issue in message['quality_issues']:
                            st.write(f"• {issue}")
           
            # عرض الوقت
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")

def main():
    """الدالة الرئيسية للتطبيق"""
   
    # تهيئة حالة الجلسة
    initialize_session_state()
   
    st.title(APP_TITLE)
    st.markdown(f"**الإصدار:** {VERSION} | **مخصص للمرحلة الابتدائية**")
   
    # تحميل متغيرات البيئة بصمت
    project_id, location, credentials_path = load_environment_variables_silently()
    
    if not project_id:
        st.error("❌ لم يتم تعيين بيانات Google Cloud في Streamlit Secrets")
        st.info("💡 يرجى إضافة المتغيرات المطلوبة في إعدادات التطبيق")
        st.stop()
    
    # فحص وبناء قواعد المعرفة إذا لزم الأمر
    if not st.session_state.knowledge_bases_built:
        st.info("🔄 جاري فحص قواعد المعرفة...")
        
        kb_status = check_knowledge_base_status(project_id, location)
        
        if not kb_status["docs_exist"]:
            st.warning("⚠️ لا توجد ملفات منهج دراسي. سيعمل المعلم الذكي بالمعرفة العامة فقط.")
            st.session_state.knowledge_bases_built = True
        elif kb_status["missing_dbs"]:
            st.warning(f"⚠️ {len(kb_status['missing_dbs'])} قاعدة بيانات مفقودة. جاري البناء التلقائي...")
            
            with st.spinner("🏗️ جاري بناء قواعد المعرفة... قد يستغرق هذا بضع دقائق في المرة الأولى."):
                build_result = build_knowledge_bases_if_needed(project_id, location)
                
                if build_result["success"]:
                    if "built_databases" in build_result:
                        st.success(f"✅ تم بناء {len(build_result['built_databases'])} قاعدة معرفة بنجاح!")
                    if "failed_databases" in build_result and build_result["failed_databases"]:
                        st.warning(f"⚠️ فشل بناء {len(build_result['failed_databases'])} قاعدة معرفة")
                else:
                    st.error(f"❌ {build_result['message']}")
                    if "suggestion" in build_result:
                        st.info(f"💡 {build_result['suggestion']}")
            
            st.session_state.knowledge_bases_built = True
        else:
            st.success("✅ قواعد المعرفة جاهزة!")
            st.session_state.knowledge_bases_built = True
   
    # عرض الشريط الجانبي
    selected_grade, selected_subject = display_sidebar()
   
    # تهيئة المكونات
    with st.spinner("🔄 جاري تهيئة المعلم الذكي..."):
        gemini_client = initialize_gemini_client(project_id, location)
        if not gemini_client and GEMINI_CLIENT_AVAILABLE:
            st.error("❌ فشل تهيئة عميل Gemini")
            st.stop()
       
        kb_manager = initialize_knowledge_base(project_id, location, selected_grade, selected_subject)
        prompt_engine = initialize_prompt_engine()
   
    # عرض رسالة الترحيب إذا لم تبدأ المحادثة
    if not st.session_state.conversation_started:
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
            st.write(f"أهلاً وسهلاً! أنا معلمك الذكي للصف {GRADE_SUBJECTS[selected_grade]['name']} في مادة {GRADE_SUBJECTS[selected_grade]['subjects'][selected_subject]}.")
            if GEMINI_CLIENT_AVAILABLE and gemini_client:
                st.write("اسألني أي سؤال وسأجيبك بشرح مبسط! 😊")
                st.write("💡 **نصيحة:** أطرح أسئلة محددة عن المادة للحصول على أفضل النتائج")
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
                        prompt, gemini_client, kb_manager, prompt_engine,
                        selected_grade, selected_subject
                    )
                   
                    # عرض حالة البحث
                    if response_data['search_status'] == 'found':
                        st.success("✅ تم العثور على معلومات ذات صلة من المنهج الدراسي")
                    elif response_data['search_status'] == 'not_found':
                        st.info("ℹ️ تم البحث في المنهج ولم يتم العثور على معلومات محددة، الاعتماد على المعرفة العامة")
                    elif response_data['search_status'] == 'not_needed':
                        st.info("💬 سؤال عام - لا يحتاج بحث في المنهج")
                   
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
                   
                    # عرض معلومات الجودة
                    if response_data['quality_scores']:
                        with st.expander("📊 تقييم جودة الإجابة"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("جودة الشرح", f"{response_data['quality_scores'].get('explanation', 0)}%")
                            with col2:
                                if response_data.get('svg_code'):
                                    st.metric("جودة الرسم", f"{response_data['quality_scores'].get('svg', 0)}%")
                                else:
                                    st.info("لا يحتاج رسماً توضيحياً")
                   
                    # إضافة إجابة المساعد للمحادثة
                    add_message("assistant", "", **response_data)
                   
                except Exception as e:
                    error_msg = f"❌ حدث خطأ: {e}"
                    st.error(error_msg)
                    add_message("assistant", error_msg)
   
    # قسم المساعدة
    with st.expander("❓ كيفية استخدام المعلم الذكي المحدث"):
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
       
        **للتربية الإسلامية:**
        - "علمني كيفية الوضوء"
        - "ما هي أركان الإسلام؟"
       
        **للغة الإنجليزية:**
        - "Teach me the letter A"
        - "What colors do you know?"
       
        ### 🆕 المميزات الجديدة:
        - **بحث ذكي**: يبحث فقط في المادة المحددة
        - **رسم ذكي**: ينتج رسماً فقط عند الحاجة
        - **ردود مناسبة**: يتعامل مع التحيات والأسئلة العامة بذكاء
        
        ### 💡 ميزات المحادثة المستمرة:
        - **يتذكر**: جميع أسئلتك وإجاباتي السابقة
        - **يتطور**: يمكنك البناء على الأسئلة السابقة
        - **يحفظ**: يمكنك تصدير المحادثة كاملة
        - **ينظف**: يمكنك بدء محادثة جديدة في أي وقت
        """)
   
    # معلومات إضافية في التذييل
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💡 المعلم الذكي السعودي المحدث - مدعوم بتقنية Gemini AI و RAG<br>
    🎯 مخصص للمرحلة الابتدائية - منهج المملكة العربية السعودية<br>
    🔐 آمن ومحمي - جميع البيانات الحساسة في Streamlit Secrets<br>
    💬 يحفظ تاريخ محادثتك ويتذكر الأسئلة السابقة<br>
    🆕 بحث ذكي منفصل لكل مادة + رسم ذكي حسب الحاجة
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
