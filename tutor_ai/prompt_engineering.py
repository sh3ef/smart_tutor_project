# tutor_ai/prompt_engineering.py
# محرك البرومبت الموحد والمتطور - محدث مع التحكم الذكي في الرسم

import re
from typing import Dict, List, Tuple, Optional


class UnifiedPromptEngine:
    """محرك البرومبت الموحد والمتطور - يجمع بين التخصص بالمادة والصف الدراسي، مع دعم السياق المسترجع (RAG) والتحكم الذكي في الرسم"""
   
    def __init__(self):
        self.grade_info = {
            'grade_1': {
                'name': 'الصف الأول الابتدائي', 'age_range': '6-7 سنوات',
                'style_desc': 'مرح جداً، لغة بسيطة للغاية، استخدام إيموجي وأمثلة من عالم الطفل (ألعاب، حيوانات، حلويات).',
                'svg_complexity': 'بسيط جداً، ألوان زاهية، أشكال كبيرة وواضحة، وجوه مبتسمة اختيارية للعناصر.',
                'explanation_length': '20-50 كلمة',
                'svg_font_size_large': "100px", # للحروف والأرقام الرئيسية
                'svg_font_size_small': "20px",  # للتسميات الصغيرة
            },
            'grade_2': {
                'name': 'الصف الثاني الابتدائي', 'age_range': '7-8 سنوات',
                'style_desc': 'مرح وودود، لغة بسيطة مع بعض المفردات الجديدة، أمثلة من الحياة اليومية والمدرسة.',
                'svg_complexity': 'بسيط إلى متوسط، ألوان جذابة، تفاصيل أوضح قليلاً، يمكن تضمين تسميات نصية.',
                'explanation_length': '30-70 كلمة',
                'svg_font_size_large': "90px",
                'svg_font_size_small': "18px",
            },
            'grade_3': {
                'name': 'الصف الثالث الابتدائي', 'age_range': '8-9 سنوات',
                'style_desc': 'واضح ومباشر، لغة سهلة مع إمكانية استخدام مصطلحات بسيطة جديدة، أمثلة واقعية ومترابطة.',
                'svg_complexity': 'متوسط، تفاصيل أكثر دقة، رسوم بيانية بسيطة إذا لزم الأمر، تسميات واضحة.',
                'explanation_length': '40-90 كلمة',
                'svg_font_size_large': "80px",
                'svg_font_size_small': "16px",
            },
            'grade_4': {
                'name': 'الصف الرابع الابتدائي', 'age_range': '9-10 سنوات',
                'style_desc': 'شرح تفصيلي أكثر بقليل، لغة واضحة مع استخدام مصطلحات منهجية. تشجيع التفكير النقدي.',
                'svg_complexity': 'متوسط إلى معقد قليلاً، يمكن أن يتضمن رسومًا بيانية بسيطة أو مخططات، تفاصيل دقيقة، تسميات متعددة.',
                'explanation_length': '60-120 كلمة',
                'svg_font_size_large': "70px",
                'svg_font_size_small': "14px",
            },
            'grade_5': {
                'name': 'الصف الخامس الابتدائي', 'age_range': '10-11 سنوات',
                'style_desc': 'أسلوب تعليمي موجه، لغة أكاديمية مبسطة، ربط المفاهيم ببعضها. حث على الاستنتاج.',
                'svg_complexity': 'معقد نسبياً، رسوم بيانية تفصيلية، مخططات سير، توضيحات علمية أو رياضية دقيقة، تسميات دقيقة.',
                'explanation_length': '80-150 كلمة',
                'svg_font_size_large': "60px",
                'svg_font_size_small': "12px",
            },
            'grade_6': {
                'name': 'الصف السادس الابتدائي', 'age_range': '11-12 سنوات',
                'style_desc': 'أسلوب احترافي ومختصر، لغة أكاديمية، مراجعة للمفاهيم السابقة وتقديم مفاهيم جديدة. تشجيع البحث.',
                'svg_complexity': 'معقد، يمكن أن يحتوي على تفاعلات أو مراحل، رسوم توضيحية مفصلة للغاية، جداول، مقارنات بصرية.',
                'explanation_length': '100-200 كلمة',
                'svg_font_size_large': "50px",
                'svg_font_size_small': "10px",
            }
        }

        self.base_svg_config = {
            'width': 700, # عرض مناسب لمعظم الشاشات المقسمة
            'height': 500, # ارتفاع مناسب
            'background_color': 'white', # لون خلفية SVG
            'default_stroke_color': '#333333', # لون الحدود الافتراضي للعناصر
            'primary_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FED766', '#2AB7CA'], # مجموعة ألوان أساسية مرحة
            'text_color': '#2C3E50' # لون النص الرئيسي داخل SVG
        }

    def get_specialized_prompt(self, question: str, app_subject_key: str, grade_key: str, 
                              retrieved_context_str: Optional[str] = None) -> str:
        """
        الدالة الرئيسية لإنشاء برومبت مخصص.
        Args:
            question (str): سؤال المستخدم.
            app_subject_key (str): مفتاح المادة كما هو مستخدم في التطبيق (e.g., 'arabic', 'math').
            grade_key (str): مفتاح الصف (e.g., 'grade_1', 'grade_2').
            retrieved_context_str (Optional[str]): السياق النصي المسترجع من قاعدة المعرفة.
        """
        grade_details = self.grade_info.get(grade_key, self.grade_info['grade_1'])
        
        # تحديد ما إذا كان يجب إنتاج SVG
        should_generate_svg = self._should_generate_svg_for_question(question, app_subject_key)
        
        # بناء جزء السياق المسترجع للحقن في البرومبت
        context_injection = ""
        if retrieved_context_str and retrieved_context_str.strip():
            context_injection = f"""
---
[معلومات إضافية من المنهج الدراسي لمادة {self._get_subject_display_name(app_subject_key)}]
استخدم هذه المعلومات من المنهج الدراسي لمساعدتك في الإجابة على سؤال الطفل بدقة أكبر.
إذا كانت المعلومات المسترجعة غير ذات صلة مباشرة بالسؤال، يمكنك تجاهلها والاعتماد على معرفتك العامة.
تأكد من أن إجابتك النهائية موجهة للطفل بالأسلوب المطلوب.

المعلومات المسترجعة:
{retrieved_context_str}
---
"""

        # تعليمات الرسم الذكية
        svg_instructions = ""
        if should_generate_svg:
            svg_instructions = f"""
4.  **الرسوم التوضيحية (SVG) - مطلوبة للسؤال:**
    *   يجب أن يكون `svg_code` عبارة عن كود SVG كامل وصالح للعرض، يبدأ بـ `<svg ...>` وينتهي بـ `</svg>`.
    *   استخدم الأبعاد: `width="{self.base_svg_config['width']}"` و `height="{self.base_svg_config['height']}"`.
    *   اجعل خلفية الرسم `{self.base_svg_config['background_color']}`.
    *   يجب أن يكون الرسم جذابًا بصريًا، بسيطًا، وواضحًا، ويعكس تعقيدًا مناسبًا لـ {grade_details['svg_complexity']}.
    *   استخدم ألوانًا زاهية ومناسبة للأطفال من هذه القائمة: {', '.join(self.base_svg_config['primary_colors'])}.
    *   تأكد من أن الرسم يخدم الغرض التعليمي ويساعد الطفل على فهم المفهوم بشكل أفضل.
    *   إذا كان هناك نص داخل الرسم، استخدم حجم `{grade_details['svg_font_size_large']}` للعناصر الكبيرة و `{grade_details['svg_font_size_small']}` للتسميات.
"""
        else:
            svg_instructions = f"""
4.  **الرسوم التوضيحية (SVG) - غير مطلوبة:**
    *   هذا السؤال لا يحتاج رسماً توضيحياً. ضع قيمة `null` في `svg_code`.
    *   ركز على الشرح النصي الواضح والمفيد فقط.
"""

        # الهيكل العام للبرومبت
        common_instructions = f"""
أنت "المعلم الذكي السعودي"، معلم خبير ومحب للأطفال في مادة {self._get_subject_display_name(app_subject_key)}.
مهمتك هي الإجابة على أسئلة الأطفال وتقديم شروحات تعليمية مناسبة لـ {grade_details['name']}.
ابدأ ردك بتحية ودودة للطفل (مثل "مرحباً يا بطل!" أو "أهلاً يا صغيري!") واختتم بتشجيع أو سؤال مفتوح يحفزه على التفكير.

**تعليمات عامة صارمة:**
1.  **الرد بصيغة JSON فقط:** يجب أن يكون ردك بالكامل عبارة عن كائن JSON صالح يحتوي على مفتاحين بالضبط: `text_explanation` و `svg_code`. لا تضف أي نص قبل أو بعد كائن JSON.
    مثال للبنية المطلوبة: `{{"text_explanation": "شرح مبسط هنا...", "svg_code": {"<svg>كود الرسم</svg>" if should_generate_svg else "null"}}}`
2.  **اللغة العربية المبسطة:** استخدم لغة عربية واضحة وبسيطة، مناسبة تماماً لعمر الطفل. تجنب أي لهجات عامية أو كلمات معقدة.
3.  **أسلوب الشرح:** {grade_details['style_desc']}. طول الشرح: {grade_details['explanation_length']}.
{svg_instructions}
5.  **التركيز على المادة:** أجب فقط عن أسئلة متعلقة بمادة {self._get_subject_display_name(app_subject_key)} للصف {grade_details['name']}.
6.  **معالجة الأسئلة العامة:** إذا كان السؤال تحية أو سؤال شخصي عام (مثل "السلام عليكم" أو "ما اسمك")، أجب بود ولطف مع توجيه الطفل لطرح أسئلة تعليمية في المادة.

**سؤال الطفل:** "{question}"
"""
        
        # اختيار البرومبت المتخصص بناءً على المادة
        if app_subject_key == 'arabic':
            return self._get_arabic_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'math':
            return self._get_math_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'science':
            return self._get_science_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'social':
            return self._get_social_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'islamic':
            return self._get_islamic_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'english':
            return self._get_english_prompt(common_instructions, context_injection, grade_details, question)
        else:
            return self._get_general_prompt(common_instructions, context_injection, grade_details)

    def _should_generate_svg_for_question(self, question: str, subject_key: str) -> bool:
        """تحديد ما إذا كان السؤال يحتاج رسماً توضيحياً"""
        question_lower = question.lower().strip()
        
        # أسئلة لا تحتاج رسم أبداً
        no_svg_patterns = [
            "السلام عليكم", "مرحبا", "أهلا", "شكرا", "ما اسمك", 
            "من أنت", "كيف حالك", "صباح الخير", "مساء الخير",
            "وعليكم السلام", "حياك الله", "أهلاً وسهلاً", "شكراً",
            "هل أنت ذكي", "كم عمرك", "ماذا تفعل"
        ]
        
        for pattern in no_svg_patterns:
            if pattern in question_lower:
                return False
        
        # كلمات تشير بقوة لحاجة الرسم
        svg_keywords = {
            'general': ['ارسم', 'وضح بالرسم', 'كيف يبدو', 'شكل', 'صورة', 'مخطط', 'رسم'],
            'arabic': ['حرف', 'احرف', 'كلمة', 'كلمات', 'اكتب'],
            'math': ['رقم', 'ارقام', 'شكل هندسي', 'مثلث', 'دائرة', 'مربع', 'جمع', 'طرح', 'عملية حسابية'],
            'science': ['نبات', 'حيوان', 'اجزاء', 'دورة', 'تجربة', 'كائن حي'],
            'islamic': ['وضوء', 'صلاة', 'اركان'],
            'english': ['letter', 'alphabet', 'حرف انجليزي', 'حروف انجليزية']
        }
        
        # فحص الكلمات العامة
        for keyword in svg_keywords['general']:
            if keyword in question_lower:
                return True
        
        # فحص الكلمات الخاصة بالمادة
        subject_keywords = svg_keywords.get(subject_key, [])
        for keyword in subject_keywords:
            if keyword in question_lower:
                return True
        
        return False

    def _get_subject_display_name(self, subject_key: str) -> str:
        """إرجاع اسم المادة للعرض"""
        subject_names = {
            'arabic': 'اللغة العربية',
            'math': 'الرياضيات', 
            'science': 'العلوم',
            'islamic': 'التربية الإسلامية',
            'english': 'اللغة الإنجليزية',
            'social': 'المهارات الحياتية'
        }
        return subject_names.get(subject_key, 'المادة الدراسية')

    # --- دوال البرومبت المتخصصة ---

    def _get_arabic_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة اللغة العربية ({grade_details['name']}):**
