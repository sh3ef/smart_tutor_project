# app.py - التطبيق الرئيسي للمعلم الذكي (محسن مع إصلاحات المشاكل)

import os
import sys
import streamlit as st
import traceback
import json
import tempfile
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

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
APP_TITLE = "🤖 المعلم الذكي السعودي المحسن"
VERSION = "3.1 - Smart Edition"

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

# === دوال التصنيف الذكي للأسئلة ===

def classify_question_type(question: str) -> Dict[str, any]:
    """تصنيف نوع السؤال لتحديد كيفية التعامل معه"""
    question_lower = question.lower().strip()
    
    # أنماط التحيات والأسئلة الاجتماعية
    greetings_patterns = [
        r'السلام عليكم', r'السلام عليك', r'مرحبا', r'مرحباً', r'أهلا', r'أهلاً',
        r'صباح الخير', r'مساء الخير', r'كيف حالك', r'كيف الحال',
        r'hello', r'hi', r'good morning', r'good evening', r'how are you'
    ]
    
    # أنماط الأسئلة التي تحتاج بحث في المنهج
    curriculum_patterns = [
        r'علمني', r'اشرح.*لي', r'ما هو', r'ما هي', r'كيف.*أ(جمع|طرح|ضرب|قسم)',
        r'ما.*معنى', r'أريد.*أتعلم', r'حرف.*ال[أ-ي]', r'رقم.*\d+', r'عملية.*',
        r'درس.*', r'وحدة.*', r'teach me', r'explain.*', r'what is', r'how to', r'show me'
    ]
    
    # أنماط الأسئلة التي تحتاج رسم
    drawing_patterns = [
        r'ارسم.*لي', r'رسم.*', r'أريد.*رسم', r'وضح.*بالرسم', r'بالرسم',
        r'اشرح.*بالصور', r'مع.*رسم', r'draw.*', r'show.*drawing', r'with.*picture'
    ]
    
    # أنماط الأسئلة الرياضية
    math_patterns = [
        r'\d+\s*[+\-×÷]\s*\d+', r'جمع.*\d+', r'طرح.*\d+', r'ضرب.*\d+',
        r'قسمة.*\d+', r'معادلة', r'حساب', r'عملية.*حسابية'
    ]
    
    is_greeting = any(re.search(pattern, question_lower) for pattern in greetings_patterns)
    needs_curriculum_search = any(re.search(pattern, question_lower) for pattern in curriculum_patterns)
    needs_drawing = any(re.search(pattern, question_lower) for pattern in drawing_patterns)
    is_math_question = any(re.search(pattern, question_lower) for pattern in math_patterns)
    
    # تحديد ما إذا كان السؤال تعليمي
    is_educational = needs_curriculum_search or is_math_question or len(question.split()) > 3
    
    # تحديد ما إذا كان الرسم مطلوب صراحة أو ضروري للفهم
    drawing_required = needs_drawing or (is_educational and (is_math_question or 
                       any(word in question_lower for word in ['شكل', 'صورة', 'مثال', 'توضيح'])))
    
    return {
        'is_greeting': is_greeting,
        'is_educational': is_educational,
        'needs_curriculum_search': is_educational and not is_greeting,
        'needs_drawing': drawing_required and not is_greeting,
        'is_math_question': is_math_question,
        'question_complexity': len(question.split())
    }

