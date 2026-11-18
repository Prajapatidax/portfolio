/**
 * Cookie Consent Manager
 * Privacy-focused, GDPR/ePrivacy compliant
 */

(function () {
    const STORAGE_KEY = "prajapati_cookie_consent";
    const CONSENT_VERSION = "1.0";
    const GTAG_ID = "G-DZ5K1ZTY4K";

    function getStoredConsent() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            const parsed = JSON.parse(raw);
            if (parsed && parsed.version === CONSENT_VERSION) {
                return parsed;
            }
        } catch (e) {
            console.warn("Could not read cookie consent:", e);
        }
        return null;
    }

    function saveConsent(essential, analytics, marketing) {
        const consentData = {
            version: CONSENT_VERSION,
            timestamp: new Date().toISOString(),
            essential: true,
            analytics: Boolean(analytics),
            marketing: Boolean(marketing),
        };

        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(consentData));
        } catch (e) {
            console.warn("Could not save cookie consent:", e);
        }

        // Apply immediately
        applyConsent(consentData);

        // Hide banner & modal
        hideBanner();
        hideModal();

        // Non-blocking sync to backend
        fetch("/api/cookie-consent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(consentData),
        }).catch(() => {
            // Silently ignore network sync errors
        });
    }

    function applyConsent(consent) {
        if (consent && consent.analytics) {
            loadGoogleAnalytics();
        }
    }

    function loadGoogleAnalytics() {
        if (window.__gtag_loaded) return;
        window.__gtag_loaded = true;

        const script = document.createElement("script");
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${GTAG_ID}`;
        document.head.appendChild(script);

        window.dataLayer = window.dataLayer || [];
        function gtag() {
            window.dataLayer.push(arguments);
        }
        window.gtag = gtag;
        gtag("js", new Date());
        gtag("config", GTAG_ID, { anonymize_ip: true });
    }

    function showBanner() {
        const banner = document.getElementById("cookie-consent-banner");
        if (banner) {
            banner.classList.remove("hidden");
            setTimeout(() => banner.classList.add("show"), 100);
        }
    }

    function hideBanner() {
        const banner = document.getElementById("cookie-consent-banner");
        if (banner) {
            banner.classList.remove("show");
            setTimeout(() => banner.classList.add("hidden"), 400);
        }
    }

    function showModal() {
        const modal = document.getElementById("cookie-consent-modal");
        if (modal) {
            const current = getStoredConsent() || { analytics: false, marketing: false };
            const analyticsCheck = document.getElementById("consent-analytics-toggle");
            const marketingCheck = document.getElementById("consent-marketing-toggle");
            if (analyticsCheck) analyticsCheck.checked = current.analytics;
            if (marketingCheck) marketingCheck.checked = current.marketing;

            modal.classList.remove("hidden");
        }
    }

    function hideModal() {
        const modal = document.getElementById("cookie-consent-modal");
        if (modal) {
            modal.classList.add("hidden");
        }
    }

    // Expose global method for footer link
    window.openCookieSettings = function () {
        showModal();
    };

    document.addEventListener("DOMContentLoaded", () => {
        const consent = getStoredConsent();
        if (!consent) {
            // First visit or updated version
            showBanner();
        } else {
            applyConsent(consent);
        }

        // Button handlers
        const acceptAllBtn = document.getElementById("cookie-accept-all");
        const rejectOptBtn = document.getElementById("cookie-reject-optional");
        const settingsBtn = document.getElementById("cookie-open-settings");
        const saveSettingsBtn = document.getElementById("cookie-save-settings");
        const closeModalBtn = document.getElementById("cookie-close-modal");

        if (acceptAllBtn) {
            acceptAllBtn.addEventListener("click", () => saveConsent(true, true, true));
        }

        if (rejectOptBtn) {
            rejectOptBtn.addEventListener("click", () => saveConsent(true, false, false));
        }

        if (settingsBtn) {
            settingsBtn.addEventListener("click", () => {
                hideBanner();
                showModal();
            });
        }

        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener("click", () => {
                const analytics = document.getElementById("consent-analytics-toggle")?.checked || false;
                const marketing = document.getElementById("consent-marketing-toggle")?.checked || false;
                saveConsent(true, analytics, marketing);
            });
        }

        if (closeModalBtn) {
            closeModalBtn.addEventListener("click", () => {
                hideModal();
                if (!getStoredConsent()) {
                    showBanner();
                }
            });
        }
    });
})();
