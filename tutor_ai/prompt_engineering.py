# tutor_ai/prompt_engineering.py
import re
from typing import Dict, List, Tuple, Optional

class UnifiedPromptEngine:
    """محرك البرومبت الموحد والمتطور - يجمع بين التخصص بالمادة والصف الدراسي، مع دعم السياق المسترجع (RAG)"""
   
    def __init__(self):
        self.grade_info = {
            'grade_1': {'name': 'الصف الأول الابتدائي', 'age_range': '6-7 سنوات', 'style_desc': 'مرح جداً، لغة بسيطة للغاية، استخدام إيموجي وأمثلة من عالم الطفل (ألعاب، حيوانات، حلويات).', 'svg_complexity': 'بسيط جداً، ألوان زاهية، أشكال كبيرة وواضحة، وجوه مبتسمة اختيارية للعناصر.', 'explanation_length': '20-50 كلمة', 'svg_font_size_large': "100px", 'svg_font_size_small': "20px"},
            'grade_2': {'name': 'الصف الثاني الابتدائي', 'age_range': '7-8 سنوات', 'style_desc': 'مرح وودود، لغة بسيطة مع بعض المفردات الجديدة، أمثلة من الحياة اليومية والمدرسة.', 'svg_complexity': 'بسيط إلى متوسط، ألوان جذابة، تفاصيل أوضح قليلاً، يمكن تضمين تسميات نصية.', 'explanation_length': '30-70 كلمة', 'svg_font_size_large': "90px", 'svg_font_size_small': "18px"},
            'grade_3': {'name': 'الصف الثالث الابتدائي', 'age_range': '8-9 سنوات', 'style_desc': 'واضح ومباشر، لغة سهلة مع إمكانية استخدام مصطلحات بسيطة جديدة، أمثلة واقعية ومترابطة.', 'svg_complexity': 'متوسط، تفاصيل أكثر دقة، رسوم بيانية بسيطة إذا لزم الأمر، تسميات واضحة.', 'explanation_length': '40-90 كلمة', 'svg_font_size_large': "80px", 'svg_font_size_small': "16px"},
            'grade_4': {'name': 'الصف الرابع الابتدائي', 'age_range': '9-10 سنوات', 'style_desc': 'شرح تفصيلي أكثر بقليل، لغة واضحة مع استخدام مصطلحات منهجية. تشجيع التفكير النقدي.', 'svg_complexity': 'متوسط إلى معقد قليلاً، يمكن أن يتضمن رسومًا بيانية بسيطة أو مخططات، تفاصيل دقيقة، تسميات متعددة.', 'explanation_length': '60-120 كلمة', 'svg_font_size_large': "70px", 'svg_font_size_small': "14px"},
            'grade_5': {'name': 'الصف الخامس الابتدائي', 'age_range': '10-11 سنوات', 'style_desc': 'أسلوب تعليمي موجه، لغة أكاديمية مبسطة، ربط المفاهيم ببعضها. حث على الاستنتاج.', 'svg_complexity': 'معقد نسبياً، رسوم بيانية تفصيلية، مخططات سير، توضيحات علمية أو رياضية دقيقة، تسميات دقيقة.', 'explanation_length': '80-150 كلمة', 'svg_font_size_large': "60px", 'svg_font_size_small': "12px"},
            'grade_6': {'name': 'الصف السادس الابتدائي', 'age_range': '11-12 سنوات', 'style_desc': 'أسلوب احترافي ومختصر، لغة أكاديمية، مراجعة للمفاهيم السابقة وتقديم مفاهيم جديدة. تشجيع البحث.', 'svg_complexity': 'معقد، يمكن أن يحتوي على تفاعلات أو مراحل، رسوم توضيحية مفصلة للغاية، جداول، مقارنات بصرية.', 'explanation_length': '100-200 كلمة', 'svg_font_size_large': "50px", 'svg_font_size_small': "10px"}
        }
        self.base_svg_config = {
            'width': 700, 'height': 500, 'background_color': 'white', 
            'default_stroke_color': '#333333', 
            'primary_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FED766', '#2AB7CA'], 
            'text_color': '#2C3E50'
        }

    def get_specialized_prompt(self, question: str, app_subject_key: str, grade_key: str, 
                               retrieved_context_str: Optional[str] = None,
                               search_status: Optional[str] = None) -> str:
        grade_details = self.grade_info.get(grade_key, self.grade_info['grade_1'])
        
        # تحديد اسم المادة للعرض في البرومبت (للتوضيح فقط، ليس له تأثير مباشر على منطق RAG)
        # هذا يفترض أن GRADE_SUBJECTS متاح هنا أو يتم تمريره
        # للتبسيط، لن نستخدمه مباشرة في context_injection الآن، ولكن يمكن إضافته
        # subject_display_name = GRADE_SUBJECTS.get(grade_key, {}).get('subjects', {}).get(app_subject_key, app_subject_key)

        context_injection = ""
        if search_status == 'found' and retrieved_context_str and retrieved_context_str.strip():
            context_injection = f"""
---
[معلومات إضافية من المنهج الدراسي لمادة "{app_subject_key}" للصف {grade_details['name']}]
استخدم هذه المعلومات من المنهج الدراسي لمساعدتك في الإجابة على سؤال الطفل بدقة أكبر.
إذا كانت المعلومات المسترجعة غير ذات صلة مباشرة بالسؤال، أو كانت عامة جدًا، يمكنك تجاهلها والاعتماد على معرفتك العامة مع الالتزام بأسلوب الشرح المحدد للصف.
تأكد من أن إجابتك النهائية موجهة للطفل بالأسلوب المطلوب.

المعلومات المسترجعة:
{retrieved_context_str}
---
"""
        elif search_status == 'not_found':
            context_injection = f"""
---
[ملاحظة حول البحث في المنهج لمادة "{app_subject_key}" للصف {grade_details['name']}]
لم يتم العثور على معلومات محددة في المنهج الدراسي تتعلق بهذا السؤال.
يرجى الاعتماد على معرفتك العامة لتقديم إجابة واضحة ومناسبة، مع الالتزام بأسلوب الشرح المحدد للصف.
---
"""
        elif search_status == 'not_searched_greeting':
            context_injection = "\n--- [ملاحظة: هذا السؤال هو تحية أو عبارة عامة، لا يتطلب بحثًا في المنهج. رد بشكل مناسب وودي.] ---\n"
        elif search_status == 'kb_unavailable':
             context_injection = f"""
---
[ملاحظة: قاعدة المعرفة لمادة "{app_subject_key}" للصف {grade_details['name']} غير متاحة حاليًا أو لم يتم بناؤها.]
يرجى الاعتماد على معرفتك العامة لتقديم إجابة واضحة ومناسبة، مع الالتزام بأسلوب الشرح المحدد للصف.
---
"""
        
        # تحديد التحية الافتتاحية بناءً على نوع السؤال
        opening_greeting = 'ابدأ ردك بتحية ودودة للطفل (مثل "مرحباً يا بطل!" أو "أهلاً يا صغيري!") واختتم بتشجيع أو سؤال مفتوح يحفزه على التفكير.'
        if search_status == 'not_searched_greeting':
            opening_greeting = 'رد على تحية الطفل أو عبارته العامة بشكل طبيعي وودي ومناسب. لا تحاول ربطها بالمنهج.'

        common_instructions = f"""
أنت "المعلم الذكي السعودي"، معلم خبير ومحب للأطفال، متحمس، مشجع، وصابر. مهمتك هي الإجابة على أسئلة الأطفال وتقديم شروحات ورسومات SVG تعليمية بسيطة وجذابة.
{opening_greeting}

**تعليمات عامة صارمة يجب اتباعها دائمًا:**
1.  **الرد بصيغة JSON فقط:** يجب أن يكون ردك بالكامل عبارة عن كائن JSON صالح يحتوي على مفتاحين بالضبط: `text_explanation` و `svg_code`. لا تضف أي نص قبل أو بعد كائن JSON.
    مثال للبنية المطلوبة: `{{"text_explanation": "شرح مبسط هنا...", "svg_code": "<svg width='...' height='...'>...</svg>"}}`
2.  **اللغة العربية الفصحى المبسطة:** استخدم لغة عربية فصحى واضحة وبسيطة جدًا، مناسبة تمامًا لعمر الطفل. تجنب تمامًا أي لهجات عامية أو كلمات معقدة. **اربط المفاهيم بأمثلة من الحياة اليومية للطفل أو أشياء مألوفة لديه، واشرح المصطلحات الجديدة بوضوح.**
3.  **أسلوب الشرح:** يجب أن يكون الشرح {grade_details['style_desc']}. يجب أن يكون طول الشرح حوالي {grade_details['explanation_length']}. **تجنب التعميمات والشرح المبهم، واشرح المفهوم خطوة بخطوة بطريقة منطقية.**
4.  **الرسوم التوضيحية (SVG):**
    *   يجب أن يكون `svg_code` عبارة عن كود SVG كامل وصالح للعرض، يبدأ بـ `<svg ...>` وينتهي بـ `</svg>`.
    *   استخدم الأبعاد: `width="{self.base_svg_config['width']}"` و `height="{self.base_svg_config['height']}"`.
    *   اجعل خلفية الرسم `{self.base_svg_config['background_color']}`.
    *   يجب أن يكون الرسم جذابًا بصريًا، بسيطًا، وواضحًا، ويعكس تعقيدًا مناسبًا لـ {grade_details['svg_complexity']}. **ركز على الوضوح المباشر للمفهوم وتجنب التفاصيل المشتتة. استخدم تباينًا جيدًا للألوان.**
    *   استخدم ألوانًا زاهية ومناسبة للأطفال من هذه القائمة إذا أمكن: {', '.join(self.base_svg_config['primary_colors'])}. لون النص الرئيسي داخل SVG يجب أن يكون `{self.base_svg_config['text_color']}`.
    *   إذا كان هناك نص داخل الرسم (مثل الحروف، الأرقام، أو التسميات)، يجب أن يكون واضحًا ومقروءًا باللغة العربية، وبحجم مناسب (مثلاً، `{grade_details['svg_font_size_large']}` للعناصر الكبيرة و `{grade_details['svg_font_size_small']}` للتسميات). **استخدم خطًا يدعم العربية مثل 'Arial' أو 'Noto Sans Arabic' وتأكد أن النص داخل حدود الرسم ولا يقطعه شيء.**
    *   **مهم جدًا للـ SVG:** يجب أن تكون جميع العناصر مرسومة داخل حدود الـ SVG المحددة. وأن تكون العناصر الرئيسية في منتصف لوحة الرسم. **تأكد من أن كل عنصر رسم له سمات `fill` و `stroke` واضحة. تجنب الأشكال المتقاطعة بشكل غير مفهوم.**
    *   **الهدف التعليمي للرسم:** يجب أن يخدم الرسم الغرض التعليمي بوضوح ويساعد الطفل على فهم المفهوم بشكل أفضل.
    *   **إذا كان السؤال تحية بسيطة (search_status == 'not_searched_greeting')، يمكنك اختيار عدم إنتاج SVG أو إنتاج SVG بسيط جدًا وودي (مثل وجه مبتسم أو رمز ترحيبي).**
5.  **التركيز على السؤال:** أجب على سؤال الطفل المحدد. لا تخرج عن الموضوع إلا إذا كان السؤال تحية.

**سؤال الطفل:** "{question}"
"""
        # اختيار البرومبت المتخصص بناءً على المادة
        if app_subject_key == 'arabic':
            return self._get_arabic_prompt(common_instructions, context_injection, grade_details, search_status)
        elif app_subject_key == 'math':
            return self._get_math_prompt(common_instructions, context_injection, grade_details, search_status)
        elif app_subject_key == 'science':
            return self._get_science_prompt(common_instructions, context_injection, grade_details, search_status)
        elif app_subject_key == 'social': 
            return self._get_social_prompt(common_instructions, context_injection, grade_details, search_status)
        elif app_subject_key == 'islamic':
            return self._get_islamic_prompt(common_instructions, context_injection, grade_details, search_status)
        elif app_subject_key == 'english':
            return self._get_english_prompt(common_instructions, context_injection, grade_details, question, search_status)
        else:
            return self._get_general_prompt(common_instructions, context_injection, grade_details, search_status)

    def _get_arabic_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, search_status: Optional[str]) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة اللغة العربية ({grade_details['name']}):**
