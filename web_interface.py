from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

# Import existing functions
from flight_manager import (
    load_flights, save_flights, INFLIGHT_SERVICES,
    select_inflight_services, save_booking_with_services,
    update_booking_with_services, parse_services_codes
)

app = Flask(__name__)

# Use existing file paths
FLIGHTS_FILE = "Flights.txt"
BOOKED_FILE = "BookedFlights.txt"

def load_bookings_web():
    bookings = []
    try:
        with open(BOOKED_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                booking = {"raw_line": line}
                
                if "|" in line:
                    parts = line.split("|")
                    flight_info = parts[0].strip()
                    
                    # Parse flight info
                    if ":" in flight_info:
                        flight_part, seat = flight_info.split(":")
                        flight_number, destination = flight_part.split(" - ")
                        booking.update({
                            "flightNumber": flight_number.strip(),
                            "destination": destination.strip(),
                            "seat": seat.strip()
                        })
                    
                    # Parse services
                    for part in parts[1:]:
                        part = part.strip()
                        if part.startswith("SERVICES:"):
                            services_codes = part.replace("SERVICES:", "").strip()
                            try:
                                food_code, drink_code, comfort_code = services_codes.split(",")
                                # Store services as individual string properties instead of a nested object
                                booking["food"] = food_code
                                booking["drinks"] = drink_code
                                booking["comfort"] = comfort_code
                                booking["services_display"] = parse_services_codes(services_codes)
                            except:
                                booking["services_display"] = "Error parsing services"
                                
                        elif part.startswith("COST:"):
                            cost_str = part.replace("COST:", "").strip()
                            try:
                                # Convert to string to avoid type issues in JavaScript
                                booking["totalCost"] = cost_str
                            except:
                                booking["totalCost"] = "$0.00"
                else:
                    # Booking without services
                    if ":" in line:
                        flight_info, seat = line.split(":")
                        flight_number, destination = flight_info.split(" - ")
                        booking["flightNumber"] = flight_number.strip()
                        booking["destination"] = destination.strip()
                        booking["seat"] = seat.strip()
                        booking["services"] = "none"
                
                bookings.append(booking)
                
    except FileNotFoundError:
        pass
        
    return bookings

def save_booking_web(flight_number, destination, seat, services=None):
    try:
        with open(BOOKED_FILE, "a") as f:
            if services:
                services_code = f"{services['food']},{services['drinks']},{services['comfort']}"
                total_cost = (INFLIGHT_SERVICES["food"][services['food']]["price"] +
                            INFLIGHT_SERVICES["drinks"][services['drinks']]["price"] +
                            INFLIGHT_SERVICES["comfort"][services['comfort']]["price"])
                f.write(f"{flight_number} - {destination}: {seat} | SERVICES:{services_code} | COST:${total_cost:.2f}\n")
            else:
                f.write(f"{flight_number} - {destination}: {seat}\n")
        return True
    except Exception as e:
        print(f"Error saving booking: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/flights')
def api_flights():
    flights = load_flights()
    return jsonify(flights)

@app.route('/api/bookings')
def api_bookings():
    bookings = load_bookings_web()
    return jsonify(bookings)

@app.route('/api/services')
def api_services():
    return jsonify(INFLIGHT_SERVICES)

@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.get_json()
    if data is None:
        return jsonify({'success': False, 'error': 'Invalid JSON data'})
    flight_number = data['flightNumber']
    seat = data['seat']
    services = data.get('services')
    
    flights = load_flights()
    
    if flight_number not in flights or seat not in flights[flight_number]['seats']:
        return jsonify({'success': False, 'error': 'Invalid flight or seat'})
    
    # Remove seat from available seats
    flights[flight_number]['seats'].remove(seat)
    save_flights(flights)
    
    # Save booking
    destination = flights[flight_number]['destination']
    success = save_booking_web(flight_number, destination, seat, services)
    
    if success:
        return jsonify({'success': True})
    else:
        # Restore seat if booking failed
        flights[flight_number]['seats'].append(seat)
        save_flights(flights)
        return jsonify({'success': False, 'error': 'Booking failed'})

@app.route('/api/cancel-booking', methods=['POST'])
def api_cancel_booking():
    data = request.get_json()
    if data is None:
        return jsonify({'success': False, 'error': 'Invalid JSON data'})
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
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template with fixed JavaScript types
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Management System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .seat-grid {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 0.5rem;
            max-width: 400px;
        }
        .seat {
            aspect-ratio: 1;
            border: 2px solid #d1d5db;
            border-radius: 0.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .seat:hover {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        .seat.selected {
            border-color: #3b82f6;
            background-color: #3b82f6;
            color: white;
        }
        .seat.occupied {
            background-color: #ef4444;
            color: white;
            cursor: not-allowed;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto py-8 px-4 max-w-6xl">
        <!-- Header -->
        <div class="mb-8">
            <div class="flex items-center gap-3 mb-2">
                <i class="fas fa-plane text-2xl text-blue-600"></i>
                <h1 class="text-3xl font-bold text-gray-900">Flight Management System</h1>
            </div>
            <p class="text-gray-600">Book flights, select seats, and manage your in-flight services</p>
        </div>

        <!-- Main Tabs -->
        <div class="bg-white rounded-lg shadow-sm border">
            <div class="border-b">
                <nav class="flex">
                    <button id="bookTab" class="tab-button py-4 px-6 font-medium border-b-2 border-blue-600 text-blue-600" 
                            onclick="showTab('book')">
                        <i class="fas fa-calendar mr-2"></i>Book Flight
                    </button>
                    <button id="manageTab" class="tab-button py-4 px-6 font-medium text-gray-500"
                            onclick="showTab('manage')">
                        <i class="fas fa-cog mr-2"></i>My Bookings
                    </button>
                </nav>
            </div>

            <!-- Book Flight Content -->
            <div id="bookContent" class="p-6">
                <div class="space-y-6">
                    <!-- Flight List -->
                    <div id="flightList">
                        <h2 class="text-xl font-semibold mb-4">Available Flights</h2>
                        <p class="text-gray-600 mb-6">Select a flight to view available seats and book your trip.</p>
                        <div id="flightsGrid" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            <!-- Flights will be loaded here -->
                        </div>
                    </div>

                    <!-- Seat Selection -->
                    <div id="seatSelection" class="hidden">
                        <button class="mb-4 text-blue-600 hover:text-blue-800" onclick="showFlightList()">
                            <i class="fas fa-arrow-left mr-2"></i>Back to Flights
                        </button>
                        <div id="seatSelectionContent">
                            <!-- Seat selection will be loaded here -->
                        </div>
                    </div>

                    <!-- Services Selection -->
                    <div id="servicesSelection" class="hidden">
                        <button class="mb-4 text-blue-600 hover:text-blue-800" onclick="showSeatSelection()">
                            <i class="fas fa-arrow-left mr-2"></i>Back to Seat Selection
                        </button>
                        <div id="servicesContent">
                            <!-- Services will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Manage Bookings Content -->
            <div id="manageContent" class="p-6 hidden">
                <div class="space-y-6">
                    <h2 class="text-xl font-semibold mb-4">My Booked Flights</h2>
                    <p class="text-gray-600 mb-6">View your bookings and add or update in-flight services.</p>
                    <div id="bookingsList">
                        <!-- Bookings will be loaded here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Define INFLIGHT_SERVICES for JavaScript
        const INFLIGHT_SERVICES = {
            food: {
                F1: { name: "Chicken Meal", price: 12.50 },
                F2: { name: "Vegetarian Meal", price: 10.00 },
                F3: { name: "Beef Meal", price: 14.00 },
                F4: { name: "Pasta Meal", price: 11.00 },
                F0: { name: "No Food", price: 0.00 }
            },
            drinks: {
                D1: { name: "Coffee", price: 3.50 },
                D2: { name: "Tea", price: 2.50 },
                D3: { name: "Orange Juice", price: 4.00 },
                D4: { name: "Water", price: 1.50 },
                D5: { name: "Soda", price: 3.00 },
                D6: { name: "Beer", price: 6.00 },
                D7: { name: "Wine", price: 7.50 },
                D0: { name: "No Drink", price: 0.00 }
            },
            comfort: {
                C1: { name: "Blanket", price: 5.00 },
                C2: { name: "Pillow", price: 3.00 },
                C3: { name: "Headphones", price: 8.00 },
                C4: { name: "Eye Mask", price: 4.00 },
                C5: { name: "Neck Pillow", price: 12.00 },
                C0: { name: "No Comfort Item", price: 0.00 }
            }
        };

        let currentFlight = null;
        let currentSeat = null;

        // Tab management
        function showTab(tabName) {
            // Hide all content
            document.getElementById('bookContent').classList.add('hidden');
            document.getElementById('manageContent').classList.add('hidden');
            
            // Remove active styles from all tabs
            document.querySelectorAll('.tab-button').forEach(tab => {
                tab.classList.remove('border-blue-600', 'text-blue-600');
                tab.classList.add('text-gray-500');
            });
            
            // Show selected content and style active tab
            document.getElementById(tabName + 'Content').classList.remove('hidden');
            document.getElementById(tabName + 'Tab').classList.add('border-blue-600', 'text-blue-600');
            document.getElementById(tabName + 'Tab').classList.remove('text-gray-500');
            
            if (tabName === 'manage') {
                loadBookings();
            } else if (tabName === 'book') {
                showFlightList();
            }
        }

        // Load and display flights
        async function loadFlights() {
            try {
                const response = await fetch('/api/flights');
                const flights = await response.json();
                
                const flightsGrid = document.getElementById('flightsGrid');
                flightsGrid.innerHTML = '';
                
                for (const [flightNumber, info] of Object.entries(flights)) {
                    const flightCard = `
                        <div class="bg-white border rounded-lg p-6 hover:shadow-lg transition-shadow">
                            <div class="flex items-center gap-2 mb-2">
                                <i class="fas fa-plane text-blue-600"></i>
                                <h3 class="text-lg font-semibold">${flightNumber}</h3>
                            </div>
                            <p class="text-gray-600 mb-4">${info.destination}</p>
                            <div class="flex items-center justify-between">
                                <span class="text-sm text-gray-500">
                                    ${info.seats.length} ${info.seats.length === 1 ? 'seat' : 'seats'} available
                                </span>
                                <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors ${info.seats.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}"
                                        ${info.seats.length === 0 ? 'disabled' : ''}
                                        onclick="selectFlight('${flightNumber}')">
                                    Select
                                </button>
                            </div>
                        </div>
                    `;
                    flightsGrid.innerHTML += flightCard;
                }
            } catch (error) {
                console.error('Error loading flights:', error);
            }
        }

        function showFlightList() {
            document.getElementById('flightList').classList.remove('hidden');
            document.getElementById('seatSelection').classList.add('hidden');
            document.getElementById('servicesSelection').classList.add('hidden');
            loadFlights();
        }

        async function selectFlight(flightNumber) {
            currentFlight = flightNumber;
            
            try {
                const response = await fetch('/api/flights');
                const flights = await response.json();
                const flight = flights[flightNumber];
                
                document.getElementById('flightList').classList.add('hidden');
                document.getElementById('seatSelection').classList.remove('hidden');
                
                const seatContent = document.getElementById('seatSelectionContent');
                seatContent.innerHTML = `
                    <div class="bg-white border rounded-lg p-6">
                        <h2 class="text-xl font-semibold mb-2">Select Your Seat</h2>
                        <p class="text-gray-600 mb-6">Flight ${flightNumber} to ${flight.destination}</p>
                        
                        ${flight.seats.length === 0 ? `
                            <p class="text-center text-gray-500 py-8">No seats available on this flight.</p>
                        ` : `
                            <div class="seat-grid mb-6">
                                ${flight.seats.map(seat => `
                                    <div class="seat" onclick="selectSeat('${seat}')">
                                        <i class="fas fa-chair text-sm"></i>
                                        <span class="text-xs mt-1">${seat}</span>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <div id="seatActions" class="hidden bg-blue-50 rounded-lg p-4">
                                <div class="flex justify-between items-center mb-4">
                                    <span class="font-medium">Selected Seat:</span>
                                    <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium" id="selectedSeatDisplay"></span>
                                </div>
                                <div class="flex flex-col sm:flex-row gap-2">
                                    <button class="flex-1 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-50 transition-colors"
                                            onclick="bookSeat(false)">
                                        Book Without Services
                                    </button>
                                    <button class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                                            onclick="bookSeat(true)">
                                        Book With Services
                                    </button>
                                </div>
                            </div>
                        `}
                    </div>
                `;
            } catch (error) {
                console.error('Error loading flight details:', error);
            }
        }

        function selectSeat(seat) {
            currentSeat = seat;
            
            // Remove selection from all seats
            document.querySelectorAll('.seat').forEach(seatEl => {
                seatEl.classList.remove('selected');
            });
            
            // Add selection to clicked seat
            event.target.closest('.seat').classList.add('selected');
            
            // Show actions
            document.getElementById('seatActions').classList.remove('hidden');
            document.getElementById('selectedSeatDisplay').textContent = seat;
        }

        function showSeatSelection() {
            document.getElementById('seatSelection').classList.remove('hidden');
            document.getElementById('servicesSelection').classList.add('hidden');
        }

        async function bookSeat(withServices) {
            if (!withServices) {
                // Book without services
                try {
                    const response = await fetch('/api/book', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            flightNumber: currentFlight,
                            seat: currentSeat,
                            services: null
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert(`Successfully booked seat ${currentSeat} on ${currentFlight}!`);
                        showFlightList();
                        loadFlights();
                    } else {
                        alert('Booking failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Booking failed: ' + error.message);
                }
            } else {
                // Show services selection
                await showServicesSelection();
            }
        }

        async function showServicesSelection() {
            document.getElementById('seatSelection').classList.add('hidden');
            document.getElementById('servicesSelection').classList.remove('hidden');
            
            try {
                const response = await fetch('/api/services');
                const services = await response.json();
                
                const servicesContent = document.getElementById('servicesContent');
                servicesContent.innerHTML = `
                    <div class="bg-white border rounded-lg p-6">
                        <h2 class="text-xl font-semibold mb-2">In-Flight Services</h2>
                        <p class="text-gray-600 mb-6">Flight ${currentFlight} - Seat ${currentSeat}</p>
                        
                        <form id="servicesForm" class="space-y-6">
                            <!-- Food Selection -->
                            <div>
                                <h3 class="font-semibold mb-3"><i class="fas fa-utensils mr-2 text-blue-600"></i>Food Selection</h3>
                                ${Object.entries(services.food).map(([code, item]) => `
                                    <label class="flex items-center justify-between p-3 hover:bg-gray-50 rounded cursor-pointer">
                                        <div class="flex items-center">
                                            <input type="radio" name="food" value="${code}" ${code === 'F0' ? 'checked' : ''} class="mr-3">
                                            <span>${item.name}</span>
                                        </div>
                                        <span class="text-gray-600">$${item.price.toFixed(2)}</span>
                                    </label>
                                `).join('')}
                            </div>
                            
                            <!-- Drink Selection -->
                            <div>
                                <h3 class="font-semibold mb-3"><i class="fas fa-coffee mr-2 text-blue-600"></i>Drink Selection</h3>
                                ${Object.entries(services.drinks).map(([code, item]) => `
                                    <label class="flex items-center justify-between p-3 hover:bg-gray-50 rounded cursor-pointer">
                                        <div class="flex items-center">
                                            <input type="radio" name="drinks" value="${code}" ${code === 'D0' ? 'checked' : ''} class="mr-3">
                                            <span>${item.name}</span>
                                        </div>
                                        <span class="text-gray-600">$${item.price.toFixed(2)}</span>
                                    </label>
                                `).join('')}
                            </div>
                            
                            <!-- Comfort Selection -->
                            <div>
                                <h3 class="font-semibold mb-3"><i class="fas fa-spa mr-2 text-blue-600"></i>Comfort Items</h3>
                                ${Object.entries(services.comfort).map(([code, item]) => `
                                    <label class="flex items-center justify-between p-3 hover:bg-gray-50 rounded cursor-pointer">
                                        <div class="flex items-center">
                                            <input type="radio" name="comfort" value="${code}" ${code === 'C0' ? 'checked' : ''} class="mr-3">
                                            <span>${item.name}</span>
                                        </div>
                                        <span class="text-gray-600">$${item.price.toFixed(2)}</span>
                                    </label>
                                `).join('')}
                            </div>
                            
                            <!-- Summary -->
                            <div class="bg-gray-50 rounded-lg p-4">
                                <h3 class="font-semibold mb-3">Services Summary</h3>
                                <div id="servicesSummary" class="space-y-2 text-sm">
                                    <!-- Summary will be updated here -->
                                </div>
                            </div>
                            
                            <!-- Action Buttons -->
                            <div class="flex gap-2">
                                <button type="button" class="flex-1 bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
                                        onclick="showSeatSelection()">
                                    Cancel
                                </button>
                                <button type="submit" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors">
                                    Confirm Booking
                                </button>
                            </div>
                        </form>
                    </div>
                `;
                
                // Add form submission handler
                document.getElementById('servicesForm').addEventListener('submit', handleServicesSubmit);
                
                // Add real-time summary updates
                document.querySelectorAll('#servicesForm input[type="radio"]').forEach(input => {
                    input.addEventListener('change', updateServicesSummary);
                });
                
                updateServicesSummary();
            } catch (error) {
                console.error('Error loading services:', error);
            }
        }

        function updateServicesSummary() {
            const form = document.getElementById('servicesForm');
            const formData = new FormData(form);
            
            // Calculate total
            let total = 0;
            const services = {};
            
            // Get service names and prices from the defined INFLIGHT_SERVICES
            const food = formData.get('food') || 'F0';
            const drinks = formData.get('drinks') || 'D0';
            const comfort = formData.get('comfort') || 'C0';
            
            const foodPrice = INFLIGHT_SERVICES.food[food]?.price || 0;
            const drinkPrice = INFLIGHT_SERVICES.drinks[drinks]?.price || 0;
            const comfortPrice = INFLIGHT_SERVICES.comfort[comfort]?.price || 0;
            
            total = foodPrice + drinkPrice + comfortPrice;
            
            const foodName = INFLIGHT_SERVICES.food[food]?.name || 'None';
            const drinkName = INFLIGHT_SERVICES.drinks[drinks]?.name || 'None';
            const comfortName = INFLIGHT_SERVICES.comfort[comfort]?.name || 'None';
            
            const summary = document.getElementById('servicesSummary');
            summary.innerHTML = `
                <div class="flex justify-between">
                    <span>Food:</span>
                    <span>${foodName}</span>
                </div>
                <div class="flex justify-between">
                    <span>Drink:</span>
                    <span>${drinkName}</span>
                </div>
                <div class="flex justify-between">
                    <span>Comfort:</span>
                    <span>${comfortName}</span>
                </div>
                <div class="border-t pt-2 flex justify-between font-semibold">
                    <span>Total Additional Cost:</span>
                    <span>$${total.toFixed(2)}</span>
                </div>
            `;
        }

        async function handleServicesSubmit(e) {
            e.preventDefault();
            
            const form = document.getElementById('servicesForm');
            const formData = new FormData(form);
            
            const services = {
                food: formData.get('food') || 'F0',
                drinks: formData.get('drinks') || 'D0',
                comfort: formData.get('comfort') || 'C0'
            };
            
            try {
                const response = await fetch('/api/book', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        flightNumber: currentFlight,
                        seat: currentSeat,
                        services: services
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`Successfully booked seat ${currentSeat} on ${currentFlight} with services!`);
                    showFlightList();
                    loadFlights();
                } else {
                    alert('Booking failed: ' + result.error);
                }
            } catch (error) {
                alert('Booking failed: ' + error.message);
            }
        }

        async function loadBookings() {
            try {
                const response = await fetch('/api/bookings');
                const bookings = await response.json();
                
                const bookingsList = document.getElementById('bookingsList');
                
                if (bookings.length === 0) {
                    bookingsList.innerHTML = `
                        <div class="bg-white border rounded-lg p-6 text-center">
                            <p class="text-gray-500">No booked flights yet.</p>
                            <p class="text-sm text-gray-400 mt-2">Book a flight to get started!</p>
                        </div>
                    `;
                    return;
                }
                
                bookingsList.innerHTML = bookings.map((booking, index) => `
                    <div class="bg-white border rounded-lg p-6">
                        <div class="flex items-start justify-between mb-4">
                            <div>
                                <div class="flex items-center gap-2 mb-1">
                                    <i class="fas fa-plane text-blue-600"></i>
                                    <h3 class="text-lg font-semibold">${booking.flightNumber}</h3>
                                </div>
                                <p class="text-gray-600">${booking.destination} - Seat ${booking.seat}</p>
                            </div>
                        </div>
                        
                        ${booking.services ? `
                            <div class="space-y-3">
                                <div class="text-sm space-y-1">
                                    <div class="flex justify-between">
                                        <span class="text-gray-500">Food:</span>
                                        <span>${INFLIGHT_SERVICES.food[booking.services.food]?.name || 'Unknown'}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-gray-500">Drink:</span>
                                        <span>${INFLIGHT_SERVICES.drinks[booking.services.drinks]?.name || 'Unknown'}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-gray-500">Comfort:</span>
                                        <span>${INFLIGHT_SERVICES.comfort[booking.services.comfort]?.name || 'Unknown'}</span>
                                    </div>
                                </div>
                                <div class="flex justify-between items-center border-t pt-2">
                                    <span class="text-sm">Additional Cost:</span>
                                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">${booking.totalCost || '$0.00'}</span>
                                </div>
                            </div>
                        ` : `
                            <p class="text-sm text-gray-500">No in-flight services added</p>
                        `}
                        
                        <div class="mt-4">
                            <button class="bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700 transition-colors"
                                    onclick="cancelBooking(${index})">
                                <i class="fas fa-trash mr-1"></i>Cancel Booking
                            </button>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading bookings:', error);
            }
        }

        async function cancelBooking(bookingIndex) {
            if (confirm('Are you sure you want to cancel this booking?')) {
                try {
                    const response = await fetch('/api/cancel-booking', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ bookingIndex: parseInt(bookingIndex) })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('Booking cancelled successfully!');
                        loadBookings();
                        loadFlights();
                    } else {
                        alert('Cancellation failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Cancellation failed: ' + error.message);
                }
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadFlights();
        });
    </script>
</body>
</html>""")
    app.run(debug=True, port=5000)