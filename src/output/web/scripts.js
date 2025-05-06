// Configuration
const UPDATE_INTERVAL = 1000; // milliseconds
const MAX_POINTS = 50; // maximum number of points to display on charts
let lastFetchSuccessful = false;

// State colors
const COLORS = {
    neutral: '#95a5a6',
    is_chill: '#2ecc71',
    is_beast_mode: '#f39c12',
    is_dizzy: '#e74c3c'
};

// Chart instances
let charts = {};

// Initialize charts when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document loaded, setting up charts...");
    
    // Create debug info element if it doesn't exist
    if (!document.getElementById('debug-info')) {
        const footer = document.querySelector('footer');
        const debugDiv = document.createElement('div');
        debugDiv.id = 'debug-info';
        debugDiv.style.marginTop = '10px';
        debugDiv.style.fontSize = '12px';
        debugDiv.style.color = '#777';
        footer.appendChild(debugDiv);
    }
    
    // Set up charts
    setupCharts();
    
    // Start data polling
    fetchDataAndUpdate();
    setInterval(fetchDataAndUpdate, UPDATE_INTERVAL);
});

function setupCharts() {
    try {
        console.log("Setting up charts...");
        // Heart Rate Chart
        charts.heartRate = new Chart(
            document.getElementById('heartRateChart'),
            {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Heart Rate (bpm)',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)',
                        borderColor: 'rgba(52, 152, 219, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        data: []
                    }]
                },
                options: getChartOptions('Heart Rate (bpm)', 'Time', 'BPM')
            }
        );
        
        // Blood Pressure Chart
        charts.bloodPressure = new Chart(
            document.getElementById('bloodPressureChart'),
            {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Systolic (mmHg)',
                            backgroundColor: 'rgba(231, 76, 60, 0.2)',
                            borderColor: 'rgba(231, 76, 60, 1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            data: []
                        },
                        {
                            label: 'Diastolic (mmHg)',
                            backgroundColor: 'rgba(52, 152, 219, 0.2)',
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            data: []
                        },
                        {
                            label: 'Mean (mmHg)',
                            backgroundColor: 'rgba(46, 204, 113, 0.2)',
                            borderColor: 'rgba(46, 204, 113, 1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            data: []
                        }
                    ]
                },
                options: getChartOptions('Blood Pressure (mmHg)', 'Time', 'mmHg')
            }
        );
        
        // Oxygen Chart
        charts.oxygen = new Chart(
            document.getElementById('oxygenChart'),
            {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Oxygen Saturation (%)',
                        backgroundColor: 'rgba(142, 68, 173, 0.2)',
                        borderColor: 'rgba(142, 68, 173, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        data: []
                    }]
                },
                options: getChartOptions('Oxygen Saturation (%)', 'Time', '%', 90, 100)
            }
        );
        
        // Respiration Chart
        charts.respiration = new Chart(
            document.getElementById('respirationChart'),
            {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Respiratory Rate (breaths/min)',
                        backgroundColor: 'rgba(241, 196, 15, 0.2)',
                        borderColor: 'rgba(241, 196, 15, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        data: []
                    }]
                },
                options: getChartOptions('Respiratory Rate', 'Time', 'breaths/min')
            }
        );
        
        // Cardiac Output Chart
        charts.cardiacOutput = new Chart(
            document.getElementById('cardiacOutputChart'),
            {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Cardiac Output (L/min)',
                        backgroundColor: 'rgba(230, 126, 34, 0.2)',
                        borderColor: 'rgba(230, 126, 34, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        data: []
                    }]
                },
                options: getChartOptions('Cardiac Output', 'Time', 'L/min')
            }
        );
        console.log("Charts set up successfully");
        
        // Update debug info
        const debugElement = document.getElementById('debug-info');
        if (debugElement) {
            debugElement.textContent = "Charts initialized successfully";
        }
    } catch (error) {
        console.error("Error setting up charts:", error);
        const debugElement = document.getElementById('debug-info');
        if (debugElement) {
            debugElement.textContent = `Chart setup error: ${error.message}`;
        }
    }
}

function getChartOptions(title, xLabel, yLabel, yMin = 'auto', yMax = 'auto') {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: title,
                font: {
                    size: 14
                }
            },
            legend: {
                display: true,
                position: 'top',
                labels: {
                    boxWidth: 12,
                    font: {
                        size: 11
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second',
                    displayFormats: {
                        second: 'HH:mm:ss'
                    }
                },
                title: {
                    display: true,
                    text: xLabel
                }
            },
            y: {
                min: yMin,
                max: yMax,
                title: {
                    display: true,
                    text: yLabel
                }
            }
        },
        animation: false,
        elements: {
            line: {
                tension: 0.3 // Smoother curves
            }
        }
    };
}

