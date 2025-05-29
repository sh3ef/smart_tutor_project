# tutor_ai/gemini_client.py - النسخة الآمنة
import vertexai
from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold, Part
import json
import os
import traceback
import tempfile
import re
from typing import Dict, Optional, List, Union

# استيراد Streamlit فقط عند الحاجة
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


# --- فاحص جودة الاستجابة ---
class ResponseQualityChecker:
    """فاحص جودة الاستجابات للتأكد من جودة المحتوى المولد"""
   
    @staticmethod
    def check_svg_quality(svg_code: Optional[str]) -> Dict[str, any]:
        """فحص جودة كود SVG"""
        issues = []
        score = 100
       
        if not svg_code or len(svg_code.strip()) < 50:
            issues.append("كود SVG قصير جداً أو فارغ.")
            score -= 60
           
        if '<svg' not in str(svg_code):
            issues.append("لا يحتوي على وسم <svg> الافتتاحي.")
            score -= 30
           
        if '</svg>' not in str(svg_code):
            issues.append("وسم </svg> الختامي غير موجود.")
            score -= 25
           
        if 'width=' not in str(svg_code) or 'height=' not in str(svg_code):
            issues.append("لا يحتوي على أبعاد واضحة.")
            score -= 15
           
        svg_elements = ['<rect', '<circle', '<line', '<text', '<path', '<polygon', '<g']
        has_draw_content = any(element in str(svg_code) for element in svg_elements)
        if not has_draw_content:
            issues.append("لا يحتوي على عناصر رسم فعلية.")
            score -= 40
           
        return {
            'score': max(0, score),
            'issues': issues,
            'is_valid': score >= 50
        }
   
    @staticmethod
    def check_explanation_quality(explanation: Optional[str]) -> Dict[str, any]:
        """فحص جودة الشرح"""
        issues = []
        score = 100
       
        if not explanation or len(explanation.strip()) < 15:
            issues.append("الشرح قصير جداً أو فارغ.")
            score -= 50
           
        arabic_pattern = re.compile(r'[\u0600-\u06FF]+')
        if explanation and not arabic_pattern.search(explanation):
            issues.append("الشرح لا يبدو أنه باللغة العربية.")
            score -= 30
           
        word_count = len(explanation.split()) if explanation else 0
        if word_count < 5 and explanation:
            issues.append("الشرح قصير جداً.")
            score -= 20
        elif word_count > 250 and explanation:
            issues.append("الشرح طويل جداً للمرحلة الابتدائية.")
            score -= 15
           
        return {
            'score': max(0, score),
            'issues': issues,
            'is_valid': score >= 60
        }


