// static/history_charts.js

const cpuHistoryChartCtx = document.getElementById('cpuHistoryChart').getContext('2d');
new Chart(cpuHistoryChartCtx, {
    type: 'line',
    data: {
        
        labels: historyData.timestamps,
        datasets: [{
            label: 'CPU (%)',
            data: historyData.cpu_percents,
            borderColor: 'red',
            backgroundColor: 'rgba(255, 0, 0, 0.2)',
            fill: true,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, max: 100, title: { display: true, text: 'Kullanım (%)' } },
            x: { title: { display: true, text: 'Zaman Damgası' },
                 ticks: {
                 maxRotation: 45, 
                 minRotation: 45,
            } }
        },
        plugins: { legend: { display: true }, title: { display: true, text: 'CPU Kullanım Geçmişi' } }
    }
});

const ramHistoryChartCtx = document.getElementById('ramHistoryChart').getContext('2d');
new Chart(ramHistoryChartCtx, {
    type: 'line',
    data: {
        labels: historyData.timestamps,
        datasets: [{
            label: 'RAM (%)',
            data: historyData.ram_percents,
            borderColor: 'blue',
            backgroundColor: 'rgba(0, 0, 255, 0.2)',
            fill: true,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, max: 100, title: { display: true, text: 'Kullanım (%)' } },
            x: { title: { display: true, text: 'Zaman Damgası' } }
        },
        plugins: { legend: { display: true }, title: { display: true, text: 'RAM Kullanım Geçmişi' } }
    }
});

const diskHistoryChartCtx = document.getElementById('diskHistoryChart').getContext('2d');
new Chart(diskHistoryChartCtx, {
    type: 'line',
    data: {
        labels: historyData.timestamps,
        datasets: [{
            label: 'Disk (%)',
            data: historyData.disk_percents,
            borderColor: 'green',
            backgroundColor: 'rgba(0, 255, 0, 0.2)',
            fill: true,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, max: 100, title: { display: true, text: 'Kullanım (%)' } },
            x: { title: { display: true, text: 'Zaman Damgası' } }
        },
        plugins: { legend: { display: true }, title: { display: true, text: 'Disk Kullanım Geçmişi' } }
    }
});

// Anomali Sıklığı Grafikleri
const hourlyAnomalyChartCtx = document.getElementById('hourlyAnomalyTrendChart').getContext('2d');
new Chart(hourlyAnomalyChartCtx, {
    type: 'bar',
    data: {
        labels: hourlyAnomalyData.labels,
        datasets: [{
            label: 'Anomali Sayısı',
            data: hourlyAnomalyData.counts,
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, title: { display: true, text: 'Anomali Sayısı' } },
            x: { title: { display: true, text: 'Saat' } }
        },
        plugins: { legend: { display: true, position: 'top' }, title: { display: true, text: 'Son 24 Saatteki Anomaliler' } }
    }
});

const dailyAnomalyChartCtx = document.getElementById('dailyAnomalyTrendChart').getContext('2d');
new Chart(dailyAnomalyChartCtx, {
    type: 'line',
    data: {
        labels: dailyAnomalyData.labels,
        datasets: [{
            label: 'Anomali Sayısı',
            data: dailyAnomalyData.counts,
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            fill: false
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, title: { display: true, text: 'Anomali Sayısı' } },
            x: { title: { display: true, text: 'Tarih' } }
        },
        plugins: { legend: { display: true, position: 'top' }, title: { display: true, text: 'Son 7 Gündeki Anomaliler' } }
    }
});