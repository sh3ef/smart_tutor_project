# tutor_ai/knowledge_base_manager.py
import os
import shutil
import traceback
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعدادات المسارات
KNOWLEDGE_BASE_PARENT_DOCS_DIR = "knowledge_base_docs"
CHROMA_DB_PARENT_DIRECTORY = "chroma_dbs"

# محاولة استيراد المكتبات المطلوبة
try:
    from langchain_community.document_loaders import (
        UnstructuredMarkdownLoader,
        TextLoader,
        DirectoryLoader,
        Docx2txtLoader,
    )
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    LANGCHAIN_LOADERS_AVAILABLE = True
except ImportError as e:
    print(f"KB_MANAGER WARNING: LangChain document loaders not available: {e}")
    LANGCHAIN_LOADERS_AVAILABLE = False

try:
    from langchain_chroma import Chroma
    LANGCHAIN_CHROMA_AVAILABLE = True
except ImportError:
    print("KB_MANAGER WARNING: LangChain Chroma integration not available. Please install langchain-chroma.")
    LANGCHAIN_CHROMA_AVAILABLE = False

try:
    from langchain_google_vertexai import VertexAIEmbeddings
    import vertexai
    VERTEX_AI_AVAILABLE = True
except ImportError:
    print("KB_MANAGER WARNING: Vertex AI components not available. Please install google-cloud-aiplatform.")
    VERTEX_AI_AVAILABLE = False

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    print("KB_MANAGER WARNING: ChromaDB not available. Please install chromadb.")
    CHROMADB_AVAILABLE = False

# التحقق من توفر جميع المتطلبات لـ RAG
RAG_REQUIREMENTS_MET = (
    LANGCHAIN_LOADERS_AVAILABLE and
    LANGCHAIN_CHROMA_AVAILABLE and
    VERTEX_AI_AVAILABLE and
    CHROMADB_AVAILABLE
)

# النماذج المدعومة فعلاً (مرتبة حسب الأولوية)
EMBEDDING_MODELS = [
    "gemini-embedding-001",         # الأحدث والأفضل - 3072 dimensions
    "text-embedding-005",           # نموذج حديث - 768 dimensions  
    "text-embedding-004",           # نموذج مستقر - 768 dimensions
    "textembedding-gecko@latest",   # محاولة أخيرة للنماذج القديمة
]