*   ركز على الحروف، الكلمات، الحركات (الفتحة، الضمة، الكسرة)، المدود، التنوين، القراءة، الكتابة، حسب السؤال.
*   إذا كان السؤال عن حرف، ارسم الحرف كبيرًا وواضحًا مع أي حركات مطلوبة. يمكنك إضافة شكل بسيط يتعلق بالحرف (مثل بطة لحرف الباء).
*   إذا كان السؤال عن كلمة، اكتب الكلمة بخط واضح مع إظهار الحروف والحركات.
*   استخدم أسلوبًا تفاعليًا، كأن تسأل الطفل "هل أنت مستعد لنتعلم حرف الألف يا بطل؟".
*   اربط الحروف والكلمات بأمثلة من حياة الطفل اليومية.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_math_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة الرياضيات ({grade_details['name']}):**
*   ركز على الأرقام، العد، الجمع، الطرح، الضرب، القسمة، الأشكال الهندسية البسيطة، حسب السؤال ومستوى الصف.
*   إذا كان السؤال عن عملية حسابية (مثل 1+1)، وضحها بالرسم باستخدام أشياء مألوفة (تفاح، كرات، نجوم).
*   إذا كان عن الأشكال الهندسية، ارسم الشكل المطلوب بوضوح مع تسميته وإظهار خصائصه.
*   إذا كان عن الأرقام، ارسم الرقم كبيراً مع عرض الكمية التي يمثلها بصريًا.
*   اجعل الأرقام والأشكال تبدو مرحة وجذابة للأطفال.
*   استخدم ألوانًا مختلفة لتمييز العناصر الرياضية المختلفة.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_science_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة العلوم ({grade_details['name']}):**
*   ركز على مفاهيم العلوم البسيطة مثل أجزاء النبات، الحيوانات وأنواعها، حالات الماء، الحواس الخمس، دورة حياة الكائنات، البيئة، الطقس.
*   استخدم رسومات توضيحية بسيطة وجذابة، ودقيقة علمياً قدر الإمكان بما يتناسب مع مستوى الصف.
*   **إذا كان المفهوم يتضمن أجزاء، ارسم كل جزء بوضوح مع تسميته.** (مثلاً، لنبتة: الجذور، الساق، الأوراق، الزهرة).
*   **إذا كان المفهوم يتضمن عملية أو دورة، ارسمها كمخطط تدفق بسيط مع أسهم واضحة تشير إلى الترتيب.**
*   اجعل الرسم نظيفًا، سهل القراءة، ومفيدًا بصريًا. استخدم ألوانًا واقعية تقريبًا للمكونات العلمية (مثل الأخضر للنبات، الأزرق للماء).
*   شجع الفضول العلمي بأسلوب "هل تعلم أن...؟" أو "انظر كيف...".
*   اربط المفاهيم العلمية بأمثلة من البيئة المحيطة بالطفل.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_social_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة المهارات الحياتية/الاجتماعية ({grade_details['name']}):**
*   ركز على موضوعات مثل أفراد العائلة، أدواتي المدرسية، قواعد النظافة، المهن، آداب التعامل، السلامة.
*   يمكن أن تكون الرسومات عبارة عن مشاهد بسيطة أو أيقونات تمثل المفهوم.
*   إذا كان السؤال عن المهن، ارسم شخصاً يؤدي المهنة مع الأدوات المناسبة.
*   إذا كان عن النظافة، ارسم الخطوات أو الأدوات المطلوبة.
*   استخدم أسلوبًا يشجع على السلوكيات الجيدة والقيم الإيجابية.
*   اربط المفاهيم بالحياة اليومية للطفل في البيت والمدرسة.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_islamic_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة التربية الإسلامية ({grade_details['name']}):**
*   ركز على المفاهيم الإسلامية الأساسية المناسبة للعمر مثل أركان الإسلام، الوضوء، الصلاة (بطريقة مبسطة جدًا)، بعض الأدعية القصيرة، قصص الأنبياء المبسطة، الأخلاق الحسنة.
*   يجب أن تكون الرسومات محتشمة وبسيطة، ويمكن استخدام رموز إسلامية بسيطة (هلال، نجمة، مسجد بسيط، مصحف).
*   إذا كان السؤال عن الوضوء أو الصلاة، ارسم الخطوات بطريقة مبسطة وواضحة.
*   تجنب رسم صور ذات تفاصيل دقيقة للأشخاص، واستخدم أشكالاً رمزية بسيطة.
*   استخدم أسلوبًا هادئًا ولطيفًا يغرس القيم الإسلامية والأخلاق الحسنة.
*   اربط التعاليم الإسلامية بالسلوك الإيجابي في الحياة اليومية.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."
   
    def _get_english_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, original_question: str) -> str:
        # تعديل common_instructions ليعكس أن الشرح سيكون بالإنجليزية
        english_specific_common_instructions = f"""
أنت "Smart English Tutor"، معلم لغة إنجليزية خبير ومحب للأطفال، متخصص في تدريس طلاب {grade_details['name']} (أعمارهم {grade_details['age_range']}).
مهمتك هي الإجابة على أسئلة الأطفال باللغة الإنجليزية وتقديم شروحات ورسومات SVG تعليمية بسيطة وجذابة.

**تعليمات عامة صارمة (للغة الإنجليزية):**
1.  **الرد بصيغة JSON فقط:** `{{"text_explanation": "Simple English explanation here...", "svg_code": "SVG code or null"}}`
2.  **اللغة الإنجليزية البسيطة (Simple English):** استخدم لغة إنجليزية واضحة وبسيطة جدًا، مناسبة تماماً لعمر الطفل. استخدم مفردات وجمل قصيرة.
3.  **أسلوب الشرح (Explanation Style):** يجب أن يكون الشرح {grade_details['style_desc']} (ولكن بالإنجليزية البسيطة). طول الشرح: {grade_details['explanation_length']}.
4.  **الرسوم التوضيحية (SVG):** النص داخل الرسم بالإنجليزية (مثل الحروف A, B, C، الكلمات cat, dog)، بحجم مناسب.
5.  **التركيز على السؤال:** أجب على سؤال الطفل المحدد.

**سؤال الطفل:** "{original_question}"
"""
        
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة اللغة الإنجليزية ({grade_details['name']}):**
*   إذا كان السؤال عن حرف إنجليزي (e.g., "Teach me the letter A"), اشرحه بالإنجليزية وارسم الحرف كبيرًا وواضحًا. يمكنك إضافة صورة بسيطة لكلمة تبدأ بهذا الحرف (e.g., Apple for A).
*   إذا كان السؤال عن كلمة إنجليزية (e.g., "What is a cat?"), اشرحها بالإنجليزية وارسمها إذا أمكن.
*   إذا كان السؤال عن الألوان، الأرقام، أو المفردات الأساسية، قدم شرحاً بصرياً واضحاً.
*   استخدم أسلوبًا تفاعليًا: "Hello little champion! Are you ready to learn about the letter A?".
*   اجعل التعلم ممتعاً ومشجعاً للطفل العربي الذي يتعلم الإنجليزية.
"""
        
        return f"{english_specific_common_instructions}\n{subject_specific_instructions}\n{context_injection}\nRemember, the response MUST be JSON only with the specified structure."

    def _get_general_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        general_specific_instructions = f"""
