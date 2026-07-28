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
    assert "karma-integrity" in response.text
    assert "central-depository" in response.text
    assert "JSON.stringify(output, null, 2)" in response.text
    assert 'data-request="Show AAPL stock"' in response.text
    assert 'data-request="Distance of Earth from Sun"' in response.text
    assert 'data-request="Show low-stock inventory"' in response.text
