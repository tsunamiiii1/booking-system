from flask import Flask, render_template, request, jsonify
import json
import os
from flight_manager import load_flights, save_flights

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

def save_booking_web(flight_number, destination, seat):
    try:
        with open(BOOKED_FILE, "a") as f:
            f.write(f"{flight_number} - {destination}: {seat}\n")
        return True
    except Exception as e:
        print(f"Error saving booking: {e}")
        return False

@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.get_json()
    flight_number = data['flightNumber']
    seat = data['seat']
    
    flights = load_flights()
    
    if flight_number not in flights or seat not in flights[flight_number]['seats']:
        return jsonify({'success': False, 'error': 'Invalid flight or seat'})
    
    # Remove seat from available seats
    flights[flight_number]['seats'].remove(seat)
    save_flights(flights)
    
    # Save booking
    destination = flights[flight_number]['destination']
    success = save_booking_web(flight_number, destination, seat)
    
    if success:
        return jsonify({'success': True})
    else:
        # Restore seat if booking failed
        flights[flight_number]['seats'].append(seat)
        save_flights(flights)
        return jsonify({'success': False, 'error': 'Booking failed'})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    
    #Basic HTML template
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Flight Management System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .seat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            max-width: 300px;
        }
        .seat {
            border: 2px solid #d1d5db;
            padding: 10px;
            text-align: center;
            cursor: pointer;
            border-radius: 5px;
        }
        .seat:hover {
            border-color: #3b82f6;
        }
        .seat.selected {
            background-color: #3b82f6;
            color: white;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto py-8">
        <h1 class="text-3xl font-bold mb-6">Available Flights</h1>
        <div id="flightsList"></div>
        <div id="seatSelection" class="hidden"></div>
    </div>

    <script>
        let currentFlight = null;
        let currentSeat = null;

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
                        <button onclick="selectFlight('${flightNumber}')" 
                                class="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
                            Select Flight
                        </button>
                    </div>
                `;
                container.innerHTML += flightCard;
            }
        }

        function selectFlight(flightNumber) {
            currentFlight = flightNumber;
            
            fetch('/api/flights')
                .then(response => response.json())
                .then(flights => {
                    const flight = flights[flightNumber];
                    
                    document.getElementById('flightsList').classList.add('hidden');
                    const seatDiv = document.getElementById('seatSelection');
                    seatDiv.classList.remove('hidden');
                    
                    seatDiv.innerHTML = `
                        <h2 class="text-2xl font-bold mb-4">Select Seat for ${flightNumber}</h2>
                        <p class="text-gray-600 mb-4">${flight.destination}</p>
                        <div class="seat-grid mb-4">
                            ${flight.seats.map(seat => `
                                <div class="seat" onclick="selectSeat('${seat}')">
                                    ${seat}
                                </div>
                            `).join('')}
                        </div>
                        <div id="seatActions" class="hidden">
                            <p>Selected: <span id="selectedSeat"></span></p>
                            <button onclick="bookSeat()" class="bg-green-500 text-white px-4 py-2 rounded">
                                Book This Seat
                            </button>
                        </div>
                        <button onclick="showFlights()" class="mt-4 bg-gray-500 text-white px-4 py-2 rounded">
                            Back to Flights
                        </button>
                    `;
                });
        }

        function selectSeat(seat) {
            currentSeat = seat;
            document.querySelectorAll('.seat').forEach(s => s.classList.remove('selected'));
            event.target.classList.add('selected');
            
            document.getElementById('seatActions').classList.remove('hidden');
            document.getElementById('selectedSeat').textContent = seat;
        }

        function showFlights() {
            document.getElementById('flightsList').classList.remove('hidden');
            document.getElementById('seatSelection').classList.add('hidden');
        }

        async function bookSeat() {
            const response = await fetch('/api/book', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    flightNumber: currentFlight,
                    seat: currentSeat
                })
            });
            
            const result = await response.json();
            if (result.success) {
                alert('Booking successful!');
                showFlights();
                loadFlights();
            } else {
                alert('Booking failed: ' + result.error);
            }
        }
        
        loadFlights();
    </script>
</body>
</html>""")
    
    app.run(debug=True, port=5000)