def get_greeting_response(question: str, grade_key: str, subject_key: str) -> Dict[str, any]:
    """إنشاء رد مناسب للتحيات والأسئلة الاجتماعية"""
    question_lower = question.lower().strip()
    
    grade_name = GRADE_SUBJECTS[grade_key]['name']
    subject_name = GRADE_SUBJECTS[grade_key]['subjects'][subject_key]
    
    # ردود مختلفة للتحيات المختلفة
    if 'السلام عليكم' in question_lower or 'السلام عليك' in question_lower:
        explanation = f"وعليكم السلام ورحمة الله وبركاته يا بطل! 🌟 أهلاً وسهلاً بك! أنا معلمك الذكي، مستعد لأساعدك في تعلم {subject_name} للصف {grade_name}. ما الذي تريد أن نتعلمه اليوم؟ 📚✨"
    elif any(word in question_lower for word in ['مرحبا', 'مرحباً', 'أهلا', 'أهلاً', 'hello', 'hi']):
        explanation = f"أهلاً وسهلاً يا صغيري! 🎉 مرحباً بك في درس {subject_name}! أنا هنا لأجعل التعلم ممتعاً وسهلاً لك. اسألني عن أي شيء تريد تعلمه! 🤓💫"
    elif any(word in question_lower for word in ['صباح الخير', 'good morning']):
        explanation = f"صباح الخير يا نجم! ☀️ أتمنى لك يوماً رائعاً مليئاً بالتعلم والمرح! مستعد لنبدأ درس {subject_name} اليوم؟ 🌅📖"
    elif any(word in question_lower for word in ['مساء الخير', 'good evening']):
        explanation = f"مساء الخير يا بطل! 🌙 أرجو أن يكون يومك كان جميلاً! هيا نختتم اليوم بتعلم شيء جديد في {subject_name}! ⭐📚"
    elif any(word in question_lower for word in ['كيف حالك', 'كيف الحال', 'how are you']):
        explanation = f"أنا بخير والحمد لله، شكراً لسؤالك! 😊 أشعر بالحماس لأنني سأساعدك في تعلم {subject_name}! وأنت، كيف حالك؟ مستعد للتعلم؟ 🎈📝"
    else:
        explanation = f"أهلاً بك يا صديقي! 👋 أنا معلمك الذكي ومستعد لمساعدتك في {subject_name} للصف {grade_name}. اسألني عن أي شيء تريد تعلمه! 🚀📚"
    
    return {
        'explanation': explanation,
        'svg_code': None,  # لا رسم للتحيات
        'quality_scores': {'explanation': 100, 'svg': 100},
        'quality_issues': [],
        'search_status': 'greeting'
    }

def should_search_curriculum(question: str, question_type: Dict[str, any]) -> bool:
    """تحديد ما إذا كان يجب البحث في المنهج أم لا"""
    # لا تبحث في المنهج للتحيات
    if question_type['is_greeting']:
        return False
    
    # لا تبحث للأسئلة القصيرة جداً (كلمة أو كلمتين)
    if question_type['question_complexity'] <= 2 and not question_type['is_educational']:
        return False
    
    # ابحث فقط للأسئلة التعليمية
    return question_type['needs_curriculum_search']

def create_smart_prompt(question: str, question_type: Dict[str, any], app_subject_key: str, 
                       grade_key: str, retrieved_context_str: Optional[str], prompt_engine) -> str:
    """إنشاء برومبت ذكي يراعي نوع السؤال"""
    # الحصول على البرومبت الأساسي
    base_prompt = prompt_engine.get_specialized_prompt(
        question=question,
        app_subject_key=app_subject_key,
        grade_key=grade_key,
        retrieved_context_str=retrieved_context_str
    )
    
    # إضافة تعليمات خاصة بنوع السؤال
    if not question_type['needs_drawing']:
        drawing_instruction = """
**تعليمة خاصة للرسم:**
هذا السؤال لا يحتاج إلى رسم توضيحي. يجب أن يكون `svg_code` هو `null` أو غير موجود في الاستجابة.
ركز على تقديم شرح نصي واضح ومفيد فقط.
"""
        base_prompt += "\n" + drawing_instruction
    
    if question_type['is_greeting']:
        greeting_instruction = """
**تعليمة خاصة للتحيات:**
هذا سؤال تحية أو اجتماعي. لا تبحث في المنهج ولا ترسم أي شيء.
قدم رداً ودوداً ومناسباً لطفل في المرحلة الابتدائية.
"""
        base_prompt += "\n" + greeting_instruction
    
    return base_prompt

# === دوال المعالجة المحسنة ===

def load_environment_variables_silently():
    """تحميل متغيرات البيئة من Streamlit Secrets بصمت"""
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

