from backend.models.consent import CookieConsent


def test_cookie_consent_recording(client):
    payload = {
        "consent_uuid": "test-uuid-12345",
        "essential": True,
        "analytics": True,
        "marketing": False,
        "version": "1.0",
    }
    response = client.post("/api/cookie-consent", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["preferences"]["analytics"] is True
    assert data["preferences"]["marketing"] is False

    # Check persistence in database
    consent = CookieConsent.query.filter_by(consent_uuid="test-uuid-12345").first()
    assert consent is not None
    assert consent.essential is True
    assert consent.analytics is True
    assert consent.marketing is False
