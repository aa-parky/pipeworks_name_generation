"""Static web assets for the syllable walker web interface.

This module contains HTML and CSS templates embedded as Python strings. Assets are
embedded rather than served as separate files to maintain simplicity and avoid
requiring additional file distribution when the package is installed.

The embedded assets provide:
- HTML_TEMPLATE: Complete single-page application interface
- CSS_CONTENT: Full stylesheet for the web interface
"""

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Syllable Walker - Interactive Explorer</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Syllable Walker</h1>
            <p>Explore phonetic feature space through cost-based random walks</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="total-syllables">-</div>
                <div class="stat-label">Total Syllables</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="total-walks">0</div>
                <div class="stat-label">Walks Generated</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="current-profile">-</div>
                <div class="stat-label">Current Profile</div>
            </div>
        </div>

        <div class="content">
            <div class="controls">
                <h2 style="margin-bottom: 20px; color: #212529;">Walk Parameters</h2>

                <div class="control-group">
                    <label for="start-syllable">Starting Syllable</label>
                    <input type="text" id="start-syllable" placeholder="e.g., ka, bak, or leave empty for random">
                    <div class="help-text">Leave empty for a random starting point</div>
                </div>

                <div class="control-group">
                    <label for="profile">Walk Profile</label>
                    <select id="profile">
                        <option value="clerical">Clerical (Conservative)</option>
                        <option value="dialect" selected>Dialect (Balanced)</option>
                        <option value="goblin">Goblin (Chaotic)</option>
                        <option value="ritual">Ritual (Maximum Exploration)</option>
                        <option value="custom">Custom Parameters</option>
                    </select>
                    <div class="profile-info" id="profile-description">
                        Moderate exploration, neutral frequency bias
                    </div>
                </div>

                <div id="custom-params" style="display: none;">
                    <div class="control-group">
                        <label for="steps">Steps</label>
                        <input type="number" id="steps" value="5" min="1" max="20">
                    </div>

                    <div class="control-group">
                        <label for="max-flips">Max Feature Flips</label>
                        <input type="number" id="max-flips" value="2" min="1" max="3">
                        <div class="help-text">Maximum phonetic distance per step</div>
                    </div>

                    <div class="control-group">
                        <label for="temperature">Temperature</label>
                        <input type="number" id="temperature" value="0.7" min="0.1" max="5" step="0.1">
                        <div class="help-text">Higher = more random exploration</div>
                    </div>

                    <div class="control-group">
                        <label for="frequency-weight">Frequency Weight</label>
                        <input type="number" id="frequency-weight" value="0.0" min="-2" max="2" step="0.1">
                        <div class="help-text">Positive favors common, negative favors rare</div>
                    </div>
                </div>

                <div class="control-group">
                    <label for="seed">Random Seed (optional)</label>
                    <input type="number" id="seed" placeholder="Leave empty for random">
                    <div class="help-text">For reproducible walks</div>
                </div>

                <button class="btn" id="generate-btn" onclick="generateWalk()">
                    Generate Walk
                </button>
            </div>

            <div class="results">
                <div id="walk-output">
                    <div class="loading">
                        <p>Click "Generate Walk" to begin exploring</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let walkCount = 0;

        const profileDescriptions = {
            clerical: "Conservative, favors common syllables, minimal phonetic change",
            dialect: "Moderate exploration, neutral frequency bias",
            goblin: "Chaotic, favors rare syllables, high phonetic variation",
            ritual: "Maximum exploration, strongly favors rare syllables",
            custom: "Use custom parameters below"
        };

        const profileParams = {
            clerical: { steps: 5, max_flips: 1, temperature: 0.3, frequency_weight: 1.0 },
            dialect: { steps: 5, max_flips: 2, temperature: 0.7, frequency_weight: 0.0 },
            goblin: { steps: 5, max_flips: 2, temperature: 1.5, frequency_weight: -0.5 },
            ritual: { steps: 5, max_flips: 3, temperature: 2.5, frequency_weight: -1.0 }
        };

        // Load initial stats
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('total-syllables').textContent =
                    data.total_syllables.toLocaleString();
            });

        // Profile change handler
        document.getElementById('profile').addEventListener('change', function() {
            const profile = this.value;
            document.getElementById('profile-description').textContent = profileDescriptions[profile];
            document.getElementById('current-profile').textContent =
                profile.charAt(0).toUpperCase() + profile.slice(1);

            if (profile === 'custom') {
                document.getElementById('custom-params').style.display = 'block';
            } else {
                document.getElementById('custom-params').style.display = 'none';
                const params = profileParams[profile];
                document.getElementById('steps').value = params.steps;
                document.getElementById('max-flips').value = params.max_flips;
                document.getElementById('temperature').value = params.temperature;
                document.getElementById('frequency-weight').value = params.frequency_weight;
            }
        });

        // Initialize profile
        document.getElementById('profile').dispatchEvent(new Event('change'));

        async function generateWalk() {
            const btn = document.getElementById('generate-btn');
            const output = document.getElementById('walk-output');

            btn.disabled = true;
            output.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating walk...</p></div>';

            const params = {
                start: document.getElementById('start-syllable').value || null,
                profile: document.getElementById('profile').value,
                steps: parseInt(document.getElementById('steps').value),
                max_flips: parseInt(document.getElementById('max-flips').value),
                temperature: parseFloat(document.getElementById('temperature').value),
                frequency_weight: parseFloat(document.getElementById('frequency-weight').value),
                seed: document.getElementById('seed').value ? parseInt(document.getElementById('seed').value) : null
            };

            try {
                const response = await fetch('/api/walk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });

                const data = await response.json();

                if (data.error) {
                    output.innerHTML = `<div class="error">${data.error}</div>`;
                } else {
                    displayWalk(data);
                    walkCount++;
                    document.getElementById('total-walks').textContent = walkCount;
                }
            } catch (error) {
                output.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            } finally {
                btn.disabled = false;
            }
        }

        function displayWalk(data) {
            const path = data.walk.map(s => s.syllable).join(' → ');

            let html = `
                <div class="walk-display">
                    <h3 style="margin-bottom: 15px; color: #495057;">Walk Path</h3>
                    <div class="walk-path">${path}</div>
                </div>
                <div class="walk-details">
                    <h3 style="margin-bottom: 15px; color: #495057;">Syllable Details</h3>
            `;

            data.walk.forEach((syllable, idx) => {
                html += `
                    <div class="syllable-card">
                        <div>
                            <span style="color: #6c757d; margin-right: 10px;">${idx + 1}.</span>
                            <span class="syllable-text">${syllable.syllable}</span>
                        </div>
                        <div class="syllable-freq">freq: ${syllable.frequency}</div>
                    </div>
                `;
            });

            html += '</div>';
            document.getElementById('walk-output').innerHTML = html;
        }
    </script>
</body>
</html>
"""

# CSS stylesheet for the web interface
CSS_CONTENT = """/* ========================================
   RESET
   ======================================== */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* ========================================
   BASE
   ======================================== */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #0f1218 0%, #151a23 100%);
    color: #d6d9e0;
    min-height: 100vh;
    padding: 20px;
}