def check_knowledge_base_detailed_status(project_id: str, location: str) -> Dict[str, Any]:
    """فحص مفصل لحالة قواعد المعرفة مع تشخيص دقيق للمشاكل"""
    if not KB_MANAGER_AVAILABLE:
        return {
            "available": False,
            "reason": "KnowledgeBaseManager غير متاح",
            "details": "مكتبات RAG غير مثبتة بشكل صحيح"
        }
    
    knowledge_docs_path = Path("knowledge_base_docs")
    docs_exist = knowledge_docs_path.exists()
    
    chroma_dbs_path = Path("chroma_dbs")
    dbs_exist = chroma_dbs_path.exists()
    
    detailed_status = {
        "available": True,
        "docs_exist": docs_exist,
        "dbs_exist": dbs_exist,
        "grade_details": {},
        "total_expected": 0,
        "total_found_docs": 0,
        "total_found_dbs": 0,
        "missing_docs": [],
        "missing_dbs": [],
        "empty_docs": [],
        "build_errors": []
    }
    
    # فحص تفصيلي لكل صف ومادة
    for grade_key, grade_info in GRADE_SUBJECTS.items():
        grade_details = {"name": grade_info['name'], "subjects": {}}
        
        for subject_key, subject_name in grade_info['subjects'].items():
            subject_folder = SUBJECT_FOLDERS.get(subject_key, subject_key)
            detailed_status["total_expected"] += 1
            
            # فحص مجلد المستندات
            docs_path = knowledge_docs_path / grade_key / subject_folder
            docs_status = {
                "path": str(docs_path),
                "exists": docs_path.exists(),
                "has_files": False,
                "file_count": 0,
                "file_types": []
            }
            
            if docs_path.exists():
                try:
                    files = list(docs_path.glob("*"))
                    docs_status["file_count"] = len([f for f in files if f.is_file()])
                    docs_status["has_files"] = docs_status["file_count"] > 0
                    docs_status["file_types"] = list(set([f.suffix for f in files if f.is_file()]))
                    
                    if docs_status["has_files"]:
                        detailed_status["total_found_docs"] += 1
                    else:
                        detailed_status["empty_docs"].append(f"{grade_key}/{subject_folder}")
                except Exception as e:
                    docs_status["error"] = str(e)
                    detailed_status["build_errors"].append(f"خطأ في قراءة {docs_path}: {e}")
            else:
                detailed_status["missing_docs"].append(f"{grade_key}/{subject_folder}")
            
            # فحص قاعدة البيانات
            collection_name = f"{grade_key}_{subject_folder.replace(' ', '_').lower()}_coll"
            db_path = chroma_dbs_path / collection_name
            db_status = {
                "collection_name": collection_name,
                "path": str(db_path),
                "exists": db_path.exists(),
                "has_data": False
            }
            
            if db_path.exists():
                try:
                    data_files = list(db_path.glob("**/*"))
                    db_status["has_data"] = len([f for f in data_files if f.is_file()]) > 0
                    
                    if db_status["has_data"]:
                        detailed_status["total_found_dbs"] += 1
                    else:
                        detailed_status["missing_dbs"].append(collection_name)
                except Exception as e:
                    db_status["error"] = str(e)
                    detailed_status["build_errors"].append(f"خطأ في قراءة {db_path}: {e}")
            else:
                detailed_status["missing_dbs"].append(collection_name)
            
            grade_details["subjects"][subject_key] = {
                "name": subject_name,
                "folder": subject_folder,
                "docs": docs_status,
                "db": db_status
            }
        
        detailed_status["grade_details"][grade_key] = grade_details
    
    return detailed_status

