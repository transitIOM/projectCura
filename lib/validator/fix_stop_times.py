#!/usr/bin/env python3
"""
Script to fix invalid stop times in stop_times.txt.
Fixes issues where the hour is incorrect, causing overlaps or departure before arrival.

The script works by:
1. Reading all stops and grouping them by trip_id
2. Processing each trip's stops in order (by stop_sequence)
3. For each stop, ensuring the time is >= the previous stop's time
4. If a time is too early, incrementing the hour until it fits
5. Ensuring departure_time >= arrival_time for each stop
"""

import csv
from collections import defaultdict


def time_to_minutes(time_str):
    """Convert HH:MM or HH:MM:SS to minutes since midnight."""
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    return hour * 60 + minute


def minutes_to_time(minutes):
    """Convert minutes since midnight to HH:MM format."""
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def fix_trip_stops(stops):
    """Fix the times for a single trip's stops to ensure chronological order."""
    if not stops:
        return stops

    # Sort by stop_sequence to ensure correct order
    stops = sorted(stops, key=lambda s: int(s["stop_sequence"]))

    fixed_stops = []
    last_arrival_min = 0  # Track the last arrival time in minutes
    last_departure_min = 0  # Track the last departure time in minutes

    for stop in stops:
        stop_copy = stop.copy()

        # Parse arrival and departure times
        arrival_min = time_to_minutes(stop["arrival_time"])
        departure_min = time_to_minutes(stop["departure_time"])

        # Fix arrival time: ensure it's >= previous departure
        while arrival_min < last_departure_min:
            arrival_min += 60  # Increment by 1 hour

        # Fix departure time: ensure it's >= arrival time
        if departure_min < arrival_min:
            departure_min = arrival_min

        # Also ensure departure is >= previous departure (in case arrival was fixed more)
        while departure_min < last_departure_min:
            departure_min += 60

        # Update the stop with fixed times
        stop_copy["arrival_time"] = minutes_to_time(arrival_min)
        stop_copy["departure_time"] = minutes_to_time(departure_min)

        fixed_stops.append(stop_copy)
        last_arrival_min = arrival_min
        last_departure_min = departure_min

    return fixed_stops


def main():
    input_file = "dataset/stop_times.txt"
    output_file = "dataset/stop_times_fixed.txt"

    print(f"Reading {input_file}...")

    # Read the CSV file
    with open(input_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        all_stops = list(reader)

    print(f"Read {len(all_stops)} stop records")

    # Group stops by trip_id
    trips = defaultdict(list)
    for stop in all_stops:
        trips[stop["trip_id"]].append(stop)

    print(f"Found {len(trips)} trips")

    # Process each trip
    fixed_all_stops = []
    trips_fixed = 0

    for trip_id, stops in sorted(trips.items()):
        print(f"  Processing {trip_id} ({len(stops)} stops)...", end="")
        fixed_stops = fix_trip_stops(stops)

        # Check if any changes were made
        changed = False
        for i, (original, fixed) in enumerate(zip(stops, fixed_stops)):
            if (
                original["arrival_time"] != fixed["arrival_time"]
                or original["departure_time"] != fixed["departure_time"]
            ):
                changed = True
                break

        if changed:
            trips_fixed += 1
            print(" [FIXED]")
        else:
            print(" [OK]")

        fixed_all_stops.extend(fixed_stops)

    # Write the fixed file
    print(f"\nWriting {output_file}...")
    with open(output_file, "w", newline="") as f:
        if fixed_all_stops:
            fieldnames = fixed_all_stops[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(fixed_all_stops)

    print(f"Done! Fixed {trips_fixed} out of {len(trips)} trips")
    print(f"\nTo use the fixed file:")
    print(f"  cp {input_file} {input_file}.backup")
    print(f"  cp {output_file} {input_file}")


if __name__ == "__main__":
    main()
