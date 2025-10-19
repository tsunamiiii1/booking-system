import sys
from datetime import datetime

FLIGHTS_FILE = "Flights.txt"
BOOKED_FILE = "BookedFlights.txt"

# In-flight services menu with codes and prices
INFLIGHT_SERVICES = {
    "food": {
        "F1": {"name": "Chicken Meal", "price": 12.50},
        "F2": {"name": "Vegetarian Meal", "price": 10.00},
        "F3": {"name": "Beef Meal", "price": 14.00},
        "F4": {"name": "Pasta Meal", "price": 11.00},
        "F0": {"name": "No Food", "price": 0.00}
    },
    "drinks": {
        "D1": {"name": "Coffee", "price": 3.50},
        "D2": {"name": "Tea", "price": 2.50},
        "D3": {"name": "Orange Juice", "price": 4.00},
        "D4": {"name": "Water", "price": 1.50},
        "D5": {"name": "Soda", "price": 3.00},
        "D6": {"name": "Beer", "price": 6.00},
        "D7": {"name": "Wine", "price": 7.50},
        "D0": {"name": "No Drink", "price": 0.00}
    },
    "comfort": {
        "C1": {"name": "Blanket", "price": 5.00},
        "C2": {"name": "Pillow", "price": 3.00},
        "C3": {"name": "Headphones", "price": 8.00},
        "C4": {"name": "Eye Mask", "price": 4.00},
        "C5": {"name": "Neck Pillow", "price": 12.00},
        "C0": {"name": "No Comfort Item", "price": 0.00}
    }
}

def load_flights():
    flights = {}
    try:
        with open(FLIGHTS_FILE, "r") as f:
            for line in f:
                if ":" in line:
                    flight_info, seats = line.strip().split(":")
                    flight_number, destination = flight_info.split(" - ")
                    seat_list = [seat.strip() for seat in seats.strip(" []").split(",") if seat.strip()]
                    flights[flight_number] = {
                        "destination": destination.strip(),
                        "seats": seat_list
                    }
    except FileNotFoundError:
        print("Error: Flights file not found.")
    return flights

def save_flights(flights):
    try:
        with open(FLIGHTS_FILE, "w") as f:
            for flight, info in flights.items():
                seats_str = ", ".join(info["seats"])
                f.write(f"{flight} - {info['destination']}: [{seats_str}]\n")
    except Exception as e:
        print(f"Error saving flights: {e}")

def display_service_menu(service_type):
    services = INFLIGHT_SERVICES[service_type]
    print(f"\n--- {service_type.title()} Menu ---")
    for code, info in services.items():
        print(f"{code}: {info['name']} - ${info['price']:.2f}")

def get_service_choice(service_type):
    services = INFLIGHT_SERVICES[service_type]
    valid_codes = list(services.keys())
    
    while True:
        display_service_menu(service_type)
        choice = input(f"Choose {service_type} code: ").upper().strip()
        
        if choice in valid_codes:
            return choice
        else:
            print(f"Invalid code. Please choose from: {', '.join(valid_codes)}")

def select_inflight_services(flight_number, seat):
    print(f"\n--- In-flight Services for {flight_number} Seat {seat} ---")
    
    services_selected = {}
    total_cost = 0.0
    
    # Food selection
    print("\n1. Food Selection:")
    food_choice = get_service_choice("food")
    services_selected["food"] = food_choice
    total_cost += INFLIGHT_SERVICES["food"][food_choice]["price"]
    
    # Drink selection
    print("\n2. Drink Selection:")
    drink_choice = get_service_choice("drinks")
    services_selected["drinks"] = drink_choice
    total_cost += INFLIGHT_SERVICES["drinks"][drink_choice]["price"]
    
    # Comfort selection
    print("\n3. Comfort Selection:")
    comfort_choice = get_service_choice("comfort")
    services_selected["comfort"] = comfort_choice
    total_cost += INFLIGHT_SERVICES["comfort"][comfort_choice]["price"]
    
    # Display summary
    print(f"\n--- Services Summary ---")
    print(f"Food: {INFLIGHT_SERVICES['food'][food_choice]['name']}")
    print(f"Drink: {INFLIGHT_SERVICES['drinks'][drink_choice]['name']}")
    print(f"Comfort: {INFLIGHT_SERVICES['comfort'][comfort_choice]['name']}")
    print(f"Total Additional Cost: ${total_cost:.2f}")
    
    confirm = input("\nConfirm these services? (y/n): ").lower().strip()
    if confirm == 'y':
        return services_selected, total_cost
    else:
        print("Services selection cancelled.")
        return None, 0.0

