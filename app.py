# app.py - التطبيق الرئيسي للمعلم الذكي (مع ميزة Chat History Memory والنظام الذكي للرسم)

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

# إصلاح مشكلة protobuf
import sys
try:
    import google.protobuf
    print(f"Protobuf version: {google.protobuf.__version__}")
except ImportError:
    print("Protobuf not installed")

# إصلاح distutils
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
        except ImportError:
            print("⚠️ pysqlite3 not available, continuing with system SQLite")
    else:
        print("✅ SQLite version is sufficient")
        
except Exception as e:
    print(f"Warning: SQLite fix failed: {e}")

# تحميل الوحدات المخصصة بأمان (بصمت)
try:
    from tutor_ai.gemini_client import GeminiClientVertexAI
    GEMINI_CLIENT_AVAILABLE = True
except Exception as e:
    GEMINI_CLIENT_AVAILABLE = False

try:
    from tutor_ai.prompt_engineering import UnifiedPromptEngine
    PROMPT_ENGINE_AVAILABLE = True
except Exception as e:
    PROMPT_ENGINE_AVAILABLE = False

try:
    from tutor_ai.knowledge_base_manager import KnowledgeBaseManager, check_rag_requirements
    KB_MANAGER_AVAILABLE = True
except Exception as e:
    KB_MANAGER_AVAILABLE = False
    def check_rag_requirements():
        return {"Status": False}

try:
    from tutor_ai.code_executor import save_svg_content_to_file
    CODE_EXECUTOR_AVAILABLE = True
except Exception as e:
    CODE_EXECUTOR_AVAILABLE = False
    def save_svg_content_to_file(svg_content: str, path: str) -> bool:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            return True
        except:
            return False

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="المعلم الذكي",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# متغيرات التطبيق العامة
APP_TITLE = "🤖 المعلم الذكي"

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

# === دوال تحليل السياق والذاكرة ===

