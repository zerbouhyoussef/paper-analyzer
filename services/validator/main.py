import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from services.validator.config import Config
from services.validator.checks import ALL_CHECKS, CRITICAL_CHECKS, clean_text
from data_contracts.paper import (
    ExtractedPaper,
    ValidatedPaper,
    ValidationResult,
    ProcessingStatus,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_paper(extracted: ExtractedPaper) -> ValidatedPaper:
    """Run all quality checks on an extracted paper."""
    logger.info(f"Validating: {extracted.title}")

    checks: dict[str, bool] = {}
    warnings: list[str] = []
    errors: list[str] = []

    for name, check_fn in ALL_CHECKS.items():
        passed, message = check_fn(extracted.raw_text)
        checks[name] = passed
        if not passed:
            (errors if name in CRITICAL_CHECKS else warnings).append(message)

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Validation failed for {extracted.title}: {errors}")

    cleaned = clean_text(extracted.raw_text) if is_valid else extracted.raw_text

    return ValidatedPaper(
        paper_id=extracted.paper_id,
        title=extracted.title,
        authors=extracted.authors,
        abstract=extracted.abstract,
        clean_text=cleaned,
        validation=ValidationResult(
            is_valid=is_valid,
            checks=checks,
            warnings=warnings,
            errors=errors,
        ),
        status=ProcessingStatus.VALIDATED if is_valid else ProcessingStatus.FAILED,
    )


def process_extracted_papers(input_dir: str = "data/extracted_papers") -> None:
    """Batch-validate all extracted papers."""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return

    json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    logger.info(f"Found {len(json_files)} extracted papers to validate")

    valid_count = 0
    for json_file in json_files:
        input_path = os.path.join(input_dir, json_file)
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            extracted = ExtractedPaper(**data)
            result = validate_paper(extracted)

            output_path = os.path.join(Config.OUTPUT_DIR, json_file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))

            if result.validation.is_valid:
                valid_count += 1
            logger.info(f"{'PASS' if result.validation.is_valid else 'FAIL'}: {extracted.title}")
        except Exception as e:
            logger.error(f"Failed to validate {json_file}: {e}")

    logger.info(f"Validation complete: {valid_count}/{len(json_files)} passed")


if __name__ == "__main__":
    process_extracted_papers()
