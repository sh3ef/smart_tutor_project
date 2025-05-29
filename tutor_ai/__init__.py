# tutor_ai/__init__.py
"""
مجلد tutor_ai - نظام المعلم الذكي المتطور
يحتوي على جميع الوحدات المطلوبة لتشغيل المعلم الذكي
"""

__version__ = "1.0.0"
__author__ = "Smart Tutor Team"

# تصدير الكلاسات الرئيسية للاستخدام السهل
try:
    from .gemini_client import GeminiClientVertexAI, EnhancedGeminiClientVertexAI
    from .prompt_engineering import UnifiedPromptEngine
    from .code_executor import save_svg_content_to_file
    from .knowledge_base_manager import KnowledgeBaseManager
    
    __all__ = [
        'GeminiClientVertexAI',
        'EnhancedGeminiClientVertexAI', 
        'UnifiedPromptEngine',
        'save_svg_content_to_file',
        'KnowledgeBaseManager'
    ]
    
except ImportError as e:
    print(f"تحذير: لم يتم تحميل بعض الوحدات: {e}")
    __all__ = []