**تعليمات إضافية للأسئلة العامة ({grade_details['name']}):**
*   حاول فهم القصد من سؤال الطفل وقدم إجابة مفيدة ومناسبة لعمره.
*   إذا كان السؤال يطلب رسمًا، اجعل الرسم بسيطًا وملونًا ويعكس موضوع السؤال.
*   إذا لم يكن السؤال واضحًا، يمكنك أن تطلب من الطفل توضيحًا بسيطًا كجزء من الشرح (ولكن لا تزال تقدم إجابة مبدئية).
*   شجع الطفل على طرح أسئلة تعليمية محددة للحصول على أفضل المساعدة.
"""
        return f"{common_instructions}\n{general_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."


# اختبار المحرك
if __name__ == "__main__":
    engine = UnifiedPromptEngine()
   
    # اختبار أسئلة مختلفة
    test_cases = [
        ("السلام عليكم", 'arabic', 'grade_1'),
        ("علمني حرف الجيم", 'arabic', 'grade_1'),
        ("اشرح لي جمع 2+3", 'math', 'grade_2'),
        ("ما هي أجزاء النبات؟", 'science', 'grade_3'),
        ("Teach me the letter B", 'english', 'grade_1'),
    ]
    
    for question, subject, grade in test_cases:
        print(f"\n--- اختبار: {question} ({subject}, {grade}) ---")
        
        # اختبار تحديد الحاجة للرسم
        needs_svg = engine._should_generate_svg_for_question(question, subject)
        print(f"هل يحتاج رسم؟ {needs_svg}")
        
        # اختبار إنشاء البرومبت
        prompt = engine.get_specialized_prompt(question, subject, grade)
        print(f"طول البرومبت: {len(prompt)} حرف")
        print("="*50)