class ChatHistoryAnalyzer:
    """محلل تاريخ المحادثة لفهم السياق والمراجع"""
    
    def __init__(self):
        # الضمائر والمراجع العربية
        self.reference_patterns = [
            r'\bه\b', r'\bها\b', r'\bهذا\b', r'\bهذه\b', r'\bذلك\b', r'\bتلك\b',
            r'\bالموضوع\b', r'\bالدرس\b', r'\bالشرح\b', r'\bالمثال\b',
            r'\bنفس الشيء\b', r'\bنفس الموضوع\b', r'\bما قلته\b', r'\bما شرحته\b',
            r'\bالسؤال السابق\b', r'\bما سألت عنه\b', r'\bاللي قلته\b'
        ]
        
        # كلمات طلب التوضيح أو التفصيل
        self.clarification_patterns = [
            r'اشرح.*بالرسم', r'ارسم.*لي', r'وضح.*بالرسم', r'بالصور', r'بالرسم',
            r'مع رسم', r'رسم توضيحي', r'صورة', r'مثال بالرسم',
            r'وضح أكثر', r'فصل أكثر', r'بالتفصيل', r'أريد تفاصيل',
            r'explain.*with.*drawing', r'draw.*for.*me', r'show.*picture'
        ]
        
        # كلمات الرفض أو التصحيح
        self.correction_patterns = [
            r'\bلا\b', r'\bليس\b', r'\bغير صحيح\b', r'\bخطأ\b',
            r'لا أريد', r'لا أفهم', r'غير واضح', r'صعب',
            r'\bno\b', r'\bnot\b', r'\bwrong\b'
        ]

    def has_references(self, question: str) -> bool:
        """فحص ما إذا كان السؤال يحتوي على مراجع لمحادثات سابقة"""
        question_lower = question.lower().strip()
        return any(re.search(pattern, question_lower) for pattern in self.reference_patterns)
    
    def is_clarification_request(self, question: str) -> bool:
        """فحص ما إذا كان السؤال طلب توضيح أو تفصيل"""
        question_lower = question.lower().strip()
        return any(re.search(pattern, question_lower) for pattern in self.clarification_patterns)
    
    def is_correction_request(self, question: str) -> bool:
        """فحص ما إذا كان السؤال تصحيح أو رفض"""
        question_lower = question.lower().strip()
        return any(re.search(pattern, question_lower) for pattern in self.correction_patterns)
    
    def extract_last_topic(self, messages: List[Dict]) -> Optional[str]:
        """استخراج آخر موضوع تم مناقشته"""
        # البحث عن آخر سؤال من المستخدم وإجابة المعلم
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
        
        if user_messages:
            last_user_question = user_messages[-1]["content"]
            # استخراج الموضوع الرئيسي من السؤال
            return self._extract_main_topic(last_user_question)
        
        return None
    
    def _extract_main_topic(self, question: str) -> str:
        """استخراج الموضوع الرئيسي من السؤال"""
        # قائمة المواضيع الشائعة والكلمات المفتاحية
        topics_map = {
            'الجمع': ['جمع', 'زائد', '+', 'إضافة', 'addition'],
            'الطرح': ['طرح', 'ناقص', '-', 'subtraction'],
            'الضرب': ['ضرب', 'مضروب', '×', '*', 'multiplication'],
            'القسمة': ['قسمة', 'مقسوم', '÷', '/', 'division'],
            'الحروف': ['حرف', 'حروف', 'أبجدية', 'letter', 'alphabet'],
            'الأرقام': ['رقم', 'أرقام', 'عد', 'number', 'counting'],
            'النبات': ['نبات', 'نباتات', 'شجرة', 'زهرة', 'plant', 'tree'],
            'الحيوانات': ['حيوان', 'حيوانات', 'قطة', 'كلب', 'animal'],
            'الأشكال': ['شكل', 'أشكال', 'مربع', 'دائرة', 'مثلث', 'shape'],
            'الألوان': ['لون', 'ألوان', 'أحمر', 'أزرق', 'color']
        }
        
        question_lower = question.lower()
        for topic, keywords in topics_map.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic
        
        # إذا لم نجد موضوع محدد، نحاول استخراج أول كلمة مفيدة
        words = question.split()
        meaningful_words = [word for word in words if len(word) > 2 and word not in ['في', 'من', 'إلى', 'عن', 'مع', 'على']]
        if meaningful_words:
            return meaningful_words[0]
        
        return "الموضوع السابق"
    
    def build_context_summary(self, messages: List[Dict], max_context_length: int = 500) -> str:
        """بناء ملخص للسياق من المحادثات السابقة"""
        if not messages:
            return ""
        
        # أخذ آخر 4 رسائل كحد أقصى لتجنب الإطالة
        recent_messages = messages[-4:] if len(messages) > 4 else messages
        
        context_parts = []
        for msg in recent_messages:
            if msg["role"] == "user":
                context_parts.append(f"الطالب سأل: {msg['content']}")
            elif msg["role"] == "assistant" and 'explanation' in msg:
                # أخذ بداية الشرح فقط
                explanation = msg['explanation'][:100] + "..." if len(msg['explanation']) > 100 else msg['explanation']
                context_parts.append(f"المعلم أجاب: {explanation}")
        
        context_summary = "\n".join(context_parts)
        
        # قطع النص إذا كان طويلاً جداً
        if len(context_summary) > max_context_length:
            context_summary = context_summary[:max_context_length] + "..."
        
        return context_summary

