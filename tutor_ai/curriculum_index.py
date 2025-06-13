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