@st.cache_data
def build_knowledge_bases_with_error_handling(project_id: str, location: str, force_rebuild: bool = False) -> Dict[str, Any]:
    """بناء قواعد المعرفة مع معالجة تفصيلية للأخطاء"""
    status = check_knowledge_base_detailed_status(project_id, location)
    
    if not status["available"]:
        return {"success": False, "message": "مدير قواعد المعرفة غير متاح", "details": status.get("details", "")}
    
    if not status["docs_exist"] or status["total_found_docs"] == 0:
        return {
            "success": False,
            "message": "لا توجد ملفات منهج دراسي لبناء قواعد المعرفة منها",
            "suggestion": "تأكد من رفع مجلد knowledge_base_docs مع ملفات المنهج",
            "missing_docs": status["missing_docs"],
            "empty_docs": status["empty_docs"]
        }
    
    if not force_rebuild and status["total_found_dbs"] > 0 and len(status["missing_dbs"]) == 0:
        return {
            "success": True, 
            "message": "قواعد المعرفة موجودة ولا تحتاج إعادة بناء",
            "found_dbs": status["total_found_dbs"]
        }
    
    results = {
        "success": True,
        "built_databases": [],
        "failed_databases": [],
        "skipped_databases": [],
        "detailed_errors": []
    }
    
    # إنشاء قائمة المواد التي بها ملفات
    subjects_to_build = [
        (grade_key, subject_key, subject_folder)
        for grade_key, grade_info in GRADE_SUBJECTS.items()
        for subject_key, subject_folder in [(sk, SUBJECT_FOLDERS.get(sk, sk)) for sk in grade_info['subjects'].keys()]
        if status["grade_details"][grade_key]["subjects"][subject_key]["docs"]["has_files"]
    ]
    
    total_subjects = len(subjects_to_build)
    
    if total_subjects == 0:
        return {
            "success": False,
            "message": "لا توجد مجلدات تحتوي على ملفات صالحة للبناء",
            "empty_docs": status["empty_docs"]
        }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (grade_key, subject_key, subject_folder) in enumerate(subjects_to_build):
        current_progress = (i + 1) / total_subjects
        
        grade_name = GRADE_SUBJECTS[grade_key]['name']
        subject_name = GRADE_SUBJECTS[grade_key]['subjects'][subject_key]
        collection_name = f"{grade_key}_{subject_folder.replace(' ', '_').lower()}_coll"
        
        status_text.text(f"جاري بناء قاعدة المعرفة ({i+1}/{total_subjects}): {grade_name} - {subject_name}")
        progress_bar.progress(current_progress)
        
        db_path = Path("chroma_dbs") / collection_name
        if db_path.exists() and not force_rebuild:
            try:
                data_files = list(db_path.glob("**/*"))
                if len([f for f in data_files if f.is_file()]) > 0:
                    results["skipped_databases"].append({
                        "name": collection_name,
                        "reason": "موجودة مسبقاً وتحتوي على بيانات"
                    })
                    continue
            except Exception as e:
                results["detailed_errors"].append(f"خطأ في فحص {collection_name}: {e}")
        
        try:
            kb_manager = None
            retry_count = 3
            
            for attempt in range(retry_count):
                try:
                    kb_manager = KnowledgeBaseManager(
                        grade_folder_name=grade_key,
                        subject_folder_name=subject_folder,
                        project_id=project_id,
                        location=location,
                        force_recreate=force_rebuild
                    )
                    
                    if kb_manager.embedding_function and kb_manager.db:
                        break
                    else:
                        if attempt < retry_count - 1:
                            time.sleep(2)
                        else:
                            kb_manager = None
                except Exception as e:
                    if attempt < retry_count - 1:
                        time.sleep(2)
                    else:
                        results["detailed_errors"].append(f"فشل إنشاء مدير {collection_name}: {e}")
                        kb_manager = None
            
            if not kb_manager:
                results["failed_databases"].append({
                    "name": collection_name,
                    "reason": "فشل تهيئة مدير قاعدة المعرفة"
                })
                continue
            
            build_success = False
            for attempt in range(2):
                try:
                    if kb_manager.build_knowledge_base():
                        build_success = True
                        break
                    else:
                        if attempt == 0:
                            time.sleep(1)
                except Exception as e:
                    results["detailed_errors"].append(f"خطأ في بناء {collection_name} (المحاولة {attempt + 1}): {e}")
                    if attempt == 0:
                        time.sleep(1)
            
            if build_success:
                results["built_databases"].append(collection_name)
            else:
                results["failed_databases"].append({
                    "name": collection_name,
                    "reason": "فشل عملية البناء"
                })
                    
        except Exception as e:
            error_msg = f"خطأ عام في بناء {collection_name}: {str(e)}"
            results["failed_databases"].append({
                "name": collection_name,
                "reason": error_msg
            })
            results["detailed_errors"].append(error_msg)
    
    progress_bar.progress(1.0)
    status_text.text("اكتمل بناء قواعد المعرفة!")
    
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

