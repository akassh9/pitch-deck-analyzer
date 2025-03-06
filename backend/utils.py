from .config import Config
from .utils.text_processing import (
    is_noise_page,
    advanced_fix_spaced_text,
    fix_spaced_text,
    remove_noise,
    insert_line_breaks,
    clean_text,
    needs_ocr,
    ocr_page,
    prepare_text,
    refine_text_with_stage
)

DEBUG_LOGGING = Config.DEBUG_LOGGING