class KnowledgeBaseManager:
    """مدير قاعدة المعرفة مع دعم ChromaDB و Vertex AI Embeddings"""

    def __init__(self, grade_folder_name: str, subject_folder_name: str,
                 project_id: str, location: str = "us-central1",
                 force_recreate: bool = False):
        """
        تهيئة مدير قاعدة المعرفة
        """
        self.grade_folder = grade_folder_name
        self.subject_folder = subject_folder_name
        self.project_id = project_id
        self.location = location

        # إنشاء اسم فريد للـ collection في ChromaDB
        clean_grade_folder = grade_folder_name.replace(" ", "_").lower()
        subject_folder_cleaned = subject_folder_name.replace(" ", "_").lower()
        subject_folder_cleaned = subject_folder_cleaned.replace("الدراسات_الاسلامية", "islamic_studies")
        subject_folder_cleaned = subject_folder_cleaned.replace("المهارات_الأسرية", "family_skills")
        self.collection_name = f"{clean_grade_folder}_{subject_folder_cleaned}_coll"

        self.docs_path = os.path.join(KNOWLEDGE_BASE_PARENT_DOCS_DIR, self.grade_folder, self.subject_folder)
        self.vector_store_path = os.path.join(CHROMA_DB_PARENT_DIRECTORY, self.collection_name)

        # التحقق من توفر المتطلبات الأساسية
        if not RAG_REQUIREMENTS_MET:
            print(f"KB_MANAGER ERROR: متطلبات RAG غير متوفرة لـ {self.collection_name}.")
            print(f"  LangChain Loaders: {LANGCHAIN_LOADERS_AVAILABLE}")
            print(f"  LangChain Chroma: {LANGCHAIN_CHROMA_AVAILABLE}")
            print(f"  Vertex AI: {VERTEX_AI_AVAILABLE}")
            print(f"  ChromaDB: {CHROMADB_AVAILABLE}")
            self.embedding_function = None
            self.db = None
            self.current_model = None
            return

        # تهيئة دالة التضمين
        self.embedding_function: Optional[VertexAIEmbeddings] = None
        self.current_model = None
        self._init_embeddings()

        # حذف قاعدة البيانات القديمة إذا طُلب ذلك
        if force_recreate and os.path.exists(self.vector_store_path):
            print(f"KB_MANAGER INFO: إجبار إعادة الإنشاء. حذف بيانات ChromaDB الموجودة في: {self.vector_store_path}")
            try:
                shutil.rmtree(self.vector_store_path)
                print(f"KB_MANAGER INFO: تم حذف المجلد {self.vector_store_path} بنجاح لمجموعة '{self.collection_name}'.")
            except OSError as e_del:
                print(f"KB_MANAGER WARNING: تعذر حذف المجلد {self.vector_store_path}: {e_del}.")

        # تهيئة قاعدة البيانات
        self.db: Optional[Chroma] = None
        if self.embedding_function:
            self._initialize_vector_store()

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )

    def _init_embeddings(self):
        """تهيئة دوال التضمين من Vertex AI مع النماذج المدعومة الجديدة"""
        try:
            # البحث عن بيانات الاعتماد
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            
            # إذا لم تجد في متغير البيئة، تحقق من Streamlit Secrets
            if not cred_path or not os.path.exists(cred_path):
                try:
                    import streamlit as st
                    if hasattr(st, 'secrets'):
                        import tempfile
                        import json
                        
                        credentials_json = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                        if credentials_json:
                            if isinstance(credentials_json, str):
                                credentials_dict = json.loads(credentials_json)
                            else:
                                credentials_dict = credentials_json
                            
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                                json.dump(credentials_dict, f)
                                cred_path = f.name
                                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
                                print(f"KB_MANAGER INFO: تم إنشاء ملف مؤقت للاعتماد: {cred_path}")
                except:
                    pass

            if not cred_path or not os.path.exists(cred_path):
                print(f"KB_MANAGER ERROR: GOOGLE_APPLICATION_CREDENTIALS غير مضبوط بشكل صحيح.")
                self.embedding_function = None
                return

            # تهيئة Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            print(f"KB_MANAGER INFO: تم تهيئة Vertex AI للمشروع '{self.project_id}' في المنطقة '{self.location}'")
            
            # محاولة النماذج المدعومة بالترتيب
            for model_name in EMBEDDING_MODELS:
                try:
                    print(f"KB_MANAGER INFO: محاولة نموذج التضمين '{model_name}'...")
                    
                    # إنشاء نموذج التضمين
                    self.embedding_function = VertexAIEmbeddings(
                        model_name=model_name,
                        project=self.project_id,
                        location=self.location
                    )
                    
                    # اختبار النموذج بنص بسيط
                    try:
                        test_embedding = self.embedding_function.embed_query("اختبار النموذج")
                        if test_embedding and len(test_embedding) > 0:
                            self.current_model = model_name
                            embedding_dim = len(test_embedding)
                            print(f"KB_MANAGER SUCCESS: ✅ تم تهيئة VertexAIEmbeddings بنجاح!")
                            print(f"  النموذج: {model_name}")
                            print(f"  أبعاد التضمين: {embedding_dim}")
                            print(f"  المشروع: {self.project_id}")
                            print(f"  المنطقة: {self.location}")
                            return
                    except Exception as test_error:
                        print(f"KB_MANAGER WARNING: فشل اختبار النموذج '{model_name}': {test_error}")
                        continue
                        
                except Exception as model_error:
                    print(f"KB_MANAGER WARNING: فشل تهيئة نموذج '{model_name}': {model_error}")
                    continue
            
            # إذا فشلت جميع النماذج
            print(f"KB_MANAGER ERROR: فشلت جميع نماذج التضمين المتاحة.")
            print(f"تأكد من:")
            print(f"1. تفعيل Vertex AI API في مشروع '{self.project_id}'")
            print(f"2. أن حساب الخدمة لديه صلاحية 'Vertex AI User'")
            print(f"3. أن المشروع يدعم نماذج التضمين في المنطقة '{self.location}'")
            print(f"4. أن المشروع ليس جديداً (النماذج الجديدة تحتاج استخدام سابق)")
            self.embedding_function = None
            self.current_model = None
            
        except Exception as e:
            print(f"KB_MANAGER ERROR: فشل عام في تهيئة VertexAIEmbeddings: {e}")
            traceback.print_exc()
            self.embedding_function = None
            self.current_model = None

    def _initialize_vector_store(self) -> None:
        """تهيئة مخزن المتجهات (ChromaDB)"""
        if not self.embedding_function:
            print(f"KB_MANAGER ERROR: دالة التضمين غير مهيأة لمجموعة '{self.collection_name}'.")
            self.db = None
            return

        os.makedirs(CHROMA_DB_PARENT_DIRECTORY, exist_ok=True)
        os.makedirs(self.vector_store_path, exist_ok=True)

        print(f"KB_MANAGER INFO: تهيئة ChromaDB لمجموعة '{self.collection_name}' باستخدام النموذج '{self.current_model}'")

        try:
            client = chromadb.PersistentClient(path=self.vector_store_path)

            self.db = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
            )
            
            try:
                count = self.db._collection.count()
                print(f"KB_MANAGER INFO: تم تحميل مجموعة ChromaDB '{self.collection_name}' الموجودة مع {count} عنصر.")
                if count == 0:
                    print(f"KB_MANAGER INFO: مجموعة '{self.collection_name}' فارغة. قد تحتاج إلى بنائها.")
            except Exception as e_count:
                print(f"KB_MANAGER WARNING: تعذر الحصول على عدد المستندات في المجموعة '{self.collection_name}': {e_count}")

        except Exception as e:
            print(f"KB_MANAGER ERROR: فشل تهيئة قاعدة البيانات ChromaDB لمجموعة '{self.collection_name}': {e}")
            traceback.print_exc()
            self.db = None

    def _load_documents(self) -> List[Document]:
        """تحميل المستندات من المجلد المحدد"""
        if not LANGCHAIN_LOADERS_AVAILABLE:
            print(f"KB_MANAGER ERROR: LangChain document loaders غير متوفرة لـ {self.collection_name}")
            return []

        if not os.path.exists(self.docs_path):
            print(f"KB_MANAGER WARNING: مسار المستندات {self.docs_path} غير موجود لـ {self.collection_name}.")
            return []
       
        if not os.listdir(self.docs_path):
            print(f"KB_MANAGER WARNING: مسار المستندات {self.docs_path} فارغ لـ {self.collection_name}.")
            return []

        print(f"KB_MANAGER INFO: تحميل المستندات لـ {self.collection_name} من: {self.docs_path}")
       
        all_docs: List[Document] = []
       
        # معالجات الملفات المختلفة
        file_handlers: Dict[str, Dict[str, Any]] = {
            "**/*.md": {"loader_cls": UnstructuredMarkdownLoader, "loader_kwargs": {}},
            "**/*.txt": {"loader_cls": TextLoader, "loader_kwargs": {'encoding': 'utf-8'}},
            "**/*.docx": {"loader_cls": Docx2txtLoader, "loader_kwargs": {}},
        }

        for glob_pattern, handler_config in file_handlers.items():
            loader_cls = handler_config["loader_cls"]
            loader_kwargs = handler_config["loader_kwargs"]
           
            print(f"KB_MANAGER INFO: محاولة تحميل الملفات بنمط '{glob_pattern}' باستخدام {loader_cls.__name__}...")
           
            try:
                current_loader = DirectoryLoader(
                    self.docs_path,
                    glob=glob_pattern,
                    loader_cls=loader_cls,
                    loader_kwargs=loader_kwargs,
                    show_progress=True,
                    silent_errors=True
                )
                loaded_docs = current_loader.load()
                if loaded_docs:
                    all_docs.extend(loaded_docs)
                    print(f"KB_MANAGER INFO: تم تحميل {len(loaded_docs)} مستند(ات) بنجاح باستخدام النمط '{glob_pattern}'.")
                else:
                    print(f"KB_MANAGER INFO: لم يتم العثور على مستندات أو تحميلها للنمط '{glob_pattern}'.")
            except Exception as e_load:
                print(f"KB_MANAGER ERROR: فشل تحميل المستندات بنمط '{glob_pattern}' باستخدام {loader_cls.__name__}: {e_load}")

        print(f"KB_MANAGER INFO: إجمالي المستندات المحملة لـ {self.collection_name}: {len(all_docs)}")
        if not all_docs:
            print(f"KB_MANAGER WARNING: لم يتم تحميل أي مستندات بنجاح من {self.docs_path}.")
        return all_docs

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """تقسيم المستندات إلى قطع أصغر"""
        if not documents:
            return []
       
        split_docs = self.text_splitter.split_documents(documents)
        print(f"KB_MANAGER INFO: تم تقسيم {len(documents)} مستند إلى {len(split_docs)} جزء لـ {self.collection_name}.")
        return split_docs

    def build_knowledge_base(self) -> bool:
        """بناء قاعدة المعرفة"""
        if not RAG_REQUIREMENTS_MET:
            print(f"KB_MANAGER ERROR: متطلبات RAG غير متوفرة لـ {self.collection_name}")
            return False
           
        if not self.embedding_function:
            print(f"KB_MANAGER ERROR: دالة التضمين غير مهيأة لـ {self.collection_name}.")
            return False

        if not self.db:
            print(f"KB_MANAGER INFO: إعادة محاولة تهيئة ChromaDB لـ {self.collection_name} قبل البناء.")
            self._initialize_vector_store()
            if not self.db:
                print(f"KB_MANAGER ERROR: فشل تهيئة ChromaDB قبل البناء لـ {self.collection_name}.")
                return False
           
        print(f"KB_MANAGER INFO: بدء بناء قاعدة المعرفة لـ {self.collection_name} باستخدام نموذج '{self.current_model}'...")
        documents = self._load_documents()
       
        if not documents:
            print(f"KB_MANAGER WARNING: لم يتم العثور على مستندات لبناء قاعدة المعرفة لـ {self.collection_name}.")
            return True

        split_docs = self._split_documents(documents)
        if not split_docs:
            print(f"KB_MANAGER WARNING: لا يوجد محتوى بعد تقسيم المستندات لـ {self.collection_name}.")
            return True

        try:
            print(f"KB_MANAGER INFO: ملء مجموعة ChromaDB '{self.collection_name}' بـ {len(split_docs)} جزء...")
            
            self.db.add_documents(split_docs)

            count_after_build = self.db._collection.count()
            print(f"KB_MANAGER SUCCESS: ✅ تم بناء قاعدة المعرفة لـ {self.collection_name} بنجاح!")
            print(f"  عدد الأجزاء: {count_after_build}")
            print(f"  النموذج المستخدم: {self.current_model}")
            return True
        except Exception as e_build:
            print(f"KB_MANAGER ERROR: فشل بناء ChromaDB لـ {self.collection_name}: {e_build}")
            traceback.print_exc()
            self.db = None
            return False

    def get_retriever(self, search_type: str = "similarity", k_results: int = 3) -> Optional[Any]:
        """الحصول على أداة استرجاع الوثائق"""
        if not self.db:
            print(f"KB_MANAGER ERROR: ChromaDB غير مهيأة للمجموعة '{self.collection_name}'.")
            return None
           
        try:
            return self.db.as_retriever(
                search_type=search_type,
                search_kwargs={"k": k_results}
            )
        except Exception as e_retriever:
            print(f"KB_MANAGER ERROR: تعذر الحصول على أداة الاسترجاع للمجموعة '{self.collection_name}': {e_retriever}")
            traceback.print_exc()
            return None

    def search_documents(self, query: str, k_results: int = 3) -> List[Document]:
        """البحث المباشر في الوثائق"""
        if not self.db:
            print(f"KB_MANAGER ERROR: ChromaDB غير مهيأة لـ '{self.collection_name}'.")
            return []
       
        try:
            results = self.db.similarity_search(query, k=k_results)
            print(f"KB_MANAGER INFO: تم العثور على {len(results)} نتيجة للاستعلام: '{query}' باستخدام نموذج '{self.current_model}'")
            return results
        except Exception as e:
            print(f"KB_MANAGER ERROR: فشل البحث لـ '{self.collection_name}': {e}")
            traceback.print_exc()
            return []

    def get_database_info(self) -> Dict:
        """الحصول على معلومات قاعدة البيانات"""
        info = {
            "grade": self.grade_folder,
            "subject": self.subject_folder,
            "collection_name": self.collection_name,
            "docs_path": self.docs_path,
            "vector_store_path": self.vector_store_path,
            "rag_requirements_met": RAG_REQUIREMENTS_MET,
            "embedding_ready": self.embedding_function is not None,
            "db_ready": self.db is not None,
            "current_model": self.current_model,
            "document_count": 0
        }
       
        if self.db and hasattr(self.db, '_collection'):
            try:
                info["document_count"] = self.db._collection.count()
            except Exception as e_count:
                info["document_count"] = f"غير محدد ({e_count})"
       
        return info