def process_user_question_improved(question: str, gemini_client, kb_manager, prompt_engine, grade_key: str, subject_key: str):
    """نسخة محسنة من معالج الأسئلة مع منطق ذكي للبحث والرسم"""
    # تصنيف نوع السؤال
    question_type = classify_question_type(question)
    
    # التعامل مع التحيات
    if question_type['is_greeting']:
        return get_greeting_response(question, grade_key, subject_key)
    
    # البحث في المنهج إذا لزم الأمر
    context = ""
    search_status = "not_searched"
    
    if should_search_curriculum(question, question_type):
        if kb_manager and hasattr(kb_manager, 'db') and kb_manager.db:
            try:
                with st.spinner("🔍 البحث في المنهج الدراسي..."):
                    context = retrieve_context(kb_manager, question)
                    if context:
                        search_status = "found"
                    else:
                        search_status = "not_found"
            except Exception as e:
                print(f"خطأ في البحث: {e}")
                search_status = "error"
        else:
            search_status = "no_kb"
    
    # إنشاء البرومبت مع تحديد ما إذا كان الرسم مطلوب
    if prompt_engine:
        specialized_prompt = create_smart_prompt(
            question=question,
            question_type=question_type,
            app_subject_key=subject_key,
            grade_key=grade_key,
            retrieved_context_str=context if context else None,
            prompt_engine=prompt_engine
        )
    else:
        specialized_prompt = f"أنت معلم للصف {grade_key} في مادة {subject_key}. اشرح للطفل: {question}"
    
    # إرسال الطلب لـ Gemini
    if gemini_client:
        response = gemini_client.query_for_explanation_and_svg(specialized_prompt)
    else:
        response = {
            "text_explanation": "عذرًا، المعلم الذكي غير جاهز حالياً. يرجى المحاولة لاحقاً.",
            "svg_code": None,
            "quality_scores": {},
            "quality_issues": ["المعلم الذكي غير متاح"]
        }
    
    # إزالة الرسم إذا لم يكن مطلوباً
    if not question_type['needs_drawing']:
        response['svg_code'] = None
    
    return {
        'explanation': response.get("text_explanation", "عذرًا، لم أتمكن من إنتاج شرح مناسب."),
        'svg_code': response.get("svg_code"),
        'quality_scores': response.get("quality_scores", {}),
        'quality_issues': response.get("quality_issues", []),
        'search_status': search_status
    }

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

