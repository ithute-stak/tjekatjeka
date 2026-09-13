import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_quote_converts_to_customer_invoice():
    suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        branches = client.get("/api/v1/branches").json()
        customer = client.post("/api/v1/customers", json={"name": f"Enterprise Customer {suffix}", "phone": None, "email": None})
        assert customer.status_code == 201
        customer_id = customer.json()["id"]
        quote_no = f"Q-{suffix}"
        created = client.post(
            "/api/v1/quotes",
            json={
                "branch_id": branches[0]["id"] if branches else None,
                "customer_id": customer_id,
                "quote_no": quote_no,
                "description": "Supply and deliver blocks",
                "tax_amount": 50,
                "lines": [
                    {"description": "6-inch blocks", "quantity": 100, "unit": "each", "unit_price": 8.5},
                    {"description": "Delivery", "quantity": 1, "unit": "trip", "unit_price": 300},
                ],
            },
        )
        assert created.status_code == 201
        assert float(created.json()["total_amount"]) == 1200.0
        quote_id = created.json()["id"]
        accepted = client.patch(f"/api/v1/quotes/{quote_id}", json={"status": "accepted"})
        assert accepted.status_code == 200
        converted = client.post(f"/api/v1/quotes/{quote_id}/convert", json={"invoice_no": f"INV-{suffix}", "due_date": None})
        assert converted.status_code == 200
        assert converted.json()["quote"]["status"] == "converted"
        assert float(converted.json()["invoice"]["amount"]) == 1200.0


def test_double_entry_journal_rejects_unbalanced_posting():
    suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        accounts = client.get("/api/v1/ledger-accounts").json()
        assert len(accounts) >= 2
        balanced = client.post(
            "/api/v1/journals",
            json={
                "reference": f"JNL-{suffix}",
                "description": "Control test",
                "lines": [
                    {"account_id": accounts[0]["id"], "debit": 100, "credit": 0, "memo": "Debit"},
                    {"account_id": accounts[1]["id"], "debit": 0, "credit": 100, "memo": "Credit"},
                ],
            },
        )
        assert balanced.status_code == 201
        unbalanced = client.post(
            "/api/v1/journals",
            json={
                "reference": f"BAD-{suffix}",
                "description": "Must fail",
                "lines": [
                    {"account_id": accounts[0]["id"], "debit": 100, "credit": 0},
                    {"account_id": accounts[1]["id"], "debit": 0, "credit": 90},
                ],
            },
        )
        assert unbalanced.status_code == 422
        trial = client.get("/api/v1/trial-balance")
        assert trial.status_code == 200
        assert trial.json()["balanced"] is True


def test_payroll_cannot_approve_before_governance_decision():
    suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        employee = client.post(
            "/api/v1/employees",
            json={
                "employee_no": f"EMP-{suffix}",
                "full_name": "Payroll Test Employee",
                "job_title": "Operator",
                "basic_salary": 5000,
                "hired_date": "2026-09-01",
            },
        )
        assert employee.status_code == 201
        run = client.post(
            "/api/v1/payroll-runs",
            json={
                "period_label": f"Test-{suffix}",
                "pay_date": "2026-09-30",
                "payslips": [{"employee_id": employee.json()["id"], "allowances": 250, "deductions": 100, "notes": "Test"}],
            },
        )
        assert run.status_code == 201
        run_id = run.json()["id"]
        approval_id = run.json()["approval_id"]
        blocked = client.patch(f"/api/v1/payroll-runs/{run_id}", json={"status": "approved"})
        assert blocked.status_code == 409
        decision = client.patch(f"/api/v1/approvals/{approval_id}", json={"status": "approved", "decision_note": "Checked"})
        assert decision.status_code == 200
        approved = client.patch(f"/api/v1/payroll-runs/{run_id}", json={"status": "approved"})
        assert approved.status_code == 200
        paid = client.patch(f"/api/v1/payroll-runs/{run_id}", json={"status": "paid"})
        assert paid.status_code == 200


def test_document_upload_and_download_round_trip():
    suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        uploaded = client.post(
            "/api/v1/documents/upload",
            data={"entity_type": "test", "title": f"Receipt-{suffix}.txt", "document_type": "receipt"},
            files={"file": ("receipt.txt", b"tjekatjeka enterprise document", "text/plain")},
        )
        assert uploaded.status_code == 201
        document_id = uploaded.json()["id"]
        downloaded = client.get(f"/api/v1/documents/{document_id}/download")
        assert downloaded.status_code == 200
        assert downloaded.content == b"tjekatjeka enterprise document"