*   ركز على الحروف، الكلمات، الحركات، المدود، التنوين، إلخ، حسب السؤال.
*   إذا كان السؤال عن حرف، ارسم الحرف كبيرًا وواضحًا مع أي حركات مطلوبة. يمكنك إضافة شكل بسيط يتعلق بالحرف.
*   إذا كان السؤال تحية (`search_status == 'not_searched_greeting'`)، تجاهل هذه التعليمات الخاصة بالمادة ورد بشكل طبيعي.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_math_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, search_status: Optional[str]) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة الرياضيات ({grade_details['name']}):**
*   ركز على الأرقام، العد، الجمع، الطرح، الأشكال الهندسية البسيطة، إلخ، حسب السؤال.
*   إذا كان السؤال عن عملية حسابية، وضحها بالرسم باستخدام أشياء مألوفة.
*   إذا كان عن الأشكال، ارسم الشكل المطلوب بوضوح مع تسميته.
*   إذا كان السؤال تحية (`search_status == 'not_searched_greeting'`)، تجاهل هذه التعليمات الخاصة بالمادة ورد بشكل طبيعي.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_science_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, search_status: Optional[str]) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة العلوم ({grade_details['name']}):**
*   ركز على مفاهيم العلوم البسيطة مثل أجزاء النبات، الحيوانات، حالات الماء، الحواس الخمس.
*   استخدم رسومات توضيحية بسيطة ودقيقة علمياً بما يتناسب مع الصف.
*   إذا كان المفهوم يتضمن أجزاء، ارسم كل جزء بوضوح مع تسميته.
*   إذا كان السؤال تحية (`search_status == 'not_searched_greeting'`)، تجاهل هذه التعليمات الخاصة بالمادة ورد بشكل طبيعي.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_social_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, search_status: Optional[str]) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة المهارات الحياتية/الاجتماعية ({grade_details['name']}):**
*   ركز على موضوعات مثل أفراد العائلة، أدواتي المدرسية، قواعد النظافة، المهن.
*   يمكن أن تكون الرسومات عبارة عن مشاهد بسيطة أو أيقونات.
*   إذا كان السؤال تحية (`search_status == 'not_searched_greeting'`)، تجاهل هذه التعليمات الخاصة بالمادة ورد بشكل طبيعي.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

    def _get_islamic_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, search_status: Optional[str]) -> str:
        subject_specific_instructions = f"""
**تعليمات خاصة بمادة التربية الإسلامية ({grade_details['name']}):**
*   ركز على المفاهيم الإسلامية الأساسية: أركان الإسلام، الوضوء، الصلاة (مبسطة)، أدعية قصيرة.
*   يجب أن تكون الرسومات محتشمة وبسيطة. تجنب رسم صور ذات تفاصيل دقيقة للكائنات الحية.
*   إذا كان السؤال تحية (`search_status == 'not_searched_greeting'`)، تجاهل هذه التعليمات الخاصة بالمادة ورد بشكل طبيعي، ولكن يمكنك استخدام تحية إسلامية مناسبة إذا أردت.
"""
        return f"{common_instructions}\n{subject_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."
   
    def _get_english_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, original_question: str, search_status: Optional[str]) -> str:
        # تعديل common_instructions ليعكس أن الشرح سيكون بالإنجليزية إذا لم يكن تحية
        # إذا كان تحية، فالرد قد يكون بالعربية أو الإنجليزية حسب السياق الأفضل
        
        english_opening_greeting = f'Start your response with a friendly greeting in simple English (e.g., "Hello little champion!" or "Hi there!") and end with encouragement or an open-ended question.'
        if search_status == 'not_searched_greeting':
            # إذا كانت التحية الأصلية بالعربية، قد يكون من الأفضل الرد بالعربية
            # هذا يعتمد على كيفية التعامل مع السؤال الأصلي. حاليًا، سنبقيها إنجليزية للتبسيط.
            english_opening_greeting = 'Respond to the child\'s greeting or general phrase naturally and friendly in simple English (or Arabic if the original greeting was clearly Arabic and a simple English reply feels off). Do not try to relate it to the curriculum.'

        # تعديل common_instructions لتناسب الإنجليزية
        # هذا مثال مبسط، قد تحتاج لتعديل أكثر تعقيدًا للجزء العام من common_instructions
        # إذا كان السؤال بالإنجليزية ويتطلب شرحًا بالإنجليزية.
        # حاليًا، سأبقي common_instructions كما هو مع افتراض أن النموذج سيفهم التبديل للإنجليزية عند الحاجة.
        # من الأفضل إنشاء common_instructions مخصص للغة الإنجليزية بالكامل.
        
        # للحفاظ على البساطة، سنقوم فقط بتعديل الجزء الخاص بالمادة
        
        # إعادة صياغة الـ common_instructions ليكون أكثر وعيًا باللغة المطلوبة
        # (هذا الجزء قد يحتاج لمزيد من التفكير ليكون مثاليًا)
        # لنفترض أن common_instructions التي تم تمريرها بالفعل جيدة كقاعدة
        # ونحن فقط نضيف التعليمات الخاصة باللغة الإنجليزية

        effective_common_instructions = common_instructions # استخدام النسخة المعدلة من get_specialized_prompt

        # إذا كان السؤال تحية، فالشرح سيكون بالإنجليزية البسيطة
        explanation_language = "simple, clear English, suitable for the child's age"
        if search_status == 'not_searched_greeting' and not any(char.isalpha() and ord(char) > 127 for char in original_question): # إذا كان السؤال لا يحتوي على أحرف عربية
             pass # تبقى اللغة إنجليزية
        elif search_status == 'not_searched_greeting': # إذا كانت التحية بالعربية
            explanation_language = "اللغة العربية الفصحى المبسطة أو الإنجليزية البسيطة، أيهما أنسب للرد على التحية"


        subject_specific_instructions = f"""
**Specific instructions for English Language ({grade_details['name']}):**
*   The explanation (`text_explanation`) should be in {explanation_language}.
*   If the question is about an English letter (e.g., "Teach me the letter A"), explain it in English and draw the letter large and clear. You can add a simple picture of a word starting with this letter (e.g., Apple for A).
*   If the question is about an English word (e.g., "What is a cat?"), explain it in English and draw it.
*   Text inside the SVG should be in English (e.g., letters A, B, C, words cat, dog).
*   If the question is a greeting (`search_status == 'not_searched_greeting'`), ignore these subject-specific instructions and respond naturally.
"""
        # تعديل context_injection ليكون بالإنجليزية إذا كان السياق المسترجع بالإنجليزية
        # أو يتم تجاهله إذا كان بالعربية وغير مفيد.
        # حاليًا، سيمرر كما هو.
        
        # استبدال جزء اللغة في common_instructions إذا كان السؤال يتطلب ردًا إنجليزيًا وليس مجرد تحية
        final_instructions = effective_common_instructions
        if search_status != 'not_searched_greeting' or (search_status == 'not_searched_greeting' and not any(char.isalpha() and ord(char) > 127 for char in original_question)):
            final_instructions = final_instructions.replace(
                "اللغة العربية الفصحى المبسطة", 
                "simple, clear English, suitable for the child's age. Use short sentences and vocabulary."
            )
            final_instructions = final_instructions.replace(
                'ابدأ ردك بتحية ودودة للطفل (مثل "مرحباً يا بطل!" أو "أهلاً يا صغيري!") واختتم بتشجيع أو سؤال مفتوح يحفزه على التفكير.',
                english_opening_greeting
            )
            final_instructions = final_instructions.replace(
                "إذا كان هناك نص داخل الرسم (مثل الحروف، الأرقام، أو التسميات)، يجب أن يكون واضحًا ومقروءًا باللغة العربية",
                "If there is text inside the drawing (like letters, numbers, or labels), it must be clear, readable, and in English"
            )


        return f"{final_instructions}\n{subject_specific_instructions}\n{context_injection}\nRemember, the response MUST be JSON only with the specified structure."

    def _get_general_prompt(self, common_instructions: str, context_injection: str, grade_details: dict, search_status: Optional[str]) -> str:
        general_specific_instructions = f"""
**تعليمات إضافية للأسئلة العامة ({grade_details['name']}):**
*   حاول فهم القصد من سؤال الطفل وقدم إجابة مفيدة ومناسبة لعمره.
*   إذا كان السؤال يطلب رسمًا، اجعل الرسم بسيطًا وملونًا ويعكس موضوع السؤال.
*   إذا كان السؤال تحية (`search_status == 'not_searched_greeting'`)، تجاهل هذه التعليمات ورد بشكل طبيعي.
"""
        return f"{common_instructions}\n{general_specific_instructions}\n{context_injection}\nتذكر، الرد يجب أن يكون JSON فقط بالبنية المحددة."

