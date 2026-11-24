"""合同归属的 HTTP 入口与证据交付测试。"""


def test_allocate_stage_preview_writes_no_database(client):
    response = client.post(
        "/api/stages/allocate", data={"sample": "contracts_clean"}
    )
    assert response.status_code == 200
    payload = response.json
    assert payload["mode"] == "allocation"
    assert payload["balance"]["releasable"] is True
    assert client.get("/api/runs").json == {"items": []}


def test_allocation_stage_works_for_every_stage_key(client):
    for stage in ["intake", "allocate", "balance"]:
        response = client.post(
            f"/api/stages/{stage}", data={"sample": "contracts_dirty"}
        )
        assert response.status_code == 200


def test_dirty_allocation_sample_is_blocked(client):
    response = client.post("/api/runs", data={"sample": "contracts_dirty"})
    assert response.status_code == 200
    report = response.json["report"]
    assert report["balance"]["releasable"] is False
    statuses = {case["status"] for case in report["cases"]}
    assert {"ASSIGN_OVERLAP", "COVERAGE_GAP"} <= statuses


def test_clean_allocation_run_is_releasable_and_approvable(client):
    run = client.post("/api/runs", data={"sample": "contracts_clean"}).json
    assert run["report"]["balance"]["releasable"] is True
    review = client.patch(
        f"/api/runs/{run['id']}",
        json=dict(revision=0, status="APPROVED", note="归属分摊复核通过"),
    )
    assert review.status_code == 200 and review.json["status"] == "APPROVED"


def test_allocation_evidence_contains_departments_and_reconciliation(client):
    run = client.post("/api/runs", data={"sample": "contracts_clean"}).json
    response = client.get(f"/api/runs/{run['id']}/evidence")
    assert response.status_code == 200
    packet = response.json
    assert packet["schema"] == "review-evidence/1"
    assert packet["mode"] == "allocation"
    assert packet["balance"]["reconcile_delta_cents"] == 0
    ready = next(c for c in packet["cases"] if c["status"] == "READY")
    assert ready["allocation"]["departments"]
    assert ready["allocation"]["seat_results"]


def test_allocation_sample_downloads(client):
    response = client.get("/examples/contracts_clean")
    assert response.status_code == 200
    assert response.data.startswith(b"record,case,kind,")


def test_upload_and_sample_allocation_produce_same_run(client):
    sample = client.post("/api/runs", data={"sample": "contracts_clean"}).json
    from app.config import ROOT

    data = (ROOT / "sample_data" / "contracts_ready.csv").read_bytes()
    import io

    uploaded = client.post(
        "/api/runs", data={"file": (io.BytesIO(data), "contracts.csv")}
    ).json
    assert sample["id"] == uploaded["id"]


def test_bridge_evidence_defaults_mode_to_bridge(client):
    run = client.post("/api/runs", data={"sample": "clean"}).json
    packet = client.get(f"/api/runs/{run['id']}/evidence").json
    assert packet["mode"] == "bridge"
