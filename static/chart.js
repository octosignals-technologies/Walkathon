// chart.js

// Draws a nice small, professional doughnut chart
function drawParticipantChart(registered, checkedIn) {
    const ctx = document.getElementById('participantChart').getContext('2d');
    const participantChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Registered', 'Checked-In'],
            datasets: [{
                data: [registered, checkedIn],
                backgroundColor: ['#000', '#fff'],  // Black and White theme
                borderColor: ['#000', '#fff'],
                borderWidth: 2
            }]
        },
        options: {
            cutout: '80%',  // Bigger center hole (more professional)
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',   // Labels move to bottom
                    labels: {
                        color: '#000',
                        font: {
                            size: 14,
                            family: 'Arial'
                        }
                    }
                }
            }
        }
    });
}