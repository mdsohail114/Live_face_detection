document.addEventListener("DOMContentLoaded", () => {
    const sosButton = document.getElementById("sosButton");
    const loader = document.getElementById("gpsLoader");
    const resultBox = document.getElementById("sosResult");
    const mapEl = document.getElementById("map");
    if (!sosButton || !mapEl) {
        return;
    }

    const mapState = createSafetyMap("map");
    setTimeout(() => mapState.map.invalidateSize(), 200);

    function showLoader(visible) {
        if (!loader) return;
        loader.classList.toggle("d-none", !visible);
    }

    function showResult(html, cssClass) {
        if (!resultBox) return;
        resultBox.className = `alert mt-3 text-start ${cssClass}`;
        resultBox.innerHTML = html;
        resultBox.classList.remove("d-none");
    }

    async function refreshDisplayedLocation() {
        try {
            const position = await requestCurrentPosition();
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            const urls = updateMapLocation(mapState, latitude, longitude);
            fillLocationFields(latitude, longitude, urls.googleUrl);
        } catch (error) {
            fillLocationFieldsFallback(error);
        }
    }

    function fillLocationFieldsFallback(error) {
        const latEl = document.getElementById("latValue");
        const lngEl = document.getElementById("lngValue");
        const message = gpsErrorMessage(error);
        if (latEl) latEl.textContent = message;
        if (lngEl) lngEl.textContent = "Unavailable";
    }

    refreshDisplayedLocation();

    sosButton.addEventListener("click", async () => {
        const confirmed = window.confirm("Are you sure you want to send an emergency alert?");
        if (!confirmed) {
            return;
        }

        sosButton.disabled = true;
        showLoader(true);
        showResult("Requesting your GPS location…", "alert-info");

        let position;
        try {
            position = await requestCurrentPosition();
        } catch (error) {
            showLoader(false);
            sosButton.disabled = false;
            showResult(gpsErrorMessage(error), "alert-danger");
            return;
        }

        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        const urls = updateMapLocation(mapState, latitude, longitude);
        fillLocationFields(latitude, longitude, urls.googleUrl);

        const emergencyType = document.getElementById("emergencyType")?.value || "Other";
        const description = document.getElementById("description")?.value || "";
        const userSeverity = document.getElementById("userSeverity")?.value || "3";

        try {
            const response = await fetch("/sos", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({
                    latitude,
                    longitude,
                    emergency_type: emergencyType,
                    description,
                    user_severity: userSeverity
                })
            });
            const data = await response.json();
            showLoader(false);
            sosButton.disabled = false;

            if (!response.ok || !data.ok) {
                showResult(data.error || "The emergency alert could not be sent.", "alert-danger");
                return;
            }

            const smsNote = data.demo_sms
                ? `<div><strong>SMS:</strong> Demo Mode: SMS service is not configured.</div><div class="small">${escapeHtml(data.sms_status)}</div>`
                : `<div><strong>SMS:</strong> ${escapeHtml(data.sms_status)}</div>`;
            const emailNote = data.demo_email
                ? `<div class="mt-2"><strong>Email:</strong> Demo Mode: Email service is not configured.</div><div class="small">${escapeHtml(data.email_status)}</div>`
                : `<div class="mt-2"><strong>Email:</strong> ${escapeHtml(data.email_status)}</div>`;

            showResult(
                `<div><strong>Alert #${data.alert_id} saved.</strong></div>
                 <div>Assistance risk label: <strong>${escapeHtml(data.risk_level)}</strong></div>
                 <div class="small">${escapeHtml(data.ai_disclaimer || "")}</div>
                 ${smsNote}
                 ${emailNote}
                 <div class="mt-2"><a href="${data.location_url}" target="_blank" rel="noopener">Open location link</a></div>
                 <div class="small mt-2">Refreshing dashboard…</div>`,
                "alert-success"
            );
            setTimeout(() => {
                window.location.reload();
            }, 2500);
        } catch (error) {
            showLoader(false);
            sosButton.disabled = false;
            showResult("The server could not be reached. Please try again.", "alert-danger");
        }
    });
});

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}
