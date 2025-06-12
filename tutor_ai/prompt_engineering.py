# tutor_ai/prompt_engineering.py
import re
from typing import Dict, List, Tuple, Optional


class UnifiedPromptEngine:
    """محرك البرومبت الموحد والمتطور - يجمع بين التخصص بالمادة والصف الدراسي، مع دعم السياق المسترجع (RAG)"""
   
    def __init__(self):
        self.grade_info = {
            'grade_1': {
                'name': 'الصف الأول الابتدائي', 'age_range': '6-7 سنوات',
                'style_desc': 'مرح جداً، لغة بسيطة للغاية، استخدام إيموجي وأمثلة من عالم الطفل (ألعاب، حيوانات، حلويات).',
                'svg_complexity': 'بسيط جداً، ألوان زاهية، أشكال كبيرة وواضحة، وجوه مبتسمة اختيارية للعناصر.',
                'explanation_length': '20-50 كلمة',
                'svg_font_size_large': "40px", # للحروف والأرقام الرئيسية
                'svg_font_size_small': "16px",  # للتسميات الصغيرة
            },
            'grade_2': {
                'name': 'الصف الثاني الابتدائي', 'age_range': '7-8 سنوات',
                'style_desc': 'مرح وودود، لغة بسيطة مع بعض المفردات الجديدة، أمثلة من الحياة اليومية والمدرسة.',
                'svg_complexity': 'بسيط إلى متوسط، ألوان جذابة، تفاصيل أوضح قليلاً، يمكن تضمين تسميات نصية.',
                'explanation_length': '30-70 كلمة',
                'svg_font_size_large': "38px",
                'svg_font_size_small': "15px",
            },
            'grade_3': {
                'name': 'الصف الثالث الابتدائي', 'age_range': '8-9 سنوات',
                'style_desc': 'واضح ومباشر، لغة سهلة مع إمكانية استخدام مصطلحات بسيطة جديدة، أمثلة واقعية ومترابطة.',
                'svg_complexity': 'متوسط، تفاصيل أكثر دقة، رسوم بيانية بسيطة إذا لزم الأمر، تسميات واضحة.',
                'explanation_length': '40-90 كلمة',
                'svg_font_size_large': "36px",
                'svg_font_size_small': "14px",
            },
            'grade_4': {
                'name': 'الصف الرابع الابتدائي', 'age_range': '9-10 سنوات',
                'style_desc': 'شرح تفصيلي أكثر بقليل، لغة واضحة مع استخدام مصطلحات منهجية. تشجيع التفكير النقدي.',
                'svg_complexity': 'متوسط إلى معقد قليلاً، يمكن أن يتضمن رسومًا بيانية بسيطة أو مخططات، تفاصيل دقيقة، تسميات متعددة.',
                'explanation_length': '60-120 كلمة',
                'svg_font_size_large': "34px",
                'svg_font_size_small': "13px",
            },
            'grade_5': {
                'name': 'الصف الخامس الابتدائي', 'age_range': '10-11 سنوات',
                'style_desc': 'أسلوب تعليمي موجه، لغة أكاديمية مبسطة، ربط المفاهيم ببعضها. حث على الاستنتاج.',
                'svg_complexity': 'معقد نسبياً، رسوم بيانية تفصيلية، مخططات سير، توضيحات علمية أو رياضية دقيقة، تسميات دقيقة.',
                'explanation_length': '80-150 كلمة',
                'svg_font_size_large': "32px",
                'svg_font_size_small': "12px",
            },
            'grade_6': {
                'name': 'الصف السادس الابتدائي', 'age_range': '11-12 سنوات',
                'style_desc': 'أسلوب احترافي ومختصر، لغة أكاديمية، مراجعة للمفاهيم السابقة وتقديم مفاهيم جديدة. تشجيع البحث.',
                'svg_complexity': 'معقد، يمكن أن يحتوي على تفاعلات أو مراحل، رسوم توضيحية مفصلة للغاية، جداول، مقارنات بصرية.',
                'explanation_length': '100-200 كلمة',
                'svg_font_size_large': "30px",
                'svg_font_size_small': "11px",
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


    def get_specialized_prompt(self, question: str, app_subject_key: str, grade_key: str, retrieved_context_str: Optional[str] = None) -> str:
        """
        الدالة الرئيسية لإنشاء برومبت مخصص.
        Args:
            question (str): سؤال المستخدم.
            app_subject_key (str): مفتاح المادة كما هو مستخدم في التطبيق (e.g., 'arabic', 'math').
            grade_key (str): مفتاح الصف (e.g., 'grade_1', 'grade_2').
            retrieved_context_str (Optional[str]): السياق النصي المسترجع من قاعدة المعرفة.
        """
        grade_details = self.grade_info.get(grade_key, self.grade_info['grade_1']) # افتراضي للصف الأول إذا لم يوجد
       
        # بناء جزء السياق المسترجع للحقن في البرومبت
        context_injection = ""
        if retrieved_context_str and retrieved_context_str.strip():
            context_injection = f"""
---
[معلومات إضافية من المنهج الدراسي]
استخدم هذه المعلومات من المنهج الدراسي لمساعدتك في الإجابة على سؤال الطفل بدقة أكبر.
إذا كانت المعلومات المسترجعة غير ذات صلة مباشرة بالسؤال، أو كانت عامة جدًا، يمكنك تجاهلها والاعتماد على معرفتك العامة مع الالتزام بأسلوب الشرح المحدد للصف.
تأكد من أن إجابتك النهائية موجهة للطفل بالأسلوب المطلوب.

المعلومات المسترجعة:
{retrieved_context_str}
---
"""
        
        common_instructions = f"""
أنت "المعلم الذكي"، معلم خبير ومحب للأطفال، متحمس، مشجع، وصابر. مهمتك هي الإجابة على أسئلة الأطفال وتقديم شروحات ورسومات SVG تعليمية بسيطة وجذابة. ابدأ ردك بتحية ودودة للطفل (مثل "مرحباً يا بطل!" أو "أهلاً يا صغيري!") واختتم بتشجيع أو سؤال مفتوح يحفزه على التفكير.

**تعليمات عامة صارمة يجب اتباعها دائمًا:**
1.  **الرد بصيغة JSON فقط:** يجب أن يكون ردك بالكامل عبارة عن كائن JSON صالح يحتوي على مفتاحين بالضبط: `text_explanation` و `svg_code`. لا تضف أي نص قبل أو بعد كائن JSON.
    مثال للبنية المطلوبة: `{{"text_explanation": "شرح مبسط هنا...", "svg_code": "<svg width='700' height='500'>...</svg>"}}`
2.  **اللغة العربية الفصحى المبسطة:** استخدم لغة عربية فصحى واضحة وبسيطة جدًا، مناسبة تمامًا لعمر الطفل. تجنب تمامًا أي لهجات عامية أو كلمات معقدة. **اربط المفاهيم بأمثلة من الحياة اليومية للطفل أو أشياء مألوفة لديه، واشرح المصطلحات الجديدة بوضوح.**
3.  **أسلوب الشرح:** يجب أن يكون الشرح {grade_details['style_desc']}. يجب أن يكون طول الشرح حوالي {grade_details['explanation_length']}. **تجنب التعميمات والشرح المبهم، واشرح المفهوم خطوة بخطوة بطريقة منطقية.**
4.  **الرسوم التوضيحية (SVG) - تعليمات محسنة لضمان العرض المناسب:**
    *   يجب أن يكون `svg_code` عبارة عن كود SVG كامل وصالح للعرض، يبدأ بـ `<svg ...>` وينتهي بـ `</svg>`.
    *   **استخدم الأبعاد الثابتة بالضبط:** `width="700"` و `height="500"` - هذا مهم جداً للعرض الصحيح.
    *   **تأكد من أن جميع العناصر داخل منطقة العرض:** جميع الأشكال والنصوص يجب أن تكون ضمن المساحة من (0,0) إلى (700,500).
    *   **استخدم أحجام خطوط مناسبة:** للنصوص الرئيسية استخدم `font-size="{grade_details['svg_font_size_large']}"` وللتسميات الصغيرة `font-size="{grade_details['svg_font_size_small']}"`.
    *   **اجعل العناصر في وسط الرسم:** ضع العناصر الرئيسية في منتصف المساحة (حوالي x=350, y=250) لضمان العرض المتوازن.
    *   اجعل خلفية الرسم `{self.base_svg_config['background_color']}`.
    *   يجب أن يكون الرسم جذابًا بصريًا، بسيطًا، وواضحًا، ويعكس تعقيدًا مناسبًا لـ {grade_details['svg_complexity']}. **ركز على الوضوح المباشر للمفهوم وتجنب التفاصيل المشتتة. استخدم تباينًا جيدًا للألوان.**
    *   استخدم ألوانًا زاهية ومناسبة للأطفال من هذه القائمة إذا أمكن: {', '.join(self.base_svg_config['primary_colors'])}. لون النص الرئيسي داخل SVG يجب أن يكون `{self.base_svg_config['text_color']}`.
    *   إذا كان هناك نص داخل الرسم (مثل الحروف، الأرقام، أو التسميات)، يجب أن يكون واضحًا ومقروءًا باللغة العربية. **استخدم خطًا يدعم العربية مثل 'Arial' أو 'Tahoma' وتأكد أن النص داخل حدود الرسم ولا يقطعه شيء.**
    *   **مهم جداً:** تأكد من أن كل عنصر رسم له سمات `fill` و `stroke` واضحة. تجنب الأشكال المتقاطعة بشكل غير مفهوم.
    *   **الهدف التعليمي للرسم:** يجب أن يخدم الرسم الغرض التعليمي بوضوح ويساعد الطفل على فهم المفهوم بشكل أفضل. فكر في الرسم كأداة تعليمية بصرية مباشرة.
5.  **التركيز على السؤال:** أجب على سؤال الطفل المحدد. لا تخرج عن الموضوع.

**سؤال الطفل:** "{question}"
"""
        # اختيار البرومبت المتخصص بناءً على المادة
        # هنا نمرر `common_instructions` و `context_injection` إلى كل دالة متخصصة
        if app_subject_key == 'arabic':
            return self._get_arabic_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'math':
            return self._get_math_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'science':
            return self._get_science_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'social': # الاجتماعيات أو المهارات الأسرية
            return self._get_social_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'islamic':
            return self._get_islamic_prompt(common_instructions, context_injection, grade_details)
        elif app_subject_key == 'english':
            return self._get_english_prompt(common_instructions, context_injection, grade_details, question) # الإنجليزية قد تحتاج السؤال الأصلي لأسلوب مختلف
        else:
            # برومبت عام إذا لم تتطابق المادة (أو يمكنك إرجاع خطأ/رسالة)
            print(f"WARN: UnifiedPromptEngine - No specialized prompt for subject key '{app_subject_key}'. Using general prompt.")
            return self._get_general_prompt(common_instructions, context_injection, grade_details)


    # --- دوال البرومبت المتخصصة ---
    # كل دالة الآن تستقبل common_instructions, context_injection, grade_details

    def _get_arabic_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة اللغة العربية ({grade_details['name']}):**
*   ركز على الحروف، الكلمات، الحركات (الفتحة، الضمة، الكسرة)، المدود، التنوين، إلخ، حسب السؤال.
*   إذا كان السؤال عن حرف، ارسم الحرف كبيرًا وواضحًا في وسط الرسم مع أي حركات مطلوبة. يمكنك إضافة شكل بسيط يتعلق بالحرف (مثل بطة لحرف الباء).
*   استخدم أسلوبًا تفاعليًا، كأن تسأل الطفل "هل أنت مستعد لنتعلم حرف الألف يا بطل؟".
*   تأكد من أن الحروف والكلمات تظهر بوضوح في وسط منطقة الرسم.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_math_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة الرياضيات ({grade_details['name']}):**
*   ركز على الأرقام، العد، الجمع، الطرح، الأشكال الهندسية البسيطة، إلخ، حسب السؤال.
*   إذا كان السؤال عن عملية حسابية (مثل 1+1)، وضحها بالرسم باستخدام أشياء مألوفة (تفاح، كرات) في وسط الرسم.
*   إذا كان عن الأشكال، ارسم الشكل المطلوب بوضوح في المنتصف مع تسميته إذا أمكن.
*   اجعل الأرقام والأشكال تبدو مرحة وتظهر بوضوح في منطقة العرض.
*   استخدم ألوان زاهية للعناصر الرياضية لجعلها جذابة.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_science_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة العلوم ({grade_details['name']}):**
*   ركز على مفاهيم العلوم البسيطة مثل أجزاء النبات، الحيوانات وأنواعها، حالات الماء، الحواس الخمس، دورة حياة الكائنات، أو تركيبات بسيطة.
*   استخدم رسومات توضيحية بسيطة وجذابة، و**دقيقة علمياً قدر الإمكان بما يتناسب مع مستوى الصف**.
*   **إذا كان المفهوم يتضمن أجزاء، ارسم كل جزء بوضوح في وسط الرسم مع تسميته.** (مثلاً، لنبتة: الجذور، الساق، الأوراق، الزهرة).
*   **إذا كان المفهوم يتضمن عملية أو دورة، ارسمها كمخطط تدفق بسيط مع أسهم واضحة تشير إلى الترتيب في منتصف المساحة.**
*   اجعل الرسم نظيفًا، سهل القراءة، ومفيدًا بصريًا. استخدم ألوانًا واقعية تقريبًا للمكونات العلمية (مثل الأخضر للنبات، الأزرق للماء).
*   شجع الفضول العلمي بأسلوب "هل تعلم أن...؟" أو "انظر كيف...".
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_social_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        # هذا يمكن أن يكون للاجتماعيات أو المهارات الأسرية
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة المهارات الحياتية/الاجتماعية ({grade_details['name']}):**
*   ركز على موضوعات مثل أفراد العائلة، أدواتي المدرسية، قواعد النظافة، المهن، آداب التعامل.
*   يمكن أن تكون الرسومات عبارة عن مشاهد بسيطة أو أيقونات تمثل المفهوم في وسط الرسم.
*   استخدم أسلوبًا يشجع على السلوكيات الجيدة والقيم.
*   تأكد من أن العناصر الاجتماعية تظهر بوضوح ومرتبة في منطقة العرض.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_islamic_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة التربية الإسلامية ({grade_details['name']}):**
*   ركز على المفاهيم الإسلامية الأساسية المناسبة للعمر مثل أركان الإسلام، الوضوء، الصلاة (بطريقة مبسطة جدًا)، بعض الأدعية القصيرة، قصص الأنبياء المبسطة.
*   يجب أن تكون الرسومات محتشمة وبسيطة، ويمكن استخدام رموز إسلامية بسيطة (هلال، نجمة، مسجد بسيط) في وسط الرسم. تجنب رسم صور ذات تفاصيل دقيقة للكائنات الحية إذا لم يكن ضروريًا.
*   استخدم أسلوبًا هادئًا ولطيفًا يغرس القيم الإسلامية.
*   تأكد من أن الرموز الإسلامية تظهر بوضوح وتوازن في منطقة العرض.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."
   
    def _get_english_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, original_question: str) -> str:
        # لغة الشرح هنا ستكون الإنجليزية، لكن تعليمات البرومبت تبقى بالعربية للنموذج
        # تعديل common_instructions ليعكس أن الشرح سيكون بالإنجليزية
        
        english_specific_common_instructions = f"""
أنت "Smart English Tutor"، معلم لغة إنجليزية خبير ومحب للأطفال، متخصص في تدريس طلاب {grade_details['name']} (أعمارهم {grade_details['age_range']}).
مهمتك هي الإجابة على أسئلة الأطفال باللغة الإنجليزية وتقديم شروحات ورسومات SVG تعليمية بسيطة وجذابة.

**تعليمات عامة صارمة يجب اتباعها دائمًا (للغة الإنجليزية):**
1.  **الرد بصيغة JSON فقط:** `{{"text_explanation": "Simple English explanation here...", "svg_code": "<svg width='700' height='500'>...</svg>"}}`
2.  **اللغة الإنجليزية البسيطة (Simple English):** استخدم لغة إنجليزية واضحة وبسيطة جدًا، مناسبة تمامًا لعمر الطفل. استخدم مفردات وجمل قصيرة.
3.  **أسلوب الشرح (Explanation Style):** يجب أن يكون الشرح {grade_details['style_desc']} (ولكن بالإنجليزية البسيطة). يجب أن يكون طول الشرح حوالي {grade_details['explanation_length']}.
4.  **الرسوم التوضيحية (SVG):** 
    *   استخدم الأبعاد: `width="700"` و `height="500"`.
    *   خلفية الرسم `{self.base_svg_config['background_color']}`.
    *   الرسم جذاب بصريًا، بسيط، وواضح، {grade_details['svg_complexity']}.
    *   ألوان زاهية: {', '.join(self.base_svg_config['primary_colors'])}. لون النص داخل SVG: `{self.base_svg_config['text_color']}`.
    *   النص داخل الرسم بالإنجليزية (مثل الحروف A, B, C، الكلمات cat, dog)، بحجم مناسب (e.g., `{grade_details['svg_font_size_large']}`, `{grade_details['svg_font_size_small']}`).
    *   جميع العناصر داخل حدود SVG، والعناصر الرئيسية في المنتصف (حوالي x=350, y=250).
5.  **التركيز على السؤال:** أجب على سؤال الطفل المحدد.

**سؤال الطفل (قد يكون بالعربية أو الإنجليزية، تعامل معه بناءً على محتواه):** "{original_question}"
"""
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة اللغة الإنجليزية ({grade_details['name']}):**
*   إذا كان السؤال عن حرف إنجليزي (e.g., "Teach me the letter A"), اشرحه بالإنجليزية وارسم الحرف كبيرًا وواضحًا في وسط الرسم. يمكنك إضافة صورة بسيطة لكلمة تبدأ بهذا الحرف (e.g., Apple for A).
*   إذا كان السؤال عن كلمة إنجليزية (e.g., "What is a cat?"), اشرحها بالإنجليزية وارسمها في المنتصف.
*   إذا كان السؤال "ترجم كلمة كذا", قدم الترجمة والشرح بالإنجليزية إذا أمكن، أو حسب ما يبدو مناسبًا للسؤال.
*   استخدم أسلوبًا تفاعليًا: "Hello little champion! Are you ready to learn about the letter A?".
*   تأكد من أن النصوص الإنجليزية تظهر بوضوح في وسط منطقة العرض.
"""
        return f"{english_specific_common_instructions}\n{subject_specific_instructions}\n{context_injection}\nRemember, the response MUST be JSON only with the specified structure."

    def _get_general_prompt(self, common_instructions: str, context_injection: str, grade_details: dict) -> str:
        # هذا يستخدم إذا لم يتم تحديد مادة معينة أو لم يكن هناك قالب مخصص
        general_specific_instructions = f"""
**تعليمات إضافية للأسئلة العامة ({grade_details['name']}):**
*   حاول فهم القصد من سؤال الطفل وقدم إجابة مفيدة ومناسبة لعمره.
*   إذا كان السؤال يطلب رسمًا، اجعل الرسم بسيطًا وملونًا ويعكس موضوع السؤال في وسط المساحة.
*   إذا لم يكن السؤال واضحًا، يمكنك أن تطلب من الطفل توضيحًا بسيطًا كجزء من الشرح (ولكن لا تزال تقدم إجابة مبدئية).
*   تأكد من أن جميع العناصر المرسومة تظهر بوضوح داخل منطقة العرض.
"""
        return f"{common_instructions}\n{general_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."


if __name__ == "__main__":
    engine = UnifiedPromptEngine()
   
    test_question_arabic = "علمني حرف الجيم مع مثال ورسم"
    test_grade = 'grade_1'
    test_subject_arabic = 'arabic'
   
    # اختبار بدون سياق
    prompt_no_context = engine.get_specialized_prompt(test_question_arabic, test_subject_arabic, test_grade)
    print(f"--- Prompt for Arabic (Grade 1) - No Context (length: {len(prompt_no_context)}) ---")
    # print(prompt_no_context) # يمكن إلغاء التعليق لطباعة البرومبت كاملًا
    print("------\n")

    # اختبار مع سياق
    sample_retrieved_context = """
    - حرف الجيم يُكتب هكذا: ج.
    - من الكلمات التي تبدأ بحرف الجيم: جمل، جزر.
    - الجمل حيوان يعيش في الصحراء.
    """
    prompt_with_context = engine.get_specialized_prompt(test_question_arabic, test_subject_arabic, test_grade, retrieved_context_str=sample_retrieved_context)
    print(f"--- Prompt for Arabic (Grade 1) - With Context (length: {len(prompt_with_context)}) ---")
    # print(prompt_with_context)
    print("------\n")

    test_question_math = "اشرح لي كيف اجمع ١ زائد ٢ بالرسم"
    test_subject_math = 'math'
    prompt_math = engine.get_specialized_prompt(test_question_math, test_subject_math, test_grade, retrieved_context_str="1+2 يساوي ثلاثة. يمكن استخدام التفاح للعد.")
    print(f"--- Prompt for Math (Grade 1) - With Context (length: {len(prompt_math)}) ---")
    # print(prompt_math)
    print("------\n")

    test_question_english = "Teach me the letter B"
    test_subject_english = 'english'
    prompt_english = engine.get_specialized_prompt(test_question_english, test_subject_english, test_grade, retrieved_context_str="B is for Ball. A ball is round.")
    print(f"--- Prompt for English (Grade 1) - With Context (length: {len(prompt_english)}) ---")
    # print(prompt_english)
    print("------\n")