if __name__ == "__main__":
    engine = UnifiedPromptEngine()
    test_question_arabic_greeting = "السلام عليكم"
    test_grade = 'grade_1'
    test_subject_math = 'math'

    prompt_greeting_math = engine.get_specialized_prompt(
        test_question_arabic_greeting, 
        test_subject_math, 
        test_grade,
        search_status='not_searched_greeting'
    )
    print(f"--- Prompt for Math (Grade 1) - Greeting (length: {len(prompt_greeting_math)}) ---")
    # print(prompt_greeting_math) 
    print("------\n")

    test_question_math_real = "اشرح لي واحد زائد واحد"
    prompt_math_real_no_context = engine.get_specialized_prompt(
        test_question_math_real,
        test_subject_math,
        test_grade,
        search_status='not_found'
    )
    print(f"--- Prompt for Math (Grade 1) - Real Question, No Context (length: {len(prompt_math_real_no_context)}) ---")
    # print(prompt_math_real_no_context)
    print("------\n")

    sample_retrieved_context = "جمع الأعداد: 1+1 = 2. يمكن تمثيل ذلك باستخدام تفاحتين."
    prompt_math_real_with_context = engine.get_specialized_prompt(
        test_question_math_real,
        test_subject_math,
        test_grade,
        retrieved_context_str=sample_retrieved_context,
        search_status='found'
    )
    print(f"--- Prompt for Math (Grade 1) - Real Question, With Context (length: {len(prompt_math_real_with_context)}) ---")
    # print(prompt_math_real_with_context)
    print("------\n")

    test_question_english_greeting = "Hello"
    test_subject_english = 'english'
    prompt_english_greeting = engine.get_specialized_prompt(
        test_question_english_greeting,
        test_subject_english,
        test_grade,
        search_status='not_searched_greeting'
    )
    print(f"--- Prompt for English (Grade 1) - Greeting (length: {len(prompt_english_greeting)}) ---")
    # print(prompt_english_greeting)
    print("------\n")
