# tutor_ai/__init__.py
"""
المعلم الذكي السعودي - وحدة التعليم الذكي المحسنة
Smart Saudi Tutor - Enhanced AI Teaching Module
"""

__version__ = "3.1.0"
__author__ = "Smart Saudi Tutor Team"

# استيراد المكونات الرئيسية
try:
    from .gemini_client import GeminiClientVertexAI
    from .prompt_engineering import UnifiedPromptEngine
    from .knowledge_base_manager import KnowledgeBaseManager
    from .code_executor import save_svg_content_to_file
    
    __all__ = [
        'GeminiClientVertexAI',
        'UnifiedPromptEngine', 
        'KnowledgeBaseManager',
        'save_svg_content_to_file'
    ]
    
except ImportError as e:
    print(f"Warning: Could not import all tutor_ai components: {e}")
    __all__ = []