def classify_question_type(question: str, chat_history: List[Dict] = None) -> Dict[str, any]:
    """تصنيف نوع السؤال مع مراعاة تاريخ المحادثة واتخاذ قرار ذكي للرسم المحسن"""
    question_lower = question.lower().strip()
    analyzer = ChatHistoryAnalyzer()
    
    # التحقق من وجود مراجع للمحادثات السابقة
    has_references = analyzer.has_references(question)
    is_clarification = analyzer.is_clarification_request(question)
    is_correction = analyzer.is_correction_request(question)
    
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
    
    # أنماط الأسئلة التي تحتاج رسم بشكل صريح
    explicit_drawing_patterns = [
        r'ارسم.*لي', r'رسم.*', r'أريد.*رسم', r'وضح.*بالرسم', r'بالرسم',
        r'اشرح.*بالصور', r'مع.*رسم', r'draw.*', r'show.*drawing', r'with.*picture'
    ]
    
    # أنماط الأسئلة الرياضية
    math_patterns = [
        r'\d+\s*[+\-×÷]\s*\d+', r'جمع.*\d+', r'طرح.*\d+', r'ضرب.*\d+',
        r'قسمة.*\d+', r'معادلة', r'حساب', r'عملية.*حسابية'
    ]
    
    # مواضيع تحتاج رسم بشكل طبيعي (قرار ذكي محسن)
    high_priority_visual_topics = [
        # رياضيات - أولوية عالية
        r'جمع', r'طرح', r'ضرب', r'قسمة', r'عملية.*حسابية',
        r'مربع', r'مثلث', r'دائرة', r'مستطيل', r'شكل', r'أشكال', r'هندسة',
        r'كسر', r'كسور', r'نصف', r'ربع', r'ثلث',
        r'أرقام', r'أعداد', r'عد', r'ترقيم',
        # علوم - أولوية عالية  
        r'نبات', r'نباتات', r'شجرة', r'زهرة', r'ورقة', r'جذر', r'ساق',
        r'حيوان', r'حيوانات', r'قطة', r'كلب', r'فيل', r'أسد', r'طائر', r'سمك',
        r'جسم.*الإنسان', r'عين', r'أذن', r'يد', r'قدم', r'رأس',
        r'دورة.*حياة', r'نمو', r'تكاثر',
        # لغة عربية - حروف فقط
        r'حرف', r'حروف', r'أبجدية',
        r'خط', r'كتابة.*حرف'
    ]
    
    medium_priority_visual_topics = [
        # علوم أخرى
        r'طقس', r'مطر', r'شمس', r'سحاب', r'ثلج', r'رياح',
        r'مجموعة.*شمسية', r'كواكب', r'قمر', r'نجوم',
        r'ماء', r'هواء', r'تربة',
        # ألوان وأشياء بصرية
        r'لون', r'ألوان', r'أحمر', r'أزرق', r'أخضر', r'أصفر', r'أسود', r'أبيض',
        r'كبير', r'صغير', r'طويل', r'قصير', r'سميك', r'رفيع'
    ]
    
    # مواضيع لا تحتاج رسم عادة (نصوص، قواعد، تعريفات مجردة)
    text_only_topics = [
        r'قاعدة', r'قانون', r'تعريف', r'معنى', r'مفهوم',
        r'تاريخ', r'قصة', r'حكاية', r'سيرة',
        r'دعاء', r'آية', r'حديث', r'ذكر',
        r'إملاء', r'نحو', r'صرف', r'بلاغة',
        r'كلمة', r'كلمات', r'جملة', r'جمل'  # إلا إذا كان حروف
    ]
    
    is_greeting = any(re.search(pattern, question_lower) for pattern in greetings_patterns)
    needs_curriculum_search = any(re.search(pattern, question_lower) for pattern in curriculum_patterns)
    explicit_drawing_requested = any(re.search(pattern, question_lower) for pattern in explicit_drawing_patterns)
    is_math_question = any(re.search(pattern, question_lower) for pattern in math_patterns)
    
    # فحص المواضيع البصرية بأولويات
    is_high_priority_visual = any(re.search(pattern, question_lower) for pattern in high_priority_visual_topics)
    is_medium_priority_visual = any(re.search(pattern, question_lower) for pattern in medium_priority_visual_topics)
    is_text_only_topic = any(re.search(pattern, question_lower) for pattern in text_only_topics)
    
    # تحديد ما إذا كان السؤال تعليمي
    is_educational = needs_curriculum_search or is_math_question or len(question.split()) > 3
    
    # القرار الذكي المحسن للرسم
    smart_drawing_decision = False
    drawing_confidence = 0  # من 0 إلى 100
    
    if explicit_drawing_requested:
        # إذا طلب الرسم صراحة - أولوية قصوى
        smart_drawing_decision = True
        drawing_confidence = 100
    elif is_text_only_topic and not is_high_priority_visual:
        # المواضيع النصية لا تحتاج رسم إلا إذا كانت عالية الأولوية
        smart_drawing_decision = False
        drawing_confidence = 10
    elif is_high_priority_visual:
        # المواضيع عالية الأولوية تحتاج رسم دائماً
        smart_drawing_decision = True
        drawing_confidence = 90
    elif is_math_question:
        # العمليات الرياضية تحتاج رسم عادة
        smart_drawing_decision = True
        drawing_confidence = 85
    elif is_medium_priority_visual:
        # المواضيع متوسطة الأولوية
        smart_drawing_decision = True
        drawing_confidence = 70
    elif has_references and is_clarification:
        # طلب توضيح للموضوع السابق
        smart_drawing_decision = True
        drawing_confidence = 80
    elif is_educational and any(word in question_lower for word in ['كيف', 'أين', 'متى', 'لماذا', 'how', 'where', 'when', 'why']):
        # الأسئلة التفسيرية التعليمية
        smart_drawing_decision = True
        drawing_confidence = 60
    elif is_educational and not is_greeting:
        # أسئلة تعليمية عامة
        smart_drawing_decision = True
        drawing_confidence = 50
    
    # قرار نهائي: رسم فقط للمواضيع التعليمية وليس التحيات
    needs_drawing = smart_drawing_decision and not is_greeting and drawing_confidence >= 50
    
    return {
        'is_greeting': is_greeting,
        'is_educational': is_educational,
        'needs_curriculum_search': is_educational and not is_greeting,
        'needs_drawing': needs_drawing,
        'drawing_confidence': drawing_confidence,
        'is_math_question': is_math_question,
        'is_high_priority_visual': is_high_priority_visual,
        'is_medium_priority_visual': is_medium_priority_visual,
        'is_text_only_topic': is_text_only_topic,
        'explicit_drawing_requested': explicit_drawing_requested,
        'question_complexity': len(question.split()),
        'has_references': has_references,
        'is_clarification': is_clarification,
        'is_correction': is_correction,
        'needs_context': has_references or is_clarification or is_correction,
        'smart_decision_reason': _get_drawing_decision_reason(
            needs_drawing, is_high_priority_visual, is_medium_priority_visual, 
            is_math_question, explicit_drawing_requested, is_text_only_topic, 
            has_references, is_clarification, drawing_confidence
        )
    }

