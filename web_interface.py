from flask import Flask, render_template, request, jsonify
import json
import os
from flight_manager import load_flights

app = Flask(__name__)

FLIGHTS_FILE = "Flights.txt"
BOOKED_FILE = "BookedFlights.txt"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/flights')
def api_flights():
    flights = load_flights()
    return jsonify(flights)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    # Basic HTML template
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Flight Management System</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto py-8">
        <h1 class="text-3xl font-bold mb-6">Available Flights</h1>
        <div id="flightsList"></div>
    </div>

    <script>
        async function loadFlights() {
            const response = await fetch('/api/flights');
            const flights = await response.json();
            
            const container = document.getElementById('flightsList');
            container.innerHTML = '';
            
            for (const [flightNumber, info] of Object.entries(flights)) {
                const flightCard = `
                    <div class="bg-white border rounded-lg p-4 mb-4">
                        <h3 class="text-lg font-semibold">${flightNumber}</h3>
                        <p class="text-gray-600">${info.destination}</p>
                        <p class="text-sm text-gray-500">
                            ${info.seats.length} seats available
                        </p>
                    </div>
                `;
                container.innerHTML += flightCard;
            }
        }
        
        loadFlights();
    </script>
</body>
</html>""")
    
    app.run(debug=True, port=5000)