# --- عميل Gemini الآمن ---
class GeminiClientVertexAI:
    """عميل Gemini آمن - يقرأ من Streamlit Secrets فقط"""
   
    def __init__(self, project_id: str, location: str, model_name: str = "gemini-2.0-flash"):
        self.model: Optional[GenerativeModel] = None
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.quality_checker = ResponseQualityChecker()
        self.max_retries = 2

        if not project_id or not location:
            print("ERROR: GeminiClientVertexAI - PROJECT_ID or LOCATION not provided.")
            return
           
        try:
            print(f"INFO: GeminiClientVertexAI - Initializing for project: {project_id} in location: {location}")
            
            # إعداد بيانات الاعتماد الآمن
            self._setup_credentials()
            
            vertexai.init(project=project_id, location=location)
            print(f"INFO: GeminiClientVertexAI - Loading model: {model_name}")
            self.model = GenerativeModel(model_name=self.model_name)
            print(f"INFO: GeminiClientVertexAI - Model '{model_name}' initialized successfully.")
        except Exception as e:
            print(f"ERROR: GeminiClientVertexAI - Failed to initialize: {e}")
            traceback.print_exc()
            self._troubleshoot_vertex_init()

    def _setup_credentials(self):
        """إعداد بيانات الاعتماد من Streamlit Secrets فقط (آمن)"""
        try:
            print("DEBUG: Starting secure credential setup...")
            
            # التحقق من وجود متغير البيئة أولاً
            existing_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if existing_creds and os.path.exists(existing_creds):
                print(f"INFO: Using existing credentials from environment")
                return
            
            # القراءة من Streamlit Secrets فقط
            if STREAMLIT_AVAILABLE:
                print("DEBUG: Reading from Streamlit secrets...")
                try:
                    if hasattr(st, 'secrets') and st.secrets:
                        credentials_json = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                        if credentials_json:
                            print("DEBUG: Found credentials in Streamlit secrets")
                            
                            # إنشاء ملف مؤقت آمن
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                                try:
                                    if isinstance(credentials_json, str):
                                        credentials_dict = json.loads(credentials_json)
                                        json.dump(credentials_dict, f, indent=2)
                                        
                                        # التحقق من المفاتيح المطلوبة
                                        required_keys = ['type', 'project_id', 'private_key', 'client_email']
                                        missing_keys = [key for key in required_keys if key not in credentials_dict]
                                        if missing_keys:
                                            print(f"ERROR: Missing required keys: {missing_keys}")
                                            return
                                        
                                        print(f"DEBUG: Credentials validated for project: {credentials_dict.get('project_id')}")
                                    else:
                                        json.dump(credentials_json, f, indent=2)
                                    
                                    temp_path = f.name
                                    print(f"DEBUG: Created temporary credentials file: {temp_path}")
                                    
                                    # تعيين متغير البيئة
                                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_path
                                    print("INFO: Successfully loaded credentials from Streamlit secrets")
                                    
                                    # التحقق من الملف
                                    if os.path.exists(temp_path):
                                        file_size = os.path.getsize(temp_path)
                                        print(f"DEBUG: Credential file created, size: {file_size} bytes")
                                    return
                                    
                                except json.JSONDecodeError as e:
                                    print(f"ERROR: Invalid JSON in credentials: {e}")
                                    return
                                except Exception as e:
                                    print(f"ERROR: Failed to create credential file: {e}")
                                    return
                        else:
                            print("ERROR: GOOGLE_APPLICATION_CREDENTIALS_JSON not found in secrets")
                    else:
                        print("ERROR: Streamlit secrets not available")
                        
                except Exception as e:
                    print(f"ERROR: Failed to read from Streamlit secrets: {e}")
            else:
                print("DEBUG: Streamlit not available")
            
            print("WARN: No valid credentials found")
                    
        except Exception as e:
            print(f"ERROR: Failed to setup credentials: {e}")

    def _troubleshoot_vertex_init(self):
        """تشخيص مشاكل Vertex AI"""
        print("--- Vertex AI Troubleshooting ---")
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        print(f"1. Credentials Path: {cred_path}")
        if cred_path and not os.path.exists(cred_path):
            print("   -> WARNING: Credential file not found!")
        elif not cred_path:
            print("   -> WARNING: No credentials environment variable set")
       
        print(f"2. Project ID: {self.project_id}")
        print(f"3. Location: {self.location}")
        print(f"4. Model: {self.model_name}")
        print("5. Check Vertex AI API is enabled in Google Cloud Console")
        print("6. Check service account has 'Vertex AI User' role")
        print("---------------------------------------------")

    def _create_retry_prompt(self, original_prompt: str, quality_issues: List[str], previous_explanation: Optional[str], previous_svg: Optional[str]) -> str:
        """إنشاء برومبت محسن لإعادة المحاولة"""
        issues_text = " و ".join(quality_issues) if quality_issues else "مشاكل في الجودة"
        retry_prompt_parts = [original_prompt]
        retry_prompt_parts.append("\n\n--- ملاحظات للتحسين ---")
        retry_prompt_parts.append(f"⚠️ المحاولة السابقة كان بها: {issues_text}")
        retry_prompt_parts.append("يرجى التركيز على:")
        retry_prompt_parts.append("1. إنتاج JSON صالح بالبنية المطلوبة")
        retry_prompt_parts.append("2. شرح واضح باللغة العربية المبسطة")
        retry_prompt_parts.append("3. رسم SVG كامل وصالح")
        retry_prompt_parts.append("--- نهاية الملاحظات ---\n")
        return "\n".join(retry_prompt_parts)

    def _extract_and_clean_json_str(self, response_text: str) -> str:
        """استخراج JSON من النص"""
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_str = match.group(0).strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            return json_str.strip()
        return response_text.strip()

    def _parse_json_response(self, json_text: str) -> Optional[Dict]:
        """تحليل JSON مع معالجة الأخطاء"""
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"WARN: JSON parse error: {e}")
            # محاولة إصلاح الفواصل الزائدة
            fixed_text = re.sub(r',\s*([}\]])', r'\1', json_text)
            try:
                return json.loads(fixed_text)
            except json.JSONDecodeError:
                return None

    def query_for_explanation_and_svg(self, prompt_text: str) -> Dict:
        """الاستعلام الرئيسي مع إعادة المحاولة"""
        if not self.model:
            print("ERROR: Gemini model not initialized")
            return {
                "text_explanation": "عذرًا، المعلم الذكي غير جاهز حالياً.",
                "svg_code": None,
                "quality_scores": {"explanation": 0, "svg": 0},
                "quality_issues": ["فشل تهيئة النموذج"]
            }

        current_prompt = prompt_text
        last_explanation = None
        last_svg = None
       
        for attempt in range(self.max_retries + 1):
            print(f"INFO: Sending request to Gemini (Attempt {attempt + 1})")
           
            try:
                generation_config = {
                    "max_output_tokens": 8192,
                    "temperature": 0.65 if attempt == 0 else 0.5,
                    "top_p": 0.95,
                    "top_k": 40
                }
               
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
               
                response = self.model.generate_content(
                    current_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=False
                )
               
                # استخراج النص
                raw_response_text = ""
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            raw_response_text += part.text
                elif hasattr(response, 'text'):
                    raw_response_text = response.text
               
                if not raw_response_text.strip():
                    raise ValueError("رد فارغ من Gemini")

                print(f"Raw response length: {len(raw_response_text)}")

                # استخراج JSON
                json_string = self._extract_and_clean_json_str(raw_response_text)
                if not json_string:
                    raise ValueError("لم يتمكن من استخلاص JSON")
               
                data = self._parse_json_response(json_string)
                if not data or not isinstance(data, dict):
                    raise ValueError("فشل في تحليل JSON")
               
                explanation = data.get("text_explanation")
                svg_code = data.get("svg_code")
                last_explanation = explanation
                last_svg = svg_code

                # فحص الجودة
                explanation_quality = self.quality_checker.check_explanation_quality(explanation)
                svg_quality = self.quality_checker.check_svg_quality(svg_code)
               
                current_issues = []
                if not explanation_quality['is_valid']:
                    current_issues.extend([f"شرح: {issue}" for issue in explanation_quality['issues']])
                if not svg_quality['is_valid']:
                    current_issues.extend([f"رسم: {issue}" for issue in svg_quality['issues']])

                quality_scores = {
                    "explanation": explanation_quality['score'],
                    "svg": svg_quality['score']
                }

                # إرجاع النتيجة إذا كانت الجودة مقبولة
                if explanation_quality['is_valid'] and svg_quality['is_valid']:
                    print(f"INFO: High-quality response received")
                    return {
                        "text_explanation": explanation,
                        "svg_code": svg_code,
                        "quality_scores": quality_scores,
                        "quality_issues": []
                    }
               
                # إعادة المحاولة إذا كانت الجودة منخفضة
                if attempt < self.max_retries:
                    print(f"INFO: Low-quality response, retrying...")
                    current_prompt = self._create_retry_prompt(prompt_text, current_issues, last_explanation, last_svg)
                    continue
                else:
                    # إرجاع أفضل ما لدينا
                    return {
                        "text_explanation": explanation if explanation else "لم يتمكن من إنشاء شرح مناسب.",
                        "svg_code": svg_code,
                        "quality_scores": quality_scores,
                        "quality_issues": current_issues if current_issues else ["فشل في تحقيق الجودة المطلوبة"]
                    }
           
            except Exception as e:
                print(f"ERROR: Exception during attempt {attempt + 1}: {e}")
                if attempt < self.max_retries:
                    current_prompt = self._create_retry_prompt(prompt_text, [str(e)], last_explanation, last_svg)
                    continue
                else:
                    error_message = f"حدث خطأ: {e}"
                    return {
                        "text_explanation": error_message, 
                        "svg_code": None, 
                        "quality_scores": {"explanation": 0, "svg": 0}, 
                        "quality_issues": [error_message]
                    }
       
        # لا يجب الوصول لهنا
        return {
            "text_explanation": "عذرًا، حدث خطأ غير متوقع.",
            "svg_code": None,
            "quality_scores": {"explanation": 0, "svg": 0},
            "quality_issues": ["فشل النظام"]
        }


# للتوافق مع الكود القديم
class EnhancedGeminiClientVertexAI(GeminiClientVertexAI):
    """اسم بديل للتوافق"""
    pass