def _get_drawing_decision_reason(needs_drawing: bool, is_high_visual: bool, is_medium_visual: bool,
                               is_math: bool, explicit: bool, is_text_only: bool, 
                               has_refs: bool, is_clarif: bool, confidence: int) -> str:
    """شرح سبب قرار الرسم للتشخيص"""
    if explicit:
        return f"طلب رسم صريح (ثقة: {confidence}%)"
    elif is_text_only and not is_high_visual:
        return f"موضوع نصي لا يحتاج رسم (ثقة: {confidence}%)"
    elif is_high_visual:
        return f"موضوع عالي الأولوية يحتاج رسم (ثقة: {confidence}%)"
    elif is_math:
        return f"موضوع رياضي يحتاج رسم توضيحي (ثقة: {confidence}%)"
    elif is_medium_visual:
        return f"موضوع متوسط الأولوية يستفيد من الرسم (ثقة: {confidence}%)"
    elif has_refs and is_clarif:
        return f"طلب توضيح للموضوع السابق (ثقة: {confidence}%)"
    elif needs_drawing:
        return f"قرار ذكي: الموضوع يستفيد من الرسم (ثقة: {confidence}%)"
    else:
        return f"لا يحتاج رسم (ثقة: {confidence}%)"

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
    
    # لا تبحث للأسئلة القصيرة جداً (كلمة أو كلمتين) إلا إذا كانت تحتوي على مراجع
    if question_type['question_complexity'] <= 2 and not question_type['is_educational'] and not question_type['has_references']:
        return False
    
    # ابحث للأسئلة التعليمية أو التي تحتوي على مراجع
    return question_type['needs_curriculum_search'] or question_type['has_references']

