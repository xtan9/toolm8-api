import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models import CSVImportResponse
from app.services.csv_importer import CSVImporter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_stats() -> dict[str, str]:
    return {"message": "Admin stats endpoint - implement as needed"}


@router.post("/import-csv", response_model=CSVImportResponse)
async def import_tools_from_csv(
    file: UploadFile = File(
        ..., description="CSV file with theresanaiforthat.com scraping results"
    ),
    replace_existing: bool = Form(
        False, description="Whether to replace existing tools with same slug"
    ),
) -> CSVImportResponse:
    """
    Import AI tools from theresanaiforthat.com CSV scraping results.

    Expected CSV format:
    - Must contain columns: ai_link, task_label, external_ai_link href, etc.
    - Based on theresanaiforthat.com website structure

    Args:
        file: CSV file upload
        replace_existing: Whether to update existing tools or skip them

    Returns:
        Import results with counts and status
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    # Check file size (limit to 100MB)
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 100MB")

    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode("utf-8")

        logger.info(f"Processing CSV file: {file.filename} ({len(csv_content)} characters)")

        # Import using CSV importer service
        importer = CSVImporter()
        results = await importer.import_from_csv_content(csv_content, replace_existing)

        logger.info(f"CSV import completed: {results}")

        return CSVImportResponse(**results)

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        logger.error(f"Error processing CSV upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")
