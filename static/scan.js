let html5QrcodeScanner;  // Declare globally to clear properly

// This function is called when QR Code is successfully scanned
function onScanSuccess(decodedText) {
    // Stop scanning after success
    if (html5QrcodeScanner) {
        html5QrcodeScanner.clear();
    }

    // Post scanned data to Django backend for verification
    fetch('/process_scan/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token  // csrf_token must be provided from the HTML template
        },
        body: 'scanned_data=' + encodeURIComponent(decodedText)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('scan-result').innerHTML = 'Participant Successfully Registered';
            document.getElementById('success-audio').play();
        } else if (data.status === 'info') {
            document.getElementById('scan-result').innerHTML = 'Participant Successfully Registered'; // Same message for info
            document.getElementById('success-audio').play();
        } else if (data.status === 'already_checked_in') {
            document.getElementById('scan-result').innerHTML = 'Participant already checked-in';
            document.getElementById('error-audio').play(); // Using error audio for this case
        } else {
            document.getElementById('scan-result').innerHTML = 'Participant not found in registered list';
            document.getElementById('error-audio').play();
        }
        // Reload the page after 3 seconds to allow next scan
        setTimeout(() => location.reload(), 3000);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('scan-result').innerHTML = 'An error occurred. Please try again.';
        document.getElementById('error-audio').play();
        setTimeout(() => location.reload(), 3000);
    });
}

// This function initializes the QR scanner
function startScanner() {
    html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", { fps: 10, qrbox: 250 }
    );
    html5QrcodeScanner.render(onScanSuccess);
}

// Automatically start scanner when page loads
document.addEventListener("DOMContentLoaded", function() {
    startScanner();
});