def save_booking_with_services(flight_number, destination, seat, services=None, total_cost=0.0):
    try:
        with open(BOOKED_FILE, "a") as bf:
            if services:
                services_code = f"{services['food']},{services['drinks']},{services['comfort']}"
                bf.write(f"{flight_number} - {destination}: {seat} | SERVICES:{services_code} | COST:${total_cost:.2f}\n")
            else:
                bf.write(f"{flight_number} - {destination}: {seat}\n")
        return True
    except Exception as e:
        print(f"Error saving booking: {e}")
        return False

def inflight_services():
    print("\n--- In-flight Services ---")
    
    # Check if user has a booking
    try:
        with open(BOOKED_FILE, "r") as f:
            bookings = f.readlines()
            if not bookings:
                print("No bookings found. Please book a flight first.")
                return
    except FileNotFoundError:
        print("No bookings found. Please book a flight first.")
        return
    
    # Show existing bookings
    print("\nYour Bookings:")
    simple_bookings = []
    for i, booking in enumerate(bookings, 1):
        # Extract basic booking info (before any |)
        basic_booking = booking.split('|')[0].strip()
        simple_bookings.append(basic_booking)
        print(f"{i}. {basic_booking}")
    
    # Select booking to add services
    try:
        booking_choice = int(input("\nSelect booking to add services (number): ")) - 1
        if 0 <= booking_choice < len(simple_bookings):
            selected_booking = simple_bookings[booking_choice]  # Fixed the variable name
            
            # Parse flight number, destination, and seat
            if ":" in selected_booking:
                flight_info, seat = selected_booking.split(":")
                flight_number, destination = flight_info.split(" - ")
                flight_number = flight_number.strip()
                destination = destination.strip()
                seat = seat.strip()
                
                # Check if services already exist for this booking
                original_booking_line = bookings[booking_choice].strip()
                if "SERVICES:" in original_booking_line:
                    print("Services already exist for this booking. Would you like to update them?")
                    confirm = input("This will replace existing services. Continue? (y/n): ").lower()
                    if confirm != 'y':
                        return
                
                # Select services
                services, total_cost = select_inflight_services(flight_number, seat)
                
                if services:
                    # Remove the old booking and add new one with services
                    update_booking_with_services(bookings, booking_choice, flight_number, destination, seat, services, total_cost)
                    print("Services added to your booking successfully!")
                else:
                    print("No services were added.")
            else:
                print("Invalid booking format.")
        else:
            print("Invalid booking selection.")
    except (ValueError, IndexError):
        print("Invalid input. Please enter a valid booking number.")

def update_booking_with_services(all_bookings, booking_index, flight_number, destination, seat, services, total_cost):
    try:
        # Create new booking line with services
        services_code = f"{services['food']},{services['drinks']},{services['comfort']}"
        new_booking_line = f"{flight_number} - {destination}: {seat} | SERVICES:{services_code} | COST:${total_cost:.2f}\n"
        
        # Replace the old booking
        all_bookings[booking_index] = new_booking_line
        
        # Write back all bookings
        with open(BOOKED_FILE, "w") as f:
            f.writelines(all_bookings)
            
    except Exception as e:
        print(f"Error updating booking with services: {e}")

