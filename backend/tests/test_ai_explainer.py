from app.services.ai_explainer import _get_output_text, _safe_results_for_prompt


def test_responses_parser_collects_text_from_message_blocks() -> None:
    response = {
        "output": [
            {"type": "reasoning", "summary": []},
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": "Reja"},
                    {"type": "output_text", "text": " izohi"},
                ],
            },
        ]
    }

    assert _get_output_text(response) == "Reja izohi"


def test_prompt_data_contains_no_financial_amounts_or_customer_labels() -> None:
    results = {
        "capex": {"equipment_total": 1_000_000, "equipment_items": [
            {"name": "secret supplier/model", "cost": 1_000_000},
        ]},
        "break_even": {"break_even_revenue": 500_000},
        "monthly_opex": {"total": 200_000},
        "annual_taxes": {"profit_tax": 10_000},
        "bank_readiness": {"score": 80, "components": [
            {"key": "capex", "complete": True, "earned": 10, "possible": 10},
        ]},
    }

    safe = _safe_results_for_prompt(results)

    assert safe == {
        "section_availability": {
            "capex": True,
            "operating_costs": True,
            "taxes": True,
            "loan_schedule": False,
            "break_even": True,
            "roi": False,
        },
        "readiness_component_completeness": [
            {"key": "capex", "complete": True},
        ],
    }
    assert "secret supplier/model" not in str(safe)
    assert "1000000" not in str(safe)