def create_smart_prompt(question: str, question_type: Dict[str, any], app_subject_key: str, 
                       grade_key: str, retrieved_context_str: Optional[str], prompt_engine, 
                       chat_history: List[Dict] = None) -> str:
    """إنشاء برومبت ذكي يراعي نوع السؤال وتاريخ المحادثة مع قرار ذكي للرسم"""
    
    # بناء سياق المحادثة إذا كان هناك مراجع
    conversation_context = ""
    if question_type['needs_context'] and chat_history:
        analyzer = ChatHistoryAnalyzer()
        context_summary = analyzer.build_context_summary(chat_history)
        last_topic = analyzer.extract_last_topic(chat_history)
        
        if context_summary:
            conversation_context = f"""
**سياق المحادثة السابقة:**
{context_summary}

**آخر موضوع تم مناقشته:** {last_topic if last_topic else 'غير محدد'}

**ملاحظة مهمة:** السؤال الحالي "{question}" يبدو أنه يشير إلى الموضوع السابق. 
يرجى فهم السياق والإجابة بناءً على ما تم مناقشته مسبقاً.
"""
    
    # الحصول على البرومبت الأساسي
    base_prompt = prompt_engine.get_specialized_prompt(
        question=question,
        app_subject_key=app_subject_key,
        grade_key=grade_key,
        retrieved_context_str=retrieved_context_str,
        conversation_context=conversation_context
    )
    
    # إضافة تعليمات خاصة بقرار الرسم الذكي المحسن
    if question_type['needs_drawing']:
        smart_drawing_instruction = f"""
**تعليمة ذكية للرسم (ثقة {question_type['drawing_confidence']}%):**
تم اتخاذ قرار ذكي بأن هذا السؤال يحتاج رسم توضيحي.
السبب: {question_type.get('smart_decision_reason', 'موضوع يستفيد من التوضيح البصري')}

يرجى إنتاج رسم SVG مناسب وواضح يساعد في فهم الموضوع بشكل بصري.
اجعل الرسم بسيط ومناسب لعمر الطفل وملون وجذاب.
**تأكد من أن الرسم يساهم فعلاً في الفهم وليس مجرد زخرفة.**
"""
        base_prompt += "\n" + smart_drawing_instruction
    else:
        no_drawing_instruction = f"""
**تعليمة عدم الرسم (ثقة {question_type['drawing_confidence']}%):**
تم اتخاذ قرار ذكي بأن هذا السؤال لا يحتاج رسم توضيحي.
السبب: {question_type.get('smart_decision_reason', 'موضوع لا يستفيد من الرسم')}

يجب أن يكون `svg_code` هو `null` في الاستجابة.
ركز على تقديم شرح نصي واضح ومفيد فقط.
"""
        base_prompt += "\n" + no_drawing_instruction
    
    if question_type['is_greeting']:
        greeting_instruction = """
**تعليمة خاصة للتحيات:**
هذا سؤال تحية أو اجتماعي. لا تبحث في المنهج ولا ترسم أي شيء.
قدم رداً ودوداً ومناسباً لطفل في المرحلة الابتدائية.
"""
        base_prompt += "\n" + greeting_instruction
    
    if question_type['has_references']:
        reference_instruction = """
**تعليمة خاصة للمراجع:**
هذا السؤال يحتوي على مراجع لمحادثات سابقة. تأكد من فهم السياق السابق والإجابة بناءً عليه.
استخدم المعلومات من سياق المحادثة السابقة لتقديم إجابة مترابطة ومفهومة.
"""
        base_prompt += "\n" + reference_instruction
    
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
            "details": "مكتبات RAG غير مثبتة بشكل صحيح",
            "docs_exist": False,
            "dbs_exist": False,
            "total_expected": 0,
            "total_found_docs": 0,
            "total_found_dbs": 0,
            "missing_docs": [],
            "missing_dbs": [],
            "empty_docs": [],
            "build_errors": [],
            "grade_details": {}
        }
    
    try:
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
        
    except Exception as e:
        # في حالة حدوث خطأ، إرجاع قيم افتراضية آمنة
        return {
            "available": False,
            "reason": f"خطأ في الفحص: {str(e)}",
            "details": str(e),
            "docs_exist": False,
            "dbs_exist": False,
            "total_expected": 0,
            "total_found_docs": 0,
            "total_found_dbs": 0,
            "missing_docs": [],
            "missing_dbs": [],
            "empty_docs": [],
            "build_errors": [str(e)],
            "grade_details": {}
        }

@st.cache_data
def build_knowledge_bases_with_error_handling(project_id: str, location: str, force_rebuild: bool = False) -> Dict[str, Any]:
    """بناء قواعد المعرفة مع معالجة تفصيلية للأخطاء (بصمت)"""
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
    
    for i, (grade_key, subject_key, subject_folder) in enumerate(subjects_to_build):
        grade_name = GRADE_SUBJECTS[grade_key]['name']
        subject_name = GRADE_SUBJECTS[grade_key]['subjects'][subject_key]
        collection_name = f"{grade_key}_{subject_folder.replace(' ', '_').lower()}_coll"
        
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
        return ""

