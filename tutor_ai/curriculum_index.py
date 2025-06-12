# إضافة فهرس المواد التفاعلي - الملفات المطلوب تعديلها

# =============================================================================
# 1. إنشاء ملف جديد: tutor_ai/curriculum_index.py
# =============================================================================

import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class CurriculumIndex:
    """فهرس المنهج التفاعلي - لربط طلبات الطلاب بمحتوى المنهج المحدد"""
    
    def __init__(self):
        # تحميل فهرس المنهج من ملف JSON
        self.curriculum_data = self._load_curriculum_index()
        
        # أنماط التعرف على طلبات الدروس
        self.lesson_patterns = [
            r'الدرس\s*(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)',
            r'الدرس\s*(\d+|[١-٩])',
            r'درس\s*(\d+|[١-٩])',
            r'وحدة\s*(\d+|[١-٩])',
            r'الوحدة\s*(الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة)',
            r'فصل\s*(\d+|[١-٩])',
            r'الفصل\s*(الأول|الثاني|الثالث|الرابع|الخامس|السادس)'
        ]
        
        # تحويل الأرقام العربية والكلمات إلى أرقام
        self.number_mapping = {
            'الأول': '1', 'الثاني': '2', 'الثالث': '3', 'الرابع': '4', 'الخامس': '5',
            'السادس': '6', 'السابع': '7', 'الثامن': '8', 'التاسع': '9', 'العاشر': '10',
            'الأولى': '1', 'الثانية': '2', 'الثالثة': '3', 'الرابعة': '4', 'الخامسة': '5', 'السادسة': '6',
            '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }

    def _load_curriculum_index(self) -> Dict:
        """تحميل فهرس المنهج من ملف JSON"""
        try:
            # البحث عن ملف الفهرس في عدة مواقع محتملة
            possible_paths = [
                Path("curriculum_index.json"),
                Path("data/curriculum_index.json"),
                Path("tutor_ai/curriculum_index.json")
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # إذا لم يوجد الملف، نحاول إنشاؤه من البيانات المرفقة
            return self._create_default_index()
            
        except Exception as e:
            print(f"خطأ في تحميل فهرس المنهج: {e}")
            return {}

    def _create_default_index(self) -> Dict:
        """إنشاء فهرس افتراضي إذا لم يوجد الملف"""
        # هذا مثال مبسط - يجب استبداله بالبيانات الكاملة المرفقة
        return {
            "grade_1": {
                "arabic": {
                    "subject_name": "لغتي الجميلة",
                    "units": {
                        "الوحدة 1": {
                            "name": "أسرتي",
                            "lessons": {
                                "الدرس 1": {"name": "حرف الألف", "keywords": ["أبجدية", "حرف", "كتابة"]},
                                "الدرس 2": {"name": "حرف الباء", "keywords": ["أبجدية", "حرف", "كتابة"]}
                            }
                        }
                    }
                }
            }
        }

    def detect_lesson_request(self, question: str, grade_key: str, subject_key: str) -> Optional[Dict]:
        """اكتشاف طلب درس محدد من السؤال"""
        question_clean = question.strip().lower()
        
        # البحث عن أنماط الدروس
        for pattern in self.lesson_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                lesson_identifier = match.group(1)
                lesson_number = self._convert_to_number(lesson_identifier)
                
                if lesson_number:
                    lesson_info = self._get_lesson_info(grade_key, subject_key, lesson_number)
                    if lesson_info:
                        return {
                            'type': 'specific_lesson',
                            'lesson_number': lesson_number,
                            'lesson_info': lesson_info,
                            'search_query': self._build_lesson_search_query(lesson_info, question)
                        }
        
        return None

    def _convert_to_number(self, identifier: str) -> Optional[str]:
        """تحويل المعرف إلى رقم"""
        if identifier in self.number_mapping:
            return self.number_mapping[identifier]
        elif identifier.isdigit():
            return identifier
        return None

    def _get_lesson_info(self, grade_key: str, subject_key: str, lesson_number: str) -> Optional[Dict]:
        """الحصول على معلومات الدرس المحدد"""
        try:
            # تحويل مفتاح المادة إلى مفتاح الفهرس
            index_subject_key = self._map_subject_key(subject_key)
            
            if grade_key not in self.curriculum_data:
                return None
                
            grade_data = self.curriculum_data[grade_key]
            if index_subject_key not in grade_data:
                return None
                
            subject_data = grade_data[index_subject_key]
            
            # البحث في جميع الوحدات عن الدرس
            for unit_key, unit_data in subject_data.get('units', {}).items():
                lessons = unit_data.get('lessons', {})
                for lesson_key, lesson_data in lessons.items():
                    if f"الدرس {lesson_number}" in lesson_key or f"الدرس ال{lesson_number}" in lesson_key:
                        return {
                            'unit_name': unit_data.get('name', unit_key),
                            'lesson_name': lesson_data.get('name', lesson_key),
                            'keywords': lesson_data.get('keywords', []),
                            'unit_key': unit_key,
                            'lesson_key': lesson_key
                        }
            
            return None
            
        except Exception as e:
            print(f"خطأ في الحصول على معلومات الدرس: {e}")
            return None

    def _map_subject_key(self, app_subject_key: str) -> str:
        """تحويل مفتاح المادة من التطبيق إلى مفتاح الفهرس"""
        mapping = {
            'arabic': 'lughati',
            'math': 'Math',
            'science': 'Science',
            'islamic': 'الدراسات الاسلامية',
            'english': 'English'
        }
        return mapping.get(app_subject_key, app_subject_key)

    def _build_lesson_search_query(self, lesson_info: Dict, original_question: str) -> str:
        """بناء استعلام بحث محسن للدرس"""
        search_parts = []
        
        # إضافة اسم الدرس
        if lesson_info.get('lesson_name'):
            search_parts.append(lesson_info['lesson_name'])
        
        # إضافة الكلمات المفتاحية
        keywords = lesson_info.get('keywords', [])
        if keywords:
            search_parts.extend(keywords[:3])  # أهم 3 كلمات مفتاحية
        
        # إضافة اسم الوحدة
        if lesson_info.get('unit_name'):
            search_parts.append(lesson_info['unit_name'])
        
        # إضافة كلمات من السؤال الأصلي (تنظيف)
        question_words = self._extract_relevant_words(original_question)
        search_parts.extend(question_words)
        
        return ' '.join(search_parts)

    def _extract_relevant_words(self, question: str) -> List[str]:
        """استخراج الكلمات المهمة من السؤال"""
        # كلمات يجب تجاهلها
        stop_words = {'في', 'من', 'إلى', 'على', 'عن', 'مع', 'اشرح', 'علمني', 'أريد', 'كيف', 'ما', 'هو', 'هي'}
        
        words = question.split()
        relevant_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\u0020-\u007F]', '', word)
            if len(clean_word) > 2 and clean_word not in stop_words:
                relevant_words.append(clean_word)
        
        return relevant_words[:3]  # أهم 3 كلمات

    def get_lesson_context(self, grade_key: str, subject_key: str, lesson_number: str) -> str:
        """الحصول على سياق إضافي للدرس لتحسين البحث"""
        lesson_info = self._get_lesson_info(grade_key, subject_key, lesson_number)
        if not lesson_info:
            return ""
        
        context_parts = [
            f"الوحدة: {lesson_info.get('unit_name', '')}",
            f"الدرس: {lesson_info.get('lesson_name', '')}",
            f"المواضيع: {', '.join(lesson_info.get('keywords', []))}"
        ]
        
        return " | ".join(context_parts)


# =============================================================================
# 2. تعديل ملف app.py - إضافة الاستيرادات
# =============================================================================

# في بداية ملف app.py، أضف:
try:
    from tutor_ai.curriculum_index import CurriculumIndex
    CURRICULUM_INDEX_AVAILABLE = True
except Exception as e:
    CURRICULUM_INDEX_AVAILABLE = False

# =============================================================================
# 3. تعديل دالة classify_question_type في app.py
# =============================================================================

def classify_question_type_enhanced(question: str, chat_history: List[Dict] = None, 
                                   grade_key: str = None, subject_key: str = None) -> Dict[str, any]:
    """تصنيف نوع السؤال مع كشف طلبات الدروس المحددة"""
    
    # استدعاء التصنيف الأساسي
    basic_classification = classify_question_type(question, chat_history)
    
    # إضافة كشف الدروس المحددة
    lesson_request = None
    if CURRICULUM_INDEX_AVAILABLE and grade_key and subject_key:
        curriculum_index = CurriculumIndex()
        lesson_request = curriculum_index.detect_lesson_request(question, grade_key, subject_key)
    
    # دمج النتائج
    basic_classification.update({
        'lesson_request': lesson_request,
        'is_specific_lesson': lesson_request is not None,
        'enhanced_search_needed': lesson_request is not None
    })
    
    return basic_classification

# =============================================================================
# 4. تعديل دالة process_user_question_improved في app.py
# =============================================================================

def process_user_question_enhanced(question: str, gemini_client, kb_manager, prompt_engine, 
                                  grade_key: str, subject_key: str, chat_history: List[Dict] = None):
    """نسخة محسنة مع دعم الدروس المحددة"""
    
    # تصنيف السؤال مع كشف الدروس
    question_type = classify_question_type_enhanced(question, chat_history, grade_key, subject_key)
    
    # التعامل مع التحيات (بدون تغيير)
    if question_type['is_greeting']:
        return get_greeting_response(question, grade_key, subject_key)
    
    # معالجة خاصة للدروس المحددة
    context = ""
    search_status = "not_searched"
    
    if question_type['is_specific_lesson'] and question_type['lesson_request']:
        lesson_info = question_type['lesson_request']['lesson_info']
        enhanced_query = question_type['lesson_request']['search_query']
        
        # بحث محسن باستخدام معلومات الدرس
        if kb_manager and hasattr(kb_manager, 'db') and kb_manager.db:
            try:
                context = retrieve_context(kb_manager, enhanced_query, k_results=5)  # نتائج أكثر للدروس المحددة
                if context:
                    search_status = "found_specific_lesson"
                    # إضافة سياق إضافي عن الدرس
                    lesson_context = f"\n\n=== معلومات الدرس ===\nالوحدة: {lesson_info.get('unit_name', '')}\nالدرس: {lesson_info.get('lesson_name', '')}\nالمواضيع الرئيسية: {', '.join(lesson_info.get('keywords', []))}\n========================\n"
                    context = lesson_context + context
                else:
                    search_status = "lesson_not_found"
            except Exception as e:
                search_status = "error"
    else:
        # البحث العادي للأسئلة غير المحددة
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

    # إنشاء البرومبت المحسن
    if prompt_engine:
        specialized_prompt = create_enhanced_prompt(
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

    # تطبيق قرار الرسم
    if not question_type['needs_drawing']:
        response['svg_code'] = None

    return {
        'explanation': response.get("text_explanation", "عذرًا، لم أتمكن من إنتاج شرح مناسب."),
        'svg_code': response.get("svg_code"),
        'quality_scores': response.get("quality_scores", {}),
        'quality_issues': response.get("quality_issues", []),
        'search_status': search_status,
        'lesson_info': question_type.get('lesson_request', {}).get('lesson_info') if question_type['is_specific_lesson'] else None,
        'drawing_decision': question_type.get('smart_decision_reason', 'غير محدد'),
        'drawing_confidence': question_type.get('drawing_confidence', 0),
        'question_analysis': {
            'is_specific_lesson': question_type['is_specific_lesson'],
            'is_high_priority_visual': question_type.get('is_high_priority_visual', False),
            'is_medium_priority_visual': question_type.get('is_medium_priority_visual', False),
            'is_math_question': question_type.get('is_math_question', False),
            'explicit_drawing': question_type.get('explicit_drawing_requested', False),
            'needs_drawing': question_type['needs_drawing']
        }
    }

# =============================================================================
# 5. إنشاء دالة create_enhanced_prompt
# =============================================================================

def create_enhanced_prompt(question: str, question_type: Dict[str, any], app_subject_key: str, 
                          grade_key: str, retrieved_context_str: Optional[str], prompt_engine, 
                          chat_history: List[Dict] = None) -> str:
    """إنشاء برومبت محسن للدروس المحددة"""
    
    # البرومبت الأساسي
    base_prompt = create_smart_prompt(
        question=question,
        question_type=question_type,
        app_subject_key=app_subject_key,
        grade_key=grade_key,
        retrieved_context_str=retrieved_context_str,
        prompt_engine=prompt_engine,
        chat_history=chat_history
    )
    
    # إضافة تعليمات خاصة بالدروس المحددة
    if question_type.get('is_specific_lesson') and question_type.get('lesson_request'):
        lesson_info = question_type['lesson_request']['lesson_info']
        
        lesson_specific_instruction = f"""
**تعليمات خاصة للدرس المحدد:**
تم اكتشاف أن الطالب يسأل عن درس محدد من المنهج:
- الوحدة: {lesson_info.get('unit_name', '')}
- الدرس: {lesson_info.get('lesson_name', '')}
- المواضيع الرئيسية: {', '.join(lesson_info.get('keywords', []))}

يرجى التركيز على شرح محتوى هذا الدرس تحديداً بناءً على المعلومات المسترجعة من المنهج.
اجعل الشرح شاملاً ومتدرجاً كما لو كنت تشرح الدرس كاملاً للطالب.
"""
        base_prompt += "\n" + lesson_specific_instruction
    
    return base_prompt

# =============================================================================
# 6. تحديث الدالة الرئيسية في app.py
# =============================================================================

# في دالة main()، استبدل استدعاء process_user_question_improved بـ:
response_data = process_user_question_enhanced(
    prompt, gemini_client, kb_manager, prompt_engine,
    selected_grade, selected_subject, st.session_state.messages[:-1]
)

# =============================================================================
# 7. إنشاء ملف curriculum_index.json (يجب وضعه في جذر المشروع)
# =============================================================================

# ملف curriculum_index.json سيحتوي على البيانات المرفقة
# يجب نسخ محتوى الـ JSON المرفق إلى هذا الملف

print("تم إنشاء جميع التعديلات المطلوبة!")
print("الملفات التي تحتاج إنشاء/تعديل:")
print("1. إنشاء: tutor_ai/curriculum_index.py")
print("2. إنشاء: curriculum_index.json (في جذر المشروع)")
print("3. تعديل: app.py (إضافة الدوال المحسنة)")
print("4. تعديل: استدعاءات المعالج في main()")
