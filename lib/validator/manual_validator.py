import csv
import os


def parse_time(time_str):
    """Parse time string in HH:MM or HH:MM:SS format to total seconds.

    GTFS allows times >= 24:00 to represent trips spanning midnight.
    Returns total seconds for easy comparison.
    """
    parts = time_str.split(":")
    if len(parts) == 2:
        hour, minute = map(int, parts)
        return hour * 3600 + minute * 60
    elif len(parts) == 3:
        hour, minute, second = map(int, parts)
        return hour * 3600 + minute * 60 + second
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def load_trips():
    """Load all valid trip_ids from trips.txt."""
    trips_path = "../../dataset/trips.txt"
    trip_ids = set()
    if not os.path.exists(trips_path):
        print(f"Warning: trips.txt not found at {trips_path}")
        return trip_ids

    with open(trips_path, newline="\n") as csvfile:
        next(csvfile)  # Skip header
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        for row in reader:
            if len(row) > 2:
                trip_ids.add(row[2])  # trip_id is third column
    return trip_ids


def load_stops():
    """Load all valid stop_ids from stops.txt."""
    stops_path = "../../dataset/stops.txt"
    stop_ids = set()
    if not os.path.exists(stops_path):
        print(f"Warning: stops.txt not found at {stops_path}")
        return stop_ids

    with open(stops_path, newline="\n") as csvfile:
        next(csvfile)  # Skip header
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        for row in reader:
            if len(row) > 0:
                stop_ids.add(row[0])  # stop_id is first column
    return stop_ids


def validate_csv_structure(filePath):
    """Validate CSV structure: correct number of fields and line termination."""
    print("\n=== CSV Structure Validation ===")

    issues = []
    expected_fields = 8  # trip_id, arrival_time, departure_time, stop_id, stop_sequence, pickup_type, drop_off_type, timepoint

    with open(filePath, 'rb') as f:
        content = f.read()

    # Check for proper line endings
    lines = content.decode('utf-8').split('\n')

    # Check if file ends with newline
    if not content.endswith(b'\n'):
        issues.append("File does not end with a newline character")

    with open(filePath, newline="\n") as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        line_number = 1

        for row in reader:
            if line_number == 1:
                # Skip header
                line_number += 1
                continue

            if len(row) != expected_fields:
                issues.append(
                    f"Line {line_number}: Expected {expected_fields} fields, got {len(row)}"
                )

            line_number += 1

    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    else:
        print(f"  ✓ CSV structure is valid ({expected_fields} fields per line)")
        print(f"  ✓ Line endings are properly terminated")
        return True


