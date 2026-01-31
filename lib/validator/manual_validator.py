import csv


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


def main():
    filePath = "../../dataset/stop_times.txt"
    trips = {}
    with open(filePath, newline="\n") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        line_number = 2  # Start at line 2 since we skipped the header
        for line in reader:
            (
                trip_id,
                arrival_time,
                departure_time,
                stop_id,
                stop_sequence,
                pickup_type,
                drop_off_type,
            ) = line
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

    print("\nSummary:")
    print(f"  Total trips: {len(trips)}")
    print(f"  Valid trips: {valid_count}")
    print(f"  Trips with overlap: {overlap_count}")
    print(f"  Trips with departure before arrival: {depart_after_count}")


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
