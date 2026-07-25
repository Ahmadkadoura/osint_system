import json
from typing import List, Dict, Any
from core.entity import ParsedEntity

class PayloadBuilder:
    @staticmethod
    def build_success_payload(parsed_entity: ParsedEntity, ranked_variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        يجمع مخرجات المعالجة اللغوية والترتيب التوافيقي في مستند JSON واحد منظم واحترافي.
        """
        if not parsed_entity:
            return {
                "status": "success",
                "data": None,
                "message": "No entity was parsed from the input."
            }

        # بناء هيكل الـ JSON النهائي للمشروع
        payload = {
            "status": "success",
            "metadata": {
                "engine_version": "1.0.0",
                "confidence_score": parsed_entity.confidence
            },
            "identity": {
                "arabic_analysis": {
                    "full_name": parsed_entity.full_name,
                    "components": {
                        "first_name": parsed_entity.first_name,
                        "middle_names": parsed_entity.middle_names,
                        "last_name": parsed_entity.last_name
                    },
                    "extracted_attributes": {
                        "profession": parsed_entity.profession,
                        "location": parsed_entity.location
                    }
                },
                "latin_transliterations": {
                    "total_generated": len(ranked_variants),
                    "top_suggestions": [
                        {
                            "rank": idx,
                            "name": var["latin_name"],
                            "score": var["final_score"]
                        }
                        for idx, var in enumerate(ranked_variants, 1)
                    ]
                }
            }
        }
        return payload

    @staticmethod
    def build_error_payload(error_message: str, error_code: int = 400) -> Dict[str, Any]:
        """
        بناء Payload موحد في حالة حدوث أي خطأ أو استثناء داخل الـ Pipeline.
        """
        return {
            "status": "error",
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