def main():
    filePath = "../../dataset/stop_times.txt"

    # First validate CSV structure
    csv_valid = validate_csv_structure(filePath)

    # Load reference data for orphaned relationship checks
    valid_trip_ids = load_trips()
    valid_stop_ids = load_stops()

    print(f"\n=== Reference Data Loaded ===")
    print(f"  Valid trip_ids in trips.txt: {len(valid_trip_ids)}")
    print(f"  Valid stop_ids in stops.txt: {len(valid_stop_ids)}")

    trips = {}
    orphaned_trip_ids = set()
    orphaned_stop_ids = set()

    with open(filePath, newline="\n") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        line_number = 2  # Start at line 2 since we skipped the header
        for line in reader:
            if len(line) != 8:
                print(f"Skipping line {line_number}: incorrect number of fields")
                line_number += 1
                continue

            (
                trip_id,
                arrival_time,
                departure_time,
                stop_id,
                stop_sequence,
                pickup_type,
                drop_off_type,
                timepoint,
            ) = line

            # Check for orphaned relationships
            if valid_trip_ids and trip_id not in valid_trip_ids:
                orphaned_trip_ids.add((trip_id, line_number))
            if valid_stop_ids and stop_id not in valid_stop_ids:
                orphaned_stop_ids.add((stop_id, line_number))

            try:
                trips.setdefault(trip_id, []).append(
                    (
                        stop_sequence,
                        parse_time(arrival_time),
                        parse_time(departure_time),
                        line_number,
                    )
                )
            except ValueError as e:
                print(
                    f"Error in trip_id: {trip_id}, stop_sequence: {stop_sequence}, line_number: {line_number}"
                )
                print(
                    f"  arrival_time: {arrival_time}, departure_time: {departure_time}"
                )
                print(f"  Error: {e}")
                continue
            line_number += 1

    for key in trips:
        trips[key].sort()

    # Validate all trips
    print("\n=== Validation Results ===")

    # Report CSV structure validation
    if csv_valid:
        print("✓ CSV structure validation: PASSED")
    else:
        print("✗ CSV structure validation: FAILED")

    # Report orphaned relationships
    if orphaned_trip_ids:
        print(f"\n✗ Orphaned trip_id references ({len(orphaned_trip_ids)}):")
        for trip_id, line_num in sorted(orphaned_trip_ids)[:10]:  # Show first 10
            print(f"  Line {line_num}: trip_id '{trip_id}' not found in trips.txt")
        if len(orphaned_trip_ids) > 10:
            print(f"  ... and {len(orphaned_trip_ids) - 10} more")
    else:
        if valid_trip_ids:
            print("\n✓ Orphaned trip_id check: PASSED (all trip_ids found in trips.txt)")
        else:
            print("\n⚠ Orphaned trip_id check: SKIPPED (trips.txt not found)")

    if orphaned_stop_ids:
        print(f"\n✗ Orphaned stop_id references ({len(orphaned_stop_ids)}):")
        for stop_id, line_num in sorted(orphaned_stop_ids)[:10]:  # Show first 10
            print(f"  Line {line_num}: stop_id '{stop_id}' not found in stops.txt")
        if len(orphaned_stop_ids) > 10:
            print(f"  ... and {len(orphaned_stop_ids) - 10} more")
    else:
        if valid_stop_ids:
            print("✓ Orphaned stop_id check: PASSED (all stop_ids found in stops.txt)")
        else:
            print("⚠ Orphaned stop_id check: SKIPPED (stops.txt not found)")

    # Time validation
    print("\n=== Time Sequence Validation ===")
    overlap_count = 0
    depart_after_count = 0
    valid_count = 0

    for trip_id, trip in trips.items():
        overlap_lines = checkForOverlap(trip, trip_id)
        depart_after_lines = departAfterArrive(trip)

        if overlap_lines:
            print(
                f"OVERLAP DETECTED in trip_id: {trip_id} at line(s): {', '.join(map(str, overlap_lines))}"
            )
            overlap_count += 1
        if depart_after_lines:
            print(
                f"DEPARTURE BEFORE ARRIVAL in trip_id: {trip_id} at line(s): {', '.join(map(str, depart_after_lines))}"
            )
            depart_after_count += 1
        if not overlap_lines and not depart_after_lines:
            valid_count += 1

    print("\n=== Summary ===")
    print(f"  Total trips: {len(trips)}")
    print(f"  Valid trips: {valid_count}")
    print(f"  Trips with overlap: {overlap_count}")
    print(f"  Trips with departure before arrival: {depart_after_count}")
    print(f"  Orphaned trip_id references: {len(orphaned_trip_ids)}")
    print(f"  Orphaned stop_id references: {len(orphaned_stop_ids)}")
    print(f"  CSV structure valid: {'Yes' if csv_valid else 'No'}")


def checkForOverlap(trip, trip_id):
    """
    Check for overlaps between consecutive stops in a trip.

    The trip data is sorted by stop_sequence, so consecutive indices
    correspond to consecutive stop_sequence values.

    Args:
        trip: List of tuples (stop_sequence, arrival_time, departure_time, line_number)
        trip_id: The trip identifier for debugging

    Returns:
        List of line numbers where overlaps occur
    """
    overlap_lines = []
    for x in range(len(trip) - 1):
        # Get data for current and next stop (consecutive by stop_sequence)
        current_stop_sequence = int(trip[x][0])
        next_stop_sequence = int(trip[x + 1][0])
        current_departure = trip[x][2]
        next_arrival = trip[x + 1][1]
        current_line = trip[x][3]
        next_line = trip[x + 1][3]

        # Only check if stop_sequences are consecutive
        if next_stop_sequence - current_stop_sequence == 1:
            # Check if departure from current stop is after arrival at next stop
            # Using strict > allows equal times (no overlap when departure == arrival)
            if current_departure > next_arrival:
                # Convert seconds back to HH:MM:SS for display
                def format_time(seconds):
                    h = seconds // 3600
                    m = (seconds % 3600) // 60
                    s = seconds % 60
                    return f"{h:02d}:{m:02d}:{s:02d}"

                print(
                    f"  Overlap at lines {current_line} and {next_line}: "
                    f"stop_sequence {current_stop_sequence}->{next_stop_sequence}, "
                    f"departure={format_time(current_departure)}, next_arrival={format_time(next_arrival)}"
                )
                overlap_lines.append(current_line)
                overlap_lines.append(next_line)
    return list(set(overlap_lines))


def departAfterArrive(trip):
    depart_after_lines = []
    for stop in trip:
        if stop[1] > stop[2]:
            depart_after_lines.append(stop[3])
    return depart_after_lines


if __name__ == "__main__":
    main()