async function fetchDataAndUpdate() {
    try {
        console.log("Fetching data...");
        
        // Fetch data.json with a cache-busting query parameter
        const timestamp = new Date().getTime();
        const response = await fetch(`data.json?t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch data: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("Data fetched successfully");
        
        // Update the debug info
        const debugElement = document.getElementById('debug-info');
        if (debugElement) {
            const keysFound = Object.keys(data.values || {}).join(', ');
            const pointCount = data.values && data.values.heart_rate 
                ? data.values.heart_rate.length 
                : 0;
            
            debugElement.textContent = `Data keys: ${keysFound} | Points: ${pointCount} | Last fetch: ${new Date().toLocaleTimeString()}`;
        }
        
        if (!data.values || Object.keys(data.values).length === 0) {
            console.warn("No data values found in response");
            if (!lastFetchSuccessful) {
                document.querySelector('#state-text').textContent = "No data available yet. Please wait...";
            }
            return;
        }
        
        updateCharts(data);
        updateMetrics(data);
        updateState(data);
        updateLastUpdateTime(data);
        
        lastFetchSuccessful = true;
        console.log("UI updated successfully");
        
    } catch (error) {
        console.error('Error fetching or updating data:', error);
        const debugElement = document.getElementById('debug-info');
        if (debugElement) {
            debugElement.textContent = `Error: ${error.message} | ${new Date().toLocaleTimeString()}`;
        }
        
        if (!lastFetchSuccessful) {
            document.querySelector('#state-text').textContent = `Error: ${error.message}`;
        }
    }
}

function updateCharts(data) {
    // Convert data to chart format
    if (!data.values) {
        console.warn("No values property in data");
        return;
    }
    
    // Update Heart Rate chart
    if (data.values.heart_rate && data.values.heart_rate.length > 0) {
        const hrData = data.values.heart_rate.slice(-MAX_POINTS).map(point => ({
            x: new Date(point.x * 1000),
            y: point.y
        }));
        charts.heartRate.data.datasets[0].data = hrData;
        charts.heartRate.update();
    }
    
    // Update Blood Pressure chart
    if (data.values.systolic_pressure && data.values.diastolic_pressure && data.values.mean_pressure) {
        charts.bloodPressure.data.datasets[0].data = data.values.systolic_pressure.slice(-MAX_POINTS)
            .map(point => ({ x: new Date(point.x * 1000), y: point.y }));
        charts.bloodPressure.data.datasets[1].data = data.values.diastolic_pressure.slice(-MAX_POINTS)
            .map(point => ({ x: new Date(point.x * 1000), y: point.y }));
        charts.bloodPressure.data.datasets[2].data = data.values.mean_pressure.slice(-MAX_POINTS)
            .map(point => ({ x: new Date(point.x * 1000), y: point.y }));
        charts.bloodPressure.update();
    }
    
    // Update Oxygen Chart
    if (data.values.oxygen_saturation && data.values.oxygen_saturation.length > 0) {
        const o2Data = data.values.oxygen_saturation.slice(-MAX_POINTS).map(point => ({
            x: new Date(point.x * 1000),
            y: point.y
        }));
        charts.oxygen.data.datasets[0].data = o2Data;
        charts.oxygen.update();
    }
    
    // Update Respiration chart
    if (data.values.respiratory_rate && data.values.respiratory_rate.length > 0) {
        const rrData = data.values.respiratory_rate.slice(-MAX_POINTS).map(point => ({
            x: new Date(point.x * 1000),
            y: point.y
        }));
        charts.respiration.data.datasets[0].data = rrData;
        charts.respiration.update();
    }
    
    // Update Cardiac Output chart
    if (data.values.cardiac_output && data.values.cardiac_output.length > 0) {
        const coData = data.values.cardiac_output.slice(-MAX_POINTS).map(point => ({
            x: new Date(point.x * 1000),
            y: point.y
        }));
        charts.cardiacOutput.data.datasets[0].data = coData;
        charts.cardiacOutput.update();
    }
}

function updateMetrics(data) {
    // Update metrics panel with latest values
    if (data.latest_record && data.latest_record.physiological_values) {
        const values = data.latest_record.physiological_values;
        
        // Heart Rate
        if (values.heart_rate !== undefined) {
            document.querySelector('#heart-rate .metric-value').textContent = 
                `${Math.round(values.heart_rate)} bpm`;
        }
        
        // Blood Pressure
        if (values.systolic_pressure !== undefined && values.diastolic_pressure !== undefined) {
            document.querySelector('#blood-pressure .metric-value').textContent = 
                `${Math.round(values.systolic_pressure)}/${Math.round(values.diastolic_pressure)} mmHg`;
        }
        
        // Oxygen Saturation
        if (values.oxygen_saturation !== undefined) {
            document.querySelector('#oxygen-saturation .metric-value').textContent = 
                `${Math.round(values.oxygen_saturation * 100) / 100}%`;
        }
        
        // Respiratory Rate
        if (values.respiratory_rate !== undefined) {
            document.querySelector('#respiratory-rate .metric-value').textContent = 
                `${Math.round(values.respiratory_rate * 10) / 10} breaths/min`;
        }
        
        // Cardiac Output
        if (values.cardiac_output !== undefined) {
            document.querySelector('#cardiac-output .metric-value').textContent = 
                `${Math.round(values.cardiac_output * 10) / 10} L/min`;
        }
        
        // HRV
        if (values.hrv !== undefined) {
            document.querySelector('#hrv .metric-value').textContent = 
                `${Math.round(values.hrv)} ms`;
        }
    }
}

function updateState(data) {
    if (data.current_state) {
        const state = data.current_state.primary_state || 'neutral';
        const description = data.current_state.description || 'Unknown state';
        
        // Update state indicator
        document.querySelector('#state-text').textContent = description;
        
        // Update body class for state-specific styling
        document.body.classList.remove('state-neutral', 'state-is_chill', 'state-is_beast_mode', 'state-is_dizzy');
        document.body.classList.add(`state-${state}`);
    }
}

function updateLastUpdateTime(data) {
    if (data.latest_record && data.latest_record.timestamp) {
        const timestamp = data.latest_record.timestamp;
        const date = new Date(typeof timestamp === 'string' ? Date.parse(timestamp) : timestamp * 1000);
        document.getElementById('update-time').textContent = `Last update: ${date.toLocaleTimeString()}`;
    }
}