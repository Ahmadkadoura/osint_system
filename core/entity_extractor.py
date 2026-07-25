import os
from transformers import pipeline
from typing import List
from core.entity import Entity

class ArabicEntityExtractor:
    def __init__(self):
        # تحديد المسار المحلي للنموذج
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        self.model_path = os.path.join(project_root, "arabic_ner_model")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"لم يتم العثور على مجلد النموذج في المسار: {self.model_path}"
            )
        
        # استدعاء النموذج محلياً بنجاح دون الحاجة لـ local_files_only
        self.ner_pipeline = pipeline(
            "ner",
            model=self.model_path,
            tokenizer=self.model_path,
            aggregation_strategy="simple"
        )

    def extract(self, text: str) -> List[Entity]:
        """
        يستقبل النص المنظف، يشغل نموذج الـ BERT محلياً، ويعيد قائمة من الكيانات الخام
        """
        if not text or not text.strip():
            return []

        ner_results = self.ner_pipeline(text)
        entities = []
        
        for res in ner_results:
            entity = Entity(
                text=res['word'],
                label=res['entity_group'],
                start=res['start'],
                end=res['end'],
                confidence=float(res['score'])
            )
            entities.append(entity)
            
        return entities

if __name__ == "__main__":
    try:
        extractor = ArabicEntityExtractor()
        sample_text = "زار أحمد محمد مدينة الرياض وتحدث مع منصور"
        
        extracted_entities = extractor.extract(sample_text)
        
        print("\n" + "="*40)
        print(f"تم استخراج {len(extracted_entities)} كيانات بنجاح:")
        print("="*40)
        for ent in extracted_entities:
            print(f"الكيان: {ent.text} -> النوع: {ent.label} (الثقة: {ent.confidence:.2f})")
    except Exception as e:
        print(f"حدث خطأ أثناء التشغيل: {e}")