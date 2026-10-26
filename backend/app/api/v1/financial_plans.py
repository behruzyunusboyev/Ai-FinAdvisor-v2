"""Authenticated API for deterministic financial plan calculations."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.financial_calculation import (
    FinancialCalculationRequest,
    FinancialCalculationResponse,
)
from app.schemas.business_plan import BusinessPlanExplanation
from app.schemas.financial_export import FinancialExportRequest
from app.services.ai_explainer import AIProviderError, explain_financial_results
from app.services.financial_plan_service import calculate_financial_plan as run_financial_plan
from app.services.readiness_score import calculate_readiness_score
from app.services.financial_exports import build_excel_report, build_pdf_report


router = APIRouter(prefix="/financial-plans", tags=["Financial Plans"])


@router.post(
    "/calculate",
    response_model=FinancialCalculationResponse,
    summary="Calculate a deterministic financial plan",
)
async def calculate_financial_plan(
    payload: FinancialCalculationRequest,
    current_user: User = Depends(get_current_user),
) -> FinancialCalculationResponse:
    """Return traceable financial calculations without sending data to an LLM."""
    del current_user
    try:
        result = run_financial_plan(payload, settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return FinancialCalculationResponse(**result)


@router.post(
    "/explain",
    response_model=BusinessPlanExplanation,
    summary="Explain a deterministic financial plan",
)
async def explain_financial_plan(
    payload: FinancialCalculationRequest,
    current_user: User = Depends(get_current_user),
) -> BusinessPlanExplanation:
    """Generate an Uzbek narrative from engine results, without forwarding inputs."""
    del current_user
    if not settings.OPENAI_API_KEY or not settings.OPENAI_MODEL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI explanation is not configured",
        )
    try:
        results = run_financial_plan(payload, settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    readiness = calculate_readiness_score(
        payload=payload,
        results=results,
        settings=settings,
    )
    results["bank_readiness"] = {
        "score": readiness.score,
        "status": readiness.status,
        "note": readiness.note,
        "components": [component.__dict__ for component in readiness.components],
    }
    try:
        narrative = await explain_financial_results(
            results=results,
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI explanation provider failed",
        ) from exc
    return BusinessPlanExplanation(
        **narrative.model_dump(),
        bank_readiness_score=readiness.score,
        bank_readiness_score_status=readiness.status,
        bank_readiness_score_note=readiness.note,
        bank_readiness_components=[
            component.__dict__ for component in readiness.components
        ],
    )


@router.post(
    "/export/pdf",
    response_class=Response,
    summary="Download the financial plan as PDF",
)
async def export_financial_plan_pdf(
    payload: FinancialExportRequest,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Calculate and return a PDF without persisting the report."""
    del current_user
    try:
        results = run_financial_plan(payload.financial_inputs, settings)
        document = build_pdf_report(
            results,
            business_plan=payload.business_plan,
            risks=payload.risks,
            bank_readiness_score=payload.bank_readiness_score,
            bank_readiness_score_note=payload.bank_readiness_score_note,
            bank_readiness_components=[
                component.model_dump() for component in payload.bank_readiness_components
            ],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return Response(
        content=document,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="finadvisor-report.pdf"'},
    )


@router.post(
    "/export/excel",
    response_class=Response,
    summary="Download the financial plan as Excel",
)
async def export_financial_plan_excel(
    payload: FinancialExportRequest,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Calculate and return an XLSX workbook without persisting the report."""
    del current_user
    try:
        results = run_financial_plan(payload.financial_inputs, settings)
        workbook = build_excel_report(
            results,
            business_plan=payload.business_plan,
            risks=payload.risks,
            bank_readiness_score=payload.bank_readiness_score,
            bank_readiness_score_note=payload.bank_readiness_score_note,
            bank_readiness_components=[
                component.model_dump() for component in payload.bank_readiness_components
            ],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return Response(
        content=workbook,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": 'attachment; filename="finadvisor-report.xlsx"'},
    )