def process_user_question_improved(question: str, gemini_client, kb_manager, prompt_engine, 
                                 grade_key: str, subject_key: str, chat_history: List[Dict] = None):
    """نسخة محسنة من معالج الأسئلة مع قرار ذكي للرسم ودعم تاريخ المحادثة"""
    # تصنيف نوع السؤال مع مراعاة تاريخ المحادثة والقرار الذكي للرسم
    question_type = classify_question_type(question, chat_history)
    
    # التعامل مع التحيات
    if question_type['is_greeting']:
        return get_greeting_response(question, grade_key, subject_key)
    
    # البحث في المنهج إذا لزم الأمر
    context = ""
    search_status = "not_searched"
    
    # إذا كان السؤال يحتوي على مراجع، استخدم آخر موضوع للبحث
    search_query = question
    if question_type['has_references'] and chat_history:
        analyzer = ChatHistoryAnalyzer()
        last_topic = analyzer.extract_last_topic(chat_history)
        if last_topic:
            search_query = f"{last_topic} {question}"
    
    if should_search_curriculum(question, question_type):
        if kb_manager and hasattr(kb_manager, 'db') and kb_manager.db:
            try:
                context = retrieve_context(kb_manager, search_query)
                if context:
                    search_status = "found"
                else:
                    search_status = "not_found"
            except Exception as e:
                search_status = "error"
        else:
            search_status = "no_kb"
    
    # إنشاء البرومبت مع القرار الذكي للرسم ومراعاة تاريخ المحادثة
    if prompt_engine:
        specialized_prompt = create_smart_prompt(
            question=question,
            question_type=question_type,
            app_subject_key=subject_key,
            grade_key=grade_key,
            retrieved_context_str=context if context else None,
            prompt_engine=prompt_engine,
            chat_history=chat_history
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
    
    # تطبيق القرار الذكي للرسم: إزالة الرسم إذا لم يقرر النظام أنه مطلوب
    if not question_type['needs_drawing']:
        response['svg_code'] = None
    
    return {
        'explanation': response.get("text_explanation", "عذرًا، لم أتمكن من إنتاج شرح مناسب."),
        'svg_code': response.get("svg_code"),
        'quality_scores': response.get("quality_scores", {}),
        'quality_issues': response.get("quality_issues", []),
        'search_status': search_status,
        'drawing_decision': question_type.get('smart_decision_reason', 'غير محدد'),
        'drawing_confidence': question_type.get('drawing_confidence', 0),
        'question_analysis': {
            'is_high_priority_visual': question_type.get('is_high_priority_visual', False),
            'is_medium_priority_visual': question_type.get('is_medium_priority_visual', False),
            'is_math_question': question_type.get('is_math_question', False),
            'explicit_drawing': question_type.get('explicit_drawing_requested', False),
            'needs_drawing': question_type['needs_drawing']
        }
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

def display_sidebar():
    """عرض الشريط الجانبي المبسط"""
    with st.sidebar:
        st.title("إعدادات التعلم")
       
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
       
        # تحديث session state وحذف المحادثة عند التغيير
        if (st.session_state.selected_grade != selected_grade or 
            st.session_state.selected_subject != selected_subject):
            # حذف المحادثة السابقة عند تغيير الصف أو المادة
            st.session_state.messages = []
            st.session_state.conversation_started = False
            st.session_state.selected_grade = selected_grade
            st.session_state.selected_subject = selected_subject
            st.rerun()
       
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

def display_message(message: Dict, is_new: bool = False):
    """عرض رسالة واحدة في المحادثة مع تحسين عرض SVG"""
   
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(f"**أنت:** {message['content']}")
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")
   
    elif message["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
           
            # عرض الشرح النصي
            if 'explanation' in message:
                st.write(message['explanation'])
           
            # عرض الرسم SVG إذا كان موجوداً مع تحسين العرض
            if 'svg_code' in message and message['svg_code']:
                st.subheader("🎨 الرسم التوضيحي:")
               
                col1, col2 = st.columns([4, 1])
               
                with col1:
                    try:
                        # تحسين عرض SVG ليكون scalable ومناسب للحاوية
                        st.components.v1.html(
                            f"""
                            <div style="
                                display: flex; 
                                justify-content: center; 
                                align-items: center;
                                background-color: white; 
                                padding: 20px; 
                                border-radius: 10px;
                                border: 2px solid #e0e0e0;
                                width: 100%;
                                height: 400px;
                                overflow: hidden;
                            ">
                                <div style="
                                    width: 100%; 
                                    height: 100%; 
                                    display: flex; 
                                    justify-content: center; 
                                    align-items: center;
                                ">
                                    <svg style="
                                        max-width: 100%; 
                                        max-height: 100%; 
                                        width: auto; 
                                        height: auto;
                                    " viewBox="0 0 700 500" preserveAspectRatio="xMidYMid meet">
                                        {message['svg_code'].replace('<svg', '').replace('</svg>', '').replace('width="700"', '').replace('height="500"', '')}
                                    </svg>
                                </div>
                            </div>
                            """,
                            height=450
                        )
                    except Exception as e:
                        st.error(f"❌ خطأ في عرض الرسم: {e}")
               
                with col2:
                    st.write("💾 **تحميل:**")
                   
                    st.download_button(
                        label="⬇️ SVG",
                        data=message['svg_code'],
                        file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                        mime="image/svg+xml",
                        key=f"download_svg_{message.get('id', 'unknown')}"
                    )
                    
                    # عرض معلومات قرار الرسم إذا كانت متوفرة
                    if 'drawing_decision' in message:
                        st.caption(f"🧠 **قرار الرسم:** {message['drawing_decision']}")
                    
                    if 'drawing_confidence' in message:
                        confidence = message['drawing_confidence']
                        if confidence > 0:
                            st.caption(f"📊 **ثقة القرار:** {confidence}%")
           
            # عرض الوقت
            if 'timestamp' in message:
                st.caption(f"🕒 {message['timestamp']}")

def main():
    """الدالة الرئيسية المحسنة للتطبيق مع دعم Chat History Memory والنظام الذكي للرسم"""
   
    # تهيئة حالة الجلسة
    initialize_session_state()
   
    st.title(APP_TITLE)
   
    # تحميل متغيرات البيئة بصمت
    project_id, location, credentials_path = load_environment_variables_silently()
    
    if not project_id:
        st.error("❌ لم يتم تعيين بيانات Google Cloud في Streamlit Secrets")
        st.info("💡 يرجى إضافة المتغيرات المطلوبة في إعدادات التطبيق")
        st.stop()
    
    # فحص وبناء قواعد المعرفة إذا لزم الأمر (بصمت)
    if not st.session_state.knowledge_bases_built:
        kb_status = check_knowledge_base_detailed_status(project_id, location)
        
        if not kb_status["docs_exist"] or kb_status["total_found_docs"] == 0:
            st.session_state.knowledge_bases_built = True
        elif len(kb_status["missing_dbs"]) > 0:
            # بناء صامت لقواعد المعرفة
            build_result = build_knowledge_bases_with_error_handling(project_id, location)
            st.session_state.knowledge_bases_built = True
        else:
            st.session_state.knowledge_bases_built = True
   
    # عرض الشريط الجانبي
    selected_grade, selected_subject = display_sidebar()
   
    # تهيئة المكونات بصمت
    gemini_client = None
    if GEMINI_CLIENT_AVAILABLE:
        gemini_client = initialize_gemini_client(project_id, location)
    
    kb_manager = None
    if KB_MANAGER_AVAILABLE:
        kb_manager = initialize_knowledge_base(project_id, location, selected_grade, selected_subject)
    
    prompt_engine = initialize_prompt_engine()
   
    # عرض رسالة الترحيب إذا لم تبدأ المحادثة
    if not st.session_state.conversation_started:
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
            st.write(f"أهلاً وسهلاً! أنا معلمك الذكي للصف {GRADE_SUBJECTS[selected_grade]['name']} في مادة {GRADE_SUBJECTS[selected_grade]['subjects'][selected_subject]}.")
            if GEMINI_CLIENT_AVAILABLE and gemini_client:
                st.write("اسألني أي سؤال وسأجيبك بشرح مبسط ورسم توضيحي عند الحاجة! 😊")
                st.write("💡 **النظام الذكي للرسم:** سأقرر بنفسي متى أحتاج لرسم توضيحي لمساعدتك في الفهم!")
            else:
                st.write("يمكنني الإجابة على أسئلتك النصية! 📚")
       
        st.session_state.conversation_started = True
   
    # عرض المحادثة السابقة
    for message in st.session_state.messages:
        display_message(message)
   
    # مربع إدخال السؤال الجديد
    if prompt := st.chat_input("اكتب سؤالك هنا... 💭"):
        # إضافة سؤال المستخدم
        add_message("user", prompt)
        display_message(st.session_state.messages[-1])
       
        # معالجة السؤال وإنتاج الإجابة باستخدام المعالج المحسن مع تاريخ المحادثة
        with st.chat_message("assistant", avatar="🤖"):
            st.write("**المعلم الذكي:**")
           
            with st.spinner("🤖 المعلم الذكي يفكر في الإجابة..."):
                try:
                    # استخدام المعالج المحسن مع تمرير تاريخ المحادثة
                    response_data = process_user_question_improved(
                        prompt, gemini_client, kb_manager, prompt_engine,
                        selected_grade, selected_subject, st.session_state.messages[:-1]  # تمرير كل الرسائل ما عدا السؤال الحالي
                    )
                   
                    # عرض الشرح
                    st.write(response_data['explanation'])
                   
                    # عرض الرسم إذا كان موجوداً مع التحسين الجديد
                    if response_data['svg_code']:
                        st.subheader("🎨 الرسم التوضيحي:")
                       
                        col1, col2 = st.columns([4, 1])
                       
                        with col1:
                            try:
                                # تحسين عرض SVG ليكون scalable ومناسب للحاوية
                                st.components.v1.html(
                                    f"""
                                    <div style="
                                        display: flex; 
                                        justify-content: center; 
                                        align-items: center;
                                        background-color: white; 
                                        padding: 20px; 
                                        border-radius: 10px;
                                        border: 2px solid #e0e0e0;
                                        width: 100%;
                                        height: 400px;
                                        overflow: hidden;
                                    ">
                                        <div style="
                                            width: 100%; 
                                            height: 100%; 
                                            display: flex; 
                                            justify-content: center; 
                                            align-items: center;
                                        ">
                                            <svg style="
                                                max-width: 100%; 
                                                max-height: 100%; 
                                                width: auto; 
                                                height: auto;
                                            " viewBox="0 0 700 500" preserveAspectRatio="xMidYMid meet">
                                                {response_data['svg_code'].replace('<svg', '').replace('</svg>', '').replace('width="700"', '').replace('height="500"', '')}
                                            </svg>
                                        </div>
                                    </div>
                                    """,
                                    height=450
                                )
                            except Exception as e:
                                st.error(f"❌ خطأ في عرض الرسم: {e}")
                       
                        with col2:
                            st.write("💾 **تحميل:**")
                            st.download_button(
                                label="⬇️ SVG",
                                data=response_data['svg_code'],
                                file_name=f"رسم_توضيحي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                                mime="image/svg+xml",
                                key=f"download_svg_new"
                            )
                            
                            # عرض معلومات قرار الرسم
                            if response_data.get('drawing_decision'):
                                st.caption(f"🧠 **قرار الرسم:** {response_data['drawing_decision']}")
                            
                            if response_data.get('drawing_confidence', 0) > 0:
                                confidence = response_data['drawing_confidence']
                                st.caption(f"📊 **ثقة القرار:** {confidence}%")
                    else:
                        # عرض سبب عدم الرسم إذا لم يكن هناك رسم
                        if response_data.get('drawing_decision'):
                            st.caption(f"💭 **لماذا لا يوجد رسم؟** {response_data['drawing_decision']}")
                   
                    # إضافة إجابة المساعد للمحادثة
                    add_message("assistant", "", **response_data)
                   
                except Exception as e:
                    error_msg = f"❌ حدث خطأ: {e}"
                    st.error(error_msg)
                    add_message("assistant", error_msg)

if __name__ == "__main__":
    main()
