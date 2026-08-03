from fastapi.testclient import TestClient

from mitra_companion.api import create_app


def test_workflow_console_exposes_live_execution_surface(settings_factory):
    settings = settings_factory()

    with TestClient(create_app(settings, start_runtime=False)) as client:
        response = client.get("/workflow-console")

    assert response.status_code == 200
    assert "Watch a request move through the ecosystem" in response.text
    assert "/api/v1/ecosystem/execute" in response.text
    assert "/api/v1/ecosystem/executions?limit=50" in response.text
    assert "/recover" in response.text
    assert "Resuming from checkpoint after hosting timeout" in response.text
    assert "RECOVERY_STALE_AFTER_MS = 330000" in response.text
    assert "currentStage?.started_at" in response.text
    assert "universal-capability-runtime" in response.text
    assert "replay-validation" in response.text
    assert '"user-request", "Natural request", "User"' in response.text
    assert '"mitra-response", "Companion response", "MITRA"' in response.text
    assert "MITRA Companion" in response.text
    assert "JSON.stringify(output, null, 2)" in response.text
    assert 'data-request="Show AAPL stock"' in response.text
    assert 'data-request="Distance of Earth from Sun"' in response.text
    assert 'data-request="Show low-stock inventory"' in response.text
    assert "Raj Control Plane" in response.text
    assert "TANTRA Runtime" in response.text
    assert "Hands selected capability to Raj" in response.text
    assert "Universal Runtime -> Capability -> Bucket -> Replay -> InsightFlow" in response.text