def display_knowledge_base_diagnostics():
    """عرض تشخيص مفصل لحالة قواعد المعرفة"""
    project_id, location, _ = load_environment_variables_silently()
    if not project_id:
        st.error("❌ لا توجد إعدادات Google Cloud")
        return
    
    with st.expander("🔍 تشخيص مفصل لقواعد المعرفة"):
        status = check_knowledge_base_detailed_status(project_id, location)
        
        # إحصائيات عامة
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("المتوقع", status["total_expected"])
        with col2:
            st.metric("ملفات موجودة", status["total_found_docs"])
        with col3:
            st.metric("قواعد بيانات", status["total_found_dbs"])
        with col4:
            success_rate = round((status["total_found_dbs"] / status["total_expected"]) * 100) if status["total_expected"] > 0 else 0
            st.metric("معدل النجاح", f"{success_rate}%")
        
        # تفاصيل المشاكل
        if status["missing_docs"]:
            st.error(f"❌ مجلدات مفقودة ({len(status['missing_docs'])}): {', '.join(status['missing_docs'][:5])}{'...' if len(status['missing_docs']) > 5 else ''}")
        
        if status["empty_docs"]:
            st.warning(f"⚠️ مجلدات فارغة ({len(status['empty_docs'])}): {', '.join(status['empty_docs'][:5])}{'...' if len(status['empty_docs']) > 5 else ''}")
        
        if status["missing_dbs"]:
            st.info(f"ℹ️ قواعد بيانات مفقودة ({len(status['missing_dbs'])}): {', '.join(status['missing_dbs'][:5])}{'...' if len(status['missing_dbs']) > 5 else ''}")
        
        if status["build_errors"]:
            st.error("❌ أخطاء البناء:")
            for error in status["build_errors"][:3]:
                st.text(f"  • {error}")

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
        
        status_items = [
            ("Gemini Client", GEMINI_CLIENT_AVAILABLE),
            ("Prompt Engine", PROMPT_ENGINE_AVAILABLE),
            ("Knowledge Base", KB_MANAGER_AVAILABLE),
            ("Code Executor", CODE_EXECUTOR_AVAILABLE)
        ]
        
        for name, available in status_items:
            status = "✅" if available else "❌"
            st.write(f"{status} {name}")
            
        # عرض تشخيص قواعد المعرفة
        if st.button("🔍 تشخيص مفصل"):
            display_knowledge_base_diagnostics()
       
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
   
    conversation_text = f"محادثة مع المعلم الذكي السعودي المحسن\n"
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
    """عرض رسالة واحدة في المحادثة"""
   
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(f"**أنت:** {message['content']}")
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")
   
    elif message["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
           
            # عرض حالة البحث إذا كانت موجودة
            if 'search_status' in message:
                if message['search_status'] == 'found':
                    st.success("✅ تم العثور على معلومات ذات صلة من المنهج")
                elif message['search_status'] == 'not_found':
                    st.info("ℹ️ لم يتم العثور على معلومات في المنهج، سيتم الاعتماد على المعرفة العامة")
                elif message['search_status'] == 'greeting':
                    st.info("👋 تحية ودودة")
                elif message['search_status'] == 'not_searched':
                    st.info("ℹ️ لم يتم البحث في المنهج - السؤال لا يتطلب ذلك")
           
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
                   
                    st.download_button(
                        label="⬇️ تحميل SVG",
                        data=message['svg_code'],
                        file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                        mime="image/svg+xml",
                        key=f"download_svg_{message.get('id', 'unknown')}"
                    )
           
            # عرض معلومات الجودة إذا كانت متاحة
            if 'quality_scores' in message and message['quality_scores']:
                with st.expander("📊 تقييم جودة الإجابة"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("جودة الشرح", f"{message['quality_scores'].get('explanation', 0)}%")
                    with col2:
                        st.metric("جودة الرسم", f"{message['quality_scores'].get('svg', 0)}%")
                   
                    if 'quality_issues' in message and message['quality_issues']:
                        st.write("**ملاحظات للتحسين:**")
                        for issue in message['quality_issues']:
                            st.write(f"• {issue}")
           
            # عرض الوقت
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")

def main():
    """الدالة الرئيسية المحسنة للتطبيق"""
   
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
        
        kb_status = check_knowledge_base_detailed_status(project_id, location)
        
        if not kb_status["docs_exist"] or kb_status["total_found_docs"] == 0:
            st.warning("⚠️ لا توجد ملفات منهج دراسي. سيعمل المعلم الذكي بالمعرفة العامة فقط.")
            st.info("💡 لإضافة المنهج، ارفع مجلد 'knowledge_base_docs' مع ملفات المنهج")
            st.session_state.knowledge_bases_built = True
        elif len(kb_status["missing_dbs"]) > 0:
            missing_count = len(kb_status["missing_dbs"])
            total_count = kb_status["total_expected"]
            
            st.warning(f"⚠️ {missing_count} من أصل {total_count} قاعدة بيانات مفقودة. جاري البناء التلقائي...")
            
            if kb_status["empty_docs"]:
                st.info(f"ℹ️ {len(kb_status['empty_docs'])} مجلد فارغ سيتم تجاهله")
            
            with st.spinner("🏗️ جاري بناء قواعد المعرفة... قد يستغرق هذا بضع دقائق في المرة الأولى."):
                build_result = build_knowledge_bases_with_error_handling(project_id, location)
                
                if build_result["success"]:
                    built_count = len(build_result["built_databases"])
                    failed_count = len(build_result["failed_databases"])
                    skipped_count = len(build_result["skipped_databases"])
                    
                    if built_count > 0:
                        st.success(f"✅ تم بناء {built_count} قاعدة معرفة بنجاح!")
                    
                    if skipped_count > 0:
                        st.info(f"ℹ️ تم تجاهل {skipped_count} قاعدة موجودة مسبقاً")
                    
                    if failed_count > 0:
                        st.warning(f"⚠️ فشل بناء {failed_count} قاعدة معرفة")
                        
                        with st.expander("📋 تفاصيل الأخطاء"):
                            for error in build_result["detailed_errors"][:10]:
                                st.text(f"• {error}")
                            
                            st.info("💡 نصائح لحل المشاكل:")
                            st.write("- تأكد من وجود ملفات المنهج في المجلدات الصحيحة")
                            st.write("- تحقق من صلاحيات Google Cloud")
                            st.write("- راجع اتصال الإنترنت")
                else:
                    st.error(f"❌ {build_result['message']}")
                    if "suggestion" in build_result:
                        st.info(f"💡 {build_result['suggestion']}")
            
            st.session_state.knowledge_bases_built = True
        else:
            st.success(f"✅ قواعد المعرفة جاهزة! ({kb_status['total_found_dbs']}/{kb_status['total_expected']})")
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
                st.write("اسألني أي سؤال وسأجيبك بشرح مبسط ورسم توضيحي عند الحاجة! 😊")
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
       
        # معالجة السؤال وإنتاج الإجابة باستخدام المعالج المحسن
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
           
            with st.spinner("🤖 المعلم الذكي يفكر في الإجابة..."):
                try:
                    # استخدام المعالج المحسن
                    response_data = process_user_question_improved(
                        prompt, gemini_client, kb_manager, prompt_engine,
                        selected_grade, selected_subject
                    )
                   
                    # عرض حالة البحث
                    if response_data['search_status'] == 'found':
                        st.success("✅ تم العثور على معلومات ذات صلة من المنهج")
                    elif response_data['search_status'] == 'not_found':
                        st.info("ℹ️ لم يتم العثور على معلومات في المنهج، سيتم الاعتماد على المعرفة العامة")
                    elif response_data['search_status'] == 'greeting':
                        st.info("👋 تحية ودودة")
                    elif response_data['search_status'] == 'not_searched':
                        st.info("ℹ️ لم يتم البحث في المنهج - السؤال لا يتطلب ذلك")
                   
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
                                st.metric("جودة الرسم", f"{response_data['quality_scores'].get('svg', 0)}%")
                   
                    # إضافة إجابة المساعد للمحادثة
                    add_message("assistant", "", **response_data)
                   
                except Exception as e:
                    error_msg = f"❌ حدث خطأ: {e}"
                    st.error(error_msg)
                    add_message("assistant", error_msg)
   
    # قسم المساعدة المحدث
    with st.expander("❓ كيفية استخدام المعلم الذكي المحسن"):
        st.markdown("""
        ### 🎯 نصائح للحصول على أفضل إجابة:
       
        **للتحيات والمحادثة:**
        - "السلام عليكم" ← رد مناسب بدون بحث أو رسم
        - "مرحباً" ← ترحيب ودود
        - "كيف حالك؟" ← محادثة اجتماعية
       
        **للأسئلة التعليمية:**
        - "علمني حرف الألف مع أمثلة" ← بحث في المنهج + رسم
        - "اشرح لي جمع 2+3" ← رسم توضيحي للعملية
        - "ما هي أجزاء النبات؟" ← رسم علمي مع التسميات
       
        **للأسئلة البسيطة:**
        - "ما معنى كلمة سعادة؟" ← شرح بدون رسم
        - "متى نقول صباح الخير؟" ← إجابة مباشرة
       
        ### 🧠 الذكاء الاصطناعي للمعلم:
        - **يميز** بين التحيات والأسئلة التعليمية
        - **يبحث** فقط في المنهج المختار عند الحاجة
        - **يرسم** فقط عندما يساعد الرسم في الفهم
        - **يتذكر** محادثتك ويبني عليها
        """)
   
    # معلومات إضافية في التذييل
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💡 المعلم الذكي السعودي المحسن - مدعوم بتقنية Gemini AI و RAG الذكي<br>
    🎯 بحث ذكي في المنهج المختار فقط • رسم عند الحاجة فقط • تفاعل طبيعي مع التحيات<br>
    🔐 آمن ومحمي - جميع البيانات الحساسة في Streamlit Secrets<br>
    💬 يحفظ تاريخ محادثتك ويتذكر الأسئلة السابقة
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
