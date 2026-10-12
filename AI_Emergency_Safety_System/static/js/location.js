/* Shared GPS + Leaflet helpers. Location is never hard-coded. */

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

function gpsErrorMessage(error) {
    if (!error) {
        return "Location could not be determined.";
    }
    if (error.code === 1) {
        return "GPS permission denied. Allow location access in the browser and try again.";
    }
    if (error.code === 2) {
        return "GPS unavailable. Check device location services and try again.";
    }
    if (error.code === 3) {
        return "GPS request timed out. Move to an open area and try again.";
    }
    return error.message || "Location could not be determined.";
}

function requestCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation is not supported by this browser."));
            return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 20000,
            maximumAge: 0
        });
    });
}

function createSafetyMap(elementId) {
    const map = L.map(elementId, { zoomControl: true }).setView([20, 0], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
    return { map, marker: null };
}

function updateMapLocation(mapState, latitude, longitude) {
    const latLng = [latitude, longitude];
    mapState.map.setView(latLng, 16);
    const googleUrl = `https://www.google.com/maps?q=${latitude},${longitude}`;
    const osmUrl = `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=16/${latitude}/${longitude}`;
    const popupHtml = `
        <strong>Your current location</strong><br>
        ${latitude.toFixed(6)}, ${longitude.toFixed(6)}<br>
        <a href="${googleUrl}" target="_blank" rel="noopener">Open in Google Maps</a><br>
        <a href="${osmUrl}" target="_blank" rel="noopener">Open in OpenStreetMap</a>
    `;
    if (mapState.marker) {
        mapState.marker.setLatLng(latLng);
        mapState.marker.setPopupContent(popupHtml);
    } else {
        mapState.marker = L.marker(latLng).addTo(mapState.map);
        mapState.marker.bindPopup(popupHtml);
    }
    mapState.marker.openPopup();
    return { googleUrl, osmUrl };
}

function fillLocationFields(latitude, longitude, googleUrl) {
    const latEl = document.getElementById("latValue");
    const lngEl = document.getElementById("lngValue");
    const linkEl = document.getElementById("mapLinkValue");
    if (latEl) latEl.textContent = latitude.toFixed(6);
    if (lngEl) lngEl.textContent = longitude.toFixed(6);
    if (linkEl) {
        linkEl.innerHTML = `<a href="${googleUrl}" target="_blank" rel="noopener">Open location</a>`;
    }
}