/* ========================================
   CONTAINER
   ======================================== */
.container {
    max-width: 1200px;
    margin: 0 auto;
    background: #1b1f2a;
    border-radius: 12px;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6);
    overflow: hidden;
    border: 1px solid #262b38;
}

/* ========================================
   HEADER
   ======================================== */
.header {
    background: linear-gradient(135deg, #232a3a 0%, #1b2130 100%);
    color: #eef0f4;
    padding: 30px;
    text-align: center;
    border-bottom: 1px solid #2b3142;
}

.header h1 {
    font-size: 2.4em;
    margin-bottom: 10px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.header p {
    font-size: 1.05em;
    color: #b8bcc6;
}

/* ========================================
   STATS BAR
   ======================================== */
.stats {
    display: flex;
    justify-content: space-around;
    background: #161a23;
    padding: 20px;
    border-bottom: 1px solid #262b38;
}

.stat {
    text-align: center;
}

.stat-value {
    font-size: 2em;
    font-weight: 600;
    color: #9aa4ff;
}

.stat-label {
    color: #8c92a3;
    font-size: 0.85em;
    margin-top: 5px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ========================================
   MAIN CONTENT GRID
   ======================================== */
.content {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 30px;
    padding: 30px;
}

/* ========================================
   CONTROLS PANEL
   ======================================== */
.controls {
    background: #161a23;
    padding: 25px;
    border-radius: 8px;
    border: 1px solid #262b38;
    height: fit-content;
}

.control-group {
    margin-bottom: 20px;
}

.control-group label {
    display: block;
    font-weight: 600;
    margin-bottom: 8px;
    color: #cfd3dc;
    font-size: 0.9em;
}

.control-group input,
.control-group select {
    width: 100%;
    padding: 10px;
    background: #0f1218;
    border: 1px solid #2b3142;
    border-radius: 6px;
    font-size: 1em;
    color: #e6e8ee;
    transition: border-color 0.2s, background 0.2s;
}

.control-group input:focus,
.control-group select:focus {
    outline: none;
    border-color: #9aa4ff;
    background: #121623;
}

.control-group .help-text {
    font-size: 0.8em;
    color: #8c92a3;
    margin-top: 6px;
    line-height: 1.4;
}

.profile-info {
    background: #1f2534;
    padding: 15px;
    border-radius: 6px;
    margin-top: 10px;
    font-size: 0.85em;
    color: #cfd3dc;
    border-left: 3px solid #9aa4ff;
}

/* ========================================
   PRIMARY BUTTON
   ======================================== */
.btn {
    width: 100%;
    padding: 15px;
    background: linear-gradient(135deg, #4f5bd5 0%, #6a74ff 100%);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 1.05em;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(106, 116, 255, 0.35);
}

.btn:active {
    transform: translateY(0);
    box-shadow: none;
}

.btn:disabled {
    background: #3a3f52;
    color: #8c92a3;
    cursor: not-allowed;
    box-shadow: none;
}

/* ========================================
   RESULTS
   ======================================== */
.results {
    background: transparent;
}

/* ========================================
   WALK DISPLAY
   ======================================== */
.walk-display {
    background: #161a23;
    padding: 25px;
    border-radius: 8px;
    margin-bottom: 20px;
    border: 1px solid #262b38;
}

.walk-path {
    font-size: 1.4em;
    font-weight: 600;
    color: #eef0f4;
    line-height: 1.8;
    word-wrap: break-word;
}

/* ========================================
   SYLLABLE DETAILS
   ======================================== */
.walk-details {
    margin-top: 20px;
}

.syllable-card {
    background: #1b1f2a;
    padding: 15px;
    margin: 10px 0;
    border-radius: 6px;
    border-left: 3px solid #6a74ff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: transform 0.15s, background 0.15s;
}

.syllable-card:hover {
    transform: translateX(4px);
    background: #20263a;
}

.syllable-text {
    font-size: 1.25em;
    font-weight: 600;
    color: #eef0f4;
}

.syllable-freq {
    background: #6a74ff;
    color: #ffffff;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 600;
}

/* ========================================
   LOADING & SPINNER
   ======================================== */
.loading {
    text-align: center;
    padding: 40px;
    color: #8c92a3;
}

.spinner {
    border: 4px solid #2b3142;
    border-top: 4px solid #6a74ff;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 20px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ========================================
   ERROR STATE
   ======================================== */
.error {
    background: #2a1b1d;
    color: #f2b8bd;
    padding: 15px;
    border-radius: 6px;
    margin: 20px 0;
    border-left: 3px solid #d9534f;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
    .content {
        grid-template-columns: 1fr;
    }

    .stats {
        flex-direction: column;
        gap: 15px;
    }
}
"""
