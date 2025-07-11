document.addEventListener('DOMContentLoaded', () => {
    // The base URL for the API remains the same.
    const API_BASE_URL = 'https://api.snelapi.nl';

    // --- Helper function to perform API calls ---
    async function callApi(endpoint, method = 'GET', body = null) {
        // --- FIX: Prepend all endpoint paths with /v1 ---
        const url = `${API_BASE_URL}/v1${endpoint}`;
        
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();

            if (!response.ok) {
                return { error: true, status: response.status, data };
            }
            return { error: false, data };
        } catch (err) {
            return { error: true, status: 'Network Error', data: { detail: err.message } };
        }
    }
    
    // --- Helper function to display results ---
    function displayResult(element, result) {
        element.textContent = JSON.stringify(result.data, null, 2);
        element.classList.remove('success', 'error');
        if (result.error) {
            element.classList.add('error');
        } else {
            element.classList.add('success');
        }
    }
    
    // --- IBAN Validator ---
    const btnIban = document.getElementById('btn-validate-iban');
    if (btnIban) {
        const inputIban = document.getElementById('iban-input');
        const responseIban = document.getElementById('iban-response').querySelector('code');

        btnIban.addEventListener('click', async () => {
            const iban = inputIban.value;
            if (!iban) {
                responseIban.textContent = 'Please enter an IBAN.';
                return;
            }
            responseIban.textContent = 'Calling API...';
            // The endpoint path itself is correct; the helper function adds /v1
            const result = await callApi(`/iban/validate?code=${encodeURIComponent(iban)}`);
            displayResult(responseIban, result);
        });
    }

    // --- KvK Validator ---
    const btnKvk = document.getElementById('btn-validate-kvk');
    if (btnKvk) {
        const inputKvk = document.getElementById('kvk-input');
        const responseKvk = document.getElementById('kvk-response').querySelector('code');

        btnKvk.addEventListener('click', async () => {
            const kvk = inputKvk.value;
            if (!kvk) {
                responseKvk.textContent = 'Please enter a KvK number.';
                return;
            }
            responseKvk.textContent = 'Calling API...';
            const result = await callApi(`/kvk/validate?number=${encodeURIComponent(kvk)}`);
            displayResult(responseKvk, result);
        });
    }

    // --- Anomaly Detector ---
    const btnAnomaly = document.getElementById('btn-detect-anomaly');
    if (btnAnomaly) {
        const inputAnomaly = document.getElementById('anomaly-input');
        const responseAnomaly = document.getElementById('anomaly-response').querySelector('code');

        btnAnomaly.addEventListener('click', async () => {
            const rawValues = inputAnomaly.value;
            if (!rawValues) {
                responseAnomaly.textContent = 'Please enter data values.';
                return;
            }
            const values = rawValues.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
            if (values.length === 0) {
                responseAnomaly.textContent = 'Please enter valid, comma-separated numbers.';
                return;
            }
            responseAnomaly.textContent = 'Calling API...';
            const body = { values: values };
            const result = await callApi('/anomaly/detect', 'POST', body);
            displayResult(responseAnomaly, result);
        });
    }

    // --- Add Metrics ---
    const btnAddMetrics = document.getElementById('btn-add-metrics');
    if (btnAddMetrics) {
        const inputValue1 = document.getElementById('value1-input');
        const inputValue2 = document.getElementById('value2-input');
        const responseAddMetrics = document.getElementById('add-metrics-response').querySelector('code');

        btnAddMetrics.addEventListener('click', async () => {
            const value1 = parseFloat(inputValue1.value);
            const value2 = parseFloat(inputValue2.value);
            if (isNaN(value1) || isNaN(value2)) {
                responseAddMetrics.textContent = 'Please enter valid numbers for both values.';
                return;
            }
            responseAddMetrics.textContent = 'Calling API...';
            const body = { value1, value2 };
            const result = await callApi('/normalizer/addmetrics', 'POST', body);
            displayResult(responseAddMetrics, result);
        });
    }
});