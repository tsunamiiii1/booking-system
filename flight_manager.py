import sys

FLIGHTS_FILE = "Flights.txt"
BOOKED_FILE = "BookedFlights.txt"

def load_flights():
    flights = {}
    try:
        with open(FLIGHTS_FILE, "r") as f:
            for line in f:
                if ":" in line:
                    flight_info, seats = line.strip().split(":")
                    flight_number, destination = flight_info.split(" - ")
                    seat_list = seats.strip(" []").split(", ")
                    flights[flight_number] = {
                        "destination": destination,
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


def flight_options(flights):
    print("\nAvailable Flights:")
    for flight, info in flights.items():
        print(f"{flight} - {info['destination']} ({len(info['seats'])} seats left)")


def seat_selection(flights, flight_number):
    if flight_number not in flights:
        print("Invalid flight number.")
        return
    seats = flights[flight_number]["seats"]
    print(f"\nSeats available on {flight_number}: {', '.join(seats) if seats else 'No seats available.'}")
    seat = input("Choose your seat: ").upper().strip()
    if seat not in seats:
        print("Seat not available.")
        return

    # Remove seat from available seats
    flights[flight_number]["seats"].remove(seat)
    save_flights(flights)

    # Save booking to BookedFlights.txt
    try:
        with open("BookedFlights.txt", "a") as bf:
            bf.write(f"{flight_number} - {flights[flight_number]['destination']}: {seat}\n")
    except Exception as e:
        print(f"Error saving booking: {e}")

    print(f"Seat {seat} booked on {flight_number}.")


def return_flight():
    # Placeholder – add logic later
    print("Return flight booking not yet implemented.")


def inflight_services():
    print("\n--- In-flight Services ---")
    print("1. Meal")
    print("2. Drinks")
    print("3. Duty-free Shopping")
    print("Feature not yet implemented.")


def show_booked_flights():
    try:
        with open(BOOKED_FILE, "r") as bf:
            bookings = bf.readlines()
            if not bookings:
                print("No booked flights yet.")
                return
            print("\n--- Booked Flights ---")
            for line in bookings:
                print(line.strip())
    except FileNotFoundError:
        print("No bookings found.")


def manage_reservations(flights):
    while True:
        print("\n--- Manage Reservations ---")
        print("1. Seat Selection")
        print("2. Return Flight")
        print("3. In-flight Services")
        print("4. Show Booked Flights")
        print("5. Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            flight_number = input("Enter your flight number: ").upper().strip()
            seat_selection(flights, flight_number)
        elif choice == "2":
            return_flight()
        elif choice == "3":
            inflight_services()
        elif choice == "4":
            show_booked_flights()
        elif choice == "5":
            break
        else:
            print("Invalid option. Try again.")


def book_flight(flights):
    while True:
        print("\n--- Book Flight ---")
        print("1. Flight Options")
        print("2. Seat Selection")
        print("3. Return Flight")
        print("4. In-flight Services")
        print("5. Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            flight_options(flights)
        elif choice == "2":
            flight_number = input("Enter flight number: ").upper().strip()
            seat_selection(flights, flight_number)
        elif choice == "3":
            return_flight()
        elif choice == "4":
            inflight_services()
        elif choice == "5":
            break
        else:
            print("Invalid option. Try again.")

def main():
    flights = load_flights()
    if not flights:
        return

    while True:
        print("\n--------------")
        print("FLIGHT MANAGER")
        print("--------------")
        print("1. Book Flight")
        print("2. Manage Reservations")
        print("3. Exit")

        choice = input("What would you like to do? (1, 2, 3): ").strip()

        if choice == "1":
            book_flight(flights)
        elif choice == "2":
            manage_reservations(flights)
        elif choice == "3":
            print("Come again. See ya!")
            sys.exit()
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()
