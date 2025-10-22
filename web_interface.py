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

def load_bookings_web():
    bookings = []
    try:
        with open(BOOKED_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                booking = {"raw_line": line}
                
                if ":" in line:
                    flight_info, seat = line.split(":")
                    flight_number, destination = flight_info.split(" - ")
                    booking.update({
                        "flightNumber": flight_number.strip(),
                        "destination": destination.strip(),
                        "seat": seat.strip()
                    })
                
                bookings.append(booking)
                
    except FileNotFoundError:
        pass
        
    return bookings

@app.route('/api/bookings')
def api_bookings():
    bookings = load_bookings_web()
    return jsonify(bookings)

@app.route('/api/cancel-booking', methods=['POST'])
def api_cancel_booking():
    data = request.get_json()
    booking_index = data['bookingIndex']
    
    bookings = load_bookings_web()
    flights = load_flights()
    
    if booking_index >= len(bookings):
        return jsonify({'success': False, 'error': 'Invalid booking'})
    
    booking = bookings[booking_index]
    
    # Add seat back to available seats
    if booking['flightNumber'] in flights:
        flights[booking['flightNumber']]['seats'].append(booking['seat'])
        flights[booking['flightNumber']]['seats'].sort()
    
    # Remove booking by rewriting the file without this booking
    try:
        with open(BOOKED_FILE, "r") as f:
            all_lines = f.readlines()
        
        # Remove the specific line
        if 0 <= booking_index < len(all_lines):
            all_lines.pop(booking_index)
            
        with open(BOOKED_FILE, "w") as f:
            f.writelines(all_lines)
            
        save_flights(flights)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
        .tab-button {
            padding: 12px 24px;
            border: none;
            background: none;
            cursor: pointer;
        }
        .tab-button.active {
            border-bottom: 2px solid #3b82f6;
            color: #3b82f6;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto py-8">
        <h1 class="text-3xl font-bold mb-6">Flight Management System</h1>
        
        <div class="bg-white rounded-lg shadow border">
            <div class="border-b">
                <button id="bookTab" class="tab-button active" onclick="showTab('book')">
                    Book Flight
                </button>
                <button id="manageTab" class="tab-button" onclick="showTab('manage')">
                    My Bookings
                </button>
            </div>
            
            <div id="bookContent" class="p-6">
                <div id="flightsList"></div>
                <div id="seatSelection" class="hidden"></div>
            </div>
            
            <div id="manageContent" class="p-6 hidden">
                <h2 class="text-xl font-semibold mb-4">My Bookings</h2>
                <div id="bookingsList"></div>
            </div>
        </div>
    </div>

    <script>
        let currentFlight = null;
        let currentSeat = null;

        function showTab(tabName) {
            // Hide all content
            document.getElementById('bookContent').classList.add('hidden');
            document.getElementById('manageContent').classList.add('hidden');
            
            // Remove active styles
            document.querySelectorAll('.tab-button').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected content
            document.getElementById(tabName + 'Content').classList.remove('hidden');
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            if (tabName === 'manage') {
                loadBookings();
            }
        }

        async function loadFlights() {
            const response = await fetch('/api/flights');
            const flights = await response.json();
            
            const container = document.getElementById('flightsList');
            container.innerHTML = '<h2 class="text-xl font-semibold mb-4">Available Flights</h2>';
            
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
            loadFlights();
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

        async function loadBookings() {
            const response = await fetch('/api/bookings');
            const bookings = await response.json();
            
            const container = document.getElementById('bookingsList');
            
            if (bookings.length === 0) {
                container.innerHTML = '<p class="text-gray-500">No bookings found.</p>';
                return;
            }
            
            container.innerHTML = bookings.map((booking, index) => `
                <div class="bg-white border rounded-lg p-4 mb-4">
                    <h3 class="text-lg font-semibold">${booking.flightNumber}</h3>
                    <p class="text-gray-600">${booking.destination} - Seat ${booking.seat}</p>
                    <button onclick="cancelBooking(${index})" 
                            class="mt-2 bg-red-500 text-white px-4 py-2 rounded">
                        Cancel Booking
                    </button>
                </div>
            `).join('');
        }

        async function cancelBooking(bookingIndex) {
            if (confirm('Are you sure you want to cancel this booking?')) {
                const response = await fetch('/api/cancel-booking', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ bookingIndex: bookingIndex })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Booking cancelled successfully!');
                    loadBookings();
                } else {
                    alert('Cancellation failed: ' + result.error);
                }
            }
        }
        
        loadFlights();
    </script>
</body>
</html>""")
    
    app.run(debug=True, port=5000)