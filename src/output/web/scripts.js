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
                options: getChartOptions('Oxygen Saturation (%)', 'Time', '%', 0, 100)
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
        
        // Recovery Progress Chart (if element exists)
        if (document.getElementById('recoveryProgressChart')) {
            charts.recoveryProgress = new Chart(
                document.getElementById('recoveryProgressChart'),
                {
                    type: 'line',
                    data: {
                        datasets: [{
                            label: 'Recovery Progress (%)',
                            backgroundColor: 'rgba(46, 204, 113, 0.2)',
                            borderColor: 'rgba(46, 204, 113, 1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            data: []
                        }]
                    },
                    options: getChartOptions('Recovery Progress', 'Time', '%', 0, 100)
                }
            );
        }
        
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
        updateRecoveryStatus(data); // New function for recovery status
        
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
    
    // Update Recovery Progress chart if it exists
    if (charts.recoveryProgress && data.values.recovery_progress && data.values.recovery_progress.length > 0) {
        const recoveryData = data.values.recovery_progress.slice(-MAX_POINTS).map(point => ({
            x: new Date(point.x * 1000),
            y: point.y * 100 // Convert to percentage
        }));
        charts.recoveryProgress.data.datasets[0].data = recoveryData;
        charts.recoveryProgress.update();
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
        const description = data.current_state.state_description || 'Unknown state';
        
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

// New function to update recovery status
function updateRecoveryStatus(data) {
    const recoveryPanel = document.getElementById('recovery-panel');
    if (!recoveryPanel) return; // Exit if recovery panel doesn't exist
    
    if (!data.recovery_status || !data.recovery_status.active) {
        recoveryPanel.style.display = 'none';
        return;
    }
    
    // Show recovery panel
    recoveryPanel.style.display = 'block';
    
    // Update progress bar
    const progressPercent = Math.round(data.recovery_status.recovery_progress * 100);
    const progressBar = document.getElementById('recovery-progress-bar');
    const progressText = document.getElementById('recovery-progress-text');
    
    if (progressBar && progressText) {
        progressBar.style.width = `${progressPercent}%`;
        progressText.textContent = `${progressPercent}%`;
    }
    
    // Update severity indicator
    const severity = data.recovery_status.severity;
    const severityIndicator = document.getElementById('severity-indicator');
    const severityText = document.getElementById('severity-text');
    
    if (severityIndicator && severityText) {
        severityIndicator.className = 'severity-indicator ' + 
            (severity < 0.3 ? 'severity-low' : 
             severity < 0.7 ? 'severity-medium' : 'severity-high');
        severityText.textContent = 
            severity < 0.3 ? 'Mild' : 
            severity < 0.7 ? 'Moderate' : 'Severe';
    }
    
    // Update intervention bars
    const interventions = data.recovery_status.interventions || {};
    for (const [key, value] of Object.entries(interventions)) {
        const bar = document.getElementById(`${key}-bar`);
        if (bar) {
            bar.style.width = `${Math.round(value * 100)}%`;
        }
        
        // Update intervention level text if available
        const levelText = document.getElementById(`${key}-level`);
        if (levelText) {
            levelText.textContent = `${Math.round(value * 100)}%`;
        }
    }
    
    // Update elapsed time
    const elapsed = data.recovery_status.elapsed_time || 0;
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const timeElement = document.getElementById('recovery-time');
    
    if (timeElement) {
        timeElement.textContent = `${hours}h ${minutes}m`;
    }
    
    // Update estimated full recovery time
    const estimatedElement = document.getElementById('estimated-recovery');
    if (estimatedElement && progressPercent > 0) {
        const totalEstimatedSeconds = elapsed / (progressPercent / 100);
        const remainingSeconds = totalEstimatedSeconds - elapsed;
        
        const remainingHours = Math.floor(remainingSeconds / 3600);
        const remainingMinutes = Math.floor((remainingSeconds % 3600) / 60);
        
        estimatedElement.textContent = `${remainingHours}h ${remainingMinutes}m remaining`;
    }
}

// Function to toggle recovery interventions (for interactive controls)
function toggleIntervention(interventionType, level) {
    console.log(`Toggling intervention: ${interventionType} to level ${level}`);
    
    // Send an API request to update the intervention
    fetch('/api/intervention', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: interventionType,
            level: level
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update intervention');
        }
        return response.json();
    })
    .then(data => {
        console.log('Intervention updated successfully:', data);
        // Optionally update UI immediately instead of waiting for next fetch
        const bar = document.getElementById(`${interventionType}-bar`);
        if (bar) {
            bar.style.width = `${Math.round(level * 100)}%`;
        }
        
        const levelText = document.getElementById(`${interventionType}-level`);
        if (levelText) {
            levelText.textContent = `${Math.round(level * 100)}%`;
        }
    })
    .catch(error => {
        console.error('Error updating intervention:', error);
    });
}

// Add event listeners for intervention controls if they exist
document.addEventListener('DOMContentLoaded', function() {
    // Setup sliders for interventions
    const interventionSliders = document.querySelectorAll('.intervention-slider');
    interventionSliders.forEach(slider => {
        slider.addEventListener('input', function() {
            const interventionType = this.getAttribute('data-intervention');
            const level = parseFloat(this.value);
            
            // Update the level display
            const levelDisplay = document.querySelector(`#${interventionType}-level`);
            if (levelDisplay) {
                levelDisplay.textContent = `${Math.round(level * 100)}%`;
            }
            
            // Update the bar width
            const bar = document.getElementById(`${interventionType}-bar`);
            if (bar) {
                bar.style.width = `${Math.round(level * 100)}%`;
            }
        });
        
        slider.addEventListener('change', function() {
            const interventionType = this.getAttribute('data-intervention');
            const level = parseFloat(this.value);
            toggleIntervention(interventionType, level);
        });
    });
    
    // Setup start/stop controls for recovery simulation
    const startRecoveryBtn = document.getElementById('start-recovery');
    if (startRecoveryBtn) {
        startRecoveryBtn.addEventListener('click', function() {
            const severity = parseFloat(document.getElementById('severity-slider').value || 0.7);
            
            fetch('/api/recovery/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    severity: severity
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to start recovery simulation');
                }
                return response.json();
            })
            .then(data => {
                console.log('Recovery simulation started:', data);
                document.getElementById('recovery-panel').style.display = 'block';
            })
            .catch(error => {
                console.error('Error starting recovery simulation:', error);
            });
        });
    }
    
    const stopRecoveryBtn = document.getElementById('stop-recovery');
    if (stopRecoveryBtn) {
        stopRecoveryBtn.addEventListener('click', function() {
            fetch('/api/recovery/stop', {
                method: 'POST'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to stop recovery simulation');
                }
                return response.json();
            })
            .then(data => {
                console.log('Recovery simulation stopped:', data);
                document.getElementById('recovery-panel').style.display = 'none';
            })
            .catch(error => {
                console.error('Error stopping recovery simulation:', error);
            });
        });
    }
});