def show_booked_flights():
    try:
        with open(BOOKED_FILE, "r") as bf:
            bookings = bf.readlines()
            if not bookings:
                print("No booked flights yet.")
                return
            
            print("\n--- Booked Flights ---")
            for i, line in enumerate(bookings, 1):
                line = line.strip()
                if "|" in line:
                    parts = line.split("|")
                    flight_info = parts[0].strip()
                    
                    # Parse services if they exist
                    services_info = ""
                    cost_info = ""
                    
                    for part in parts[1:]:
                        part = part.strip()
                        if part.startswith("SERVICES:"):
                            services_codes = part.replace("SERVICES:", "").strip()
                            services_info = parse_services_codes(services_codes)
                        elif part.startswith("COST:"):
                            cost_info = part.replace("COST:", "").strip()
                    
                    print(f"{i}. Flight: {flight_info}")
                    if services_info:
                        print(f"   Services: {services_info}")
                    if cost_info:
                        print(f"   Additional Cost: {cost_info}")
                else:
                    print(f"{i}. Flight: {line} (No services added)")
                print("-" * 50)
                    
    except FileNotFoundError:
        print("No bookings found.")

def parse_services_codes(services_codes):
    try:
        food_code, drink_code, comfort_code = services_codes.split(",")
        
        food_name = INFLIGHT_SERVICES["food"][food_code]["name"]
        drink_name = INFLIGHT_SERVICES["drinks"][drink_code]["name"]
        comfort_name = INFLIGHT_SERVICES["comfort"][comfort_code]["name"]
        
        return f"Food: {food_name}, Drink: {drink_name}, Comfort: {comfort_name}"
    except Exception as e:
        return f"Error parsing services: {e}"

def flight_options(flights):
    print("\nAvailable Flights:")
    if not flights:
        print("No flights available.")
        return
        
    for flight, info in flights.items():
        print(f"{flight} - {info['destination']} ({len(info['seats'])} seats left)")

def seat_selection(flights, flight_number):
    if flight_number not in flights:
        print("Invalid flight number.")
        return None
        
    seats = flights[flight_number]["seats"]
    if not seats:
        print("No seats available on this flight.")
        return None
        
    print(f"\nSeats available on {flight_number}: {', '.join(seats)}")
    seat = input("Choose your seat: ").upper().strip()
    
    if seat not in seats:
        print("Seat not available.")
        return None

    # Remove seat from available seats
    flights[flight_number]["seats"].remove(seat)
    save_flights(flights)

    # Ask if user wants to add in-flight services
    add_services = input("Would you like to add in-flight services now? (y/n): ").lower().strip()
    services = None
    total_cost = 0.0
    
    if add_services == 'y':
        services, total_cost = select_inflight_services(flight_number, seat)
    
    # Save booking to BookedFlights.txt
    if save_booking_with_services(flight_number, flights[flight_number]["destination"], seat, services, total_cost):
        print(f"Seat {seat} booked on {flight_number}.")
        if services:
            print(f"In-flight services added. Additional cost: ${total_cost:.2f}")
        return seat
    else:
        # If saving failed, add the seat back
        flights[flight_number]["seats"].append(seat)
        save_flights(flights)
        print("Booking failed. Please try again.")
        return None

def manage_reservations(flights):
    while True:
        print("\n" + "-------------------------")
        print("Manage Reservations")
        print("-------------------------")
        print("1. In-flight Services")
        print("2. Show Booked Flights")
        print("3. Back")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            inflight_services()
        elif choice == "2":
            show_booked_flights()
        elif choice == "3":
            break
        else:
            print("Invalid option. Try again.")

def book_flight(flights):
    while True:
        print("\n" + "-------------------------")
        print("Book Flight")
        print("-------------------------")
        print("1. Flight Options")
        print("2. Seat Selection")
        print("3. Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            flight_options(flights)
        elif choice == "2":
            flight_number = input("Enter flight number: ").upper().strip()
            seat_selection(flights, flight_number)
        elif choice == "3":
            break
        else:
            print("Invalid option. Try again.")

def main():
    # Load flights or initialize sample data
    flights = load_flights()
    if not flights:
        print("No flight data found.")
        return

    while True:
        print("\n" + "-------------------------")
        print("FLIGHT MANAGEMENT SYSTEM")
        print("-------------------------")
        print("1. Book Flight")
        print("2. Manage Reservations")
        print("3. Exit")

        choice = input("\nWhat would you like to do? (1-3): ").strip()

        if choice == "1":
            book_flight(flights)
        elif choice == "2":
            manage_reservations(flights)
        elif choice == "3":
            print("\nThank you for using Flight Management System!")
            print("Have a great day!")
            sys.exit()
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()