def check_rag_requirements():
    """فحص توفر متطلبات RAG"""
    requirements = {
        "LangChain Loaders": LANGCHAIN_LOADERS_AVAILABLE,
        "LangChain Chroma": LANGCHAIN_CHROMA_AVAILABLE,
        "Vertex AI": VERTEX_AI_AVAILABLE,
        "ChromaDB": CHROMADB_AVAILABLE,
        "All Requirements": RAG_REQUIREMENTS_MET
    }
   
    print("KB_MANAGER INFO: فحص متطلبات RAG:")
    for req, available in requirements.items():
        status = "✅" if available else "❌"
        print(f"  {status} {req}")
   
    return requirements

def create_all_knowledge_base_managers(grade_subjects_config: Dict[str, str],
                                     target_grade_folder: str,
                                     project_id: str,
                                     location: str = "us-central1",
                                     force_recreate: bool = False) -> Dict[str, Optional[KnowledgeBaseManager]]:
    """إنشاء مديري قواعد المعرفة لجميع المواد"""
    managers = {}
    print(f"KB_MANAGER INFO: بدء إنشاء مديري قواعد المعرفة لـ {target_grade_folder}...")

    for app_subject_key, subject_folder_name in grade_subjects_config.items():
        manager_key = f"{target_grade_folder}_{app_subject_key}"
        print(f"KB_MANAGER INFO: محاولة إنشاء مدير لقاعدة المعرفة: {manager_key}")
       
        try:
            manager = KnowledgeBaseManager(
                grade_folder_name=target_grade_folder,
                subject_folder_name=subject_folder_name,
                project_id=project_id,
                location=location,
                force_recreate=force_recreate
            )
           
            if manager.embedding_function and manager.db:
                if manager.build_knowledge_base():
                    managers[manager_key] = manager
                    print(f"KB_MANAGER SUCCESS: تم إنشاء مدير قاعدة المعرفة وبنائها/تحميلها بنجاح: {manager_key}")
                else:
                    print(f"KB_MANAGER WARNING: فشل بناء قاعدة المعرفة أو كانت فارغة: {manager_key}.")
                    managers[manager_key] = manager
            else:
                print(f"KB_MANAGER ERROR: فشل تهيئة مدير قاعدة المعرفة: {manager_key}.")
                managers[manager_key] = None
               
        except Exception as e:
            print(f"KB_MANAGER ERROR: خطأ عام في إنشاء مدير قاعدة المعرفة {manager_key}: {e}")
            traceback.print_exc()
            managers[manager_key] = None
   
    return managers

if __name__ == "__main__":
    print("KB_MANAGER INFO: اختبار KnowledgeBaseManager...")
    check_rag_requirements()
