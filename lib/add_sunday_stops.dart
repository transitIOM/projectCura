import 'dart:io';

/// Script to add Sunday/Public Holiday trip stops to stop_times.txt
/// Reads merged.csv and generates entries following GTFS format
void main() async {
  final projectRoot = Directory.current;
  final datasetDir = Directory('${projectRoot.path}/dataset');
  final tempDir = Directory('${projectRoot.path}/dataset_temp');

  // Manual mapping for stops that don't match exactly
  final Map<String, String> manualMapping = {
    'Douglas, Lord Street': '891085000102',
    'Lord Street, Hanover House': '891085000109',
    'Clinch\'s House Lord Street': '891085000110',
    'Horses Home Southbound': '891085000301',
    'Peel Road Brown Bobby': '891085000111',
    'Middle River Industrial Estate': '891085001103',
    'Groves Road / Power Station': '891085000203',
    'National Sports Centre, Groves Road': '891085000205',
    'Groves Road / Springfield Avenue': '891085000207',
    'Anagh Coar entrance / Castletown Road': '891085010302',
    'Hampton Farm Estate, layby': '891085010304',
    'Four Roads shelter, Anagh Coar': '891085010305',
    'Mount Murray / Ballacutchell Road': '891085000307',
    'Santon School Layby': '891085000311',
    'Santon Railway Station Towards Castletown': '891085000315',
    'Orrisdale Road / Ballacreggan': '891085010407',
    'Ballasalla Main Stop Southbound': '891085000405',
    'Ballasalla Station / The Paddocks': '891085000407',
    'Victoria Road / Bowling Green Road': '891085000607',
    'Castletown Station / The Sidings': '891085000609',
    'Victoria Road Primary School': '891085000611',
    'Victoria Road / Brewery Wharf': '891085000613',
    'Castletown Square / The Parade': '891085000615',
    'Farrants Way / Kissack Road': '891085000617',
    'Red Gapp / Royal Life': '891085000621',
    'Ballabeg Hall, shelter': '891085000709',
    'The Level / Croit-E-Caley Junction': '891085010709',
    'Colby, opposite Carrick Bay View': '891085010711',
    'Ballafesson, shelter': '891085011903',
  };

  // Read stops.txt to build name->id mapping
  final stopsFile = File('${datasetDir.path}/stops.txt');
  final stopsLines = await stopsFile.readAsLines();

  final Map<String, String> stopNameToId = {};
  for (final line in stopsLines.skip(1)) { // Skip header
    if (line.trim().isEmpty) continue;
    final parts = line.split(',');
    if (parts.length >= 2) {
      final stopId = parts[0].trim();
      final stopName = parts[1].trim().replaceAll('"', '');
      if (stopId.isNotEmpty && stopName.isNotEmpty) {
        stopNameToId[stopName] = stopId;
      }
    }
  }

  print('Loaded ${stopNameToId.length} stops');

  // Read merged.csv
  final mergedFile = File('${tempDir.path}/merged.csv');
  final mergedLines = await mergedFile.readAsLines();

  // Trips start at: 07:50, 08:50, 13:05
  final tripStartTimes = ['0750', '0850', '1305'];
  final List<List<String>> trips = [[], [], []];

  int stopSequence = 1;

  for (final line in mergedLines) {
    if (line.trim().isEmpty) continue;

    // Parse CSV - format: "stop_name",time1,time2,time3
    // Use simple CSV parsing for quoted first field
    final quoteIndex = line.indexOf('"');
    if (quoteIndex == -1) continue;

    final endQuoteIndex = line.indexOf('"', quoteIndex + 1);
    if (endQuoteIndex == -1) continue;

    final stopName = line.substring(quoteIndex + 1, endQuoteIndex).trim();

    // Skip blank stop names (these appear to be waypoints)
    if (stopName.isEmpty) {
      stopSequence++;
      continue;
    }

    // Get the times after the closing quote
    final timesPart = line.substring(endQuoteIndex + 1);
    final times = timesPart.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();

    if (times.length < 3) {
      print('Warning: Skipping line with insufficient times: $line');
      continue;
    }

    final time1 = times[0]; // 07:xx
    final time2 = times[1]; // 08:xx
    final time3 = times[2]; // 13:xx

    // Try to find stop_id
    String? stopId = manualMapping[stopName];

    if (stopId == null) {
      stopId = stopNameToId[stopName];
    }

    if (stopId == null) {
      print('Warning: No stop_id found for "$stopName"');
      stopSequence++;
      continue;
    }

    // Generate stop_time entries for each trip
    // Format: trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type
    for (var i = 0; i < tripStartTimes.length; i++) {
      final time = i == 0 ? time1 : (i == 1 ? time2 : time3);
      final tripId = '1_SPH_${tripStartTimes[i]}';
      trips[i].add('$tripId,$time,$time,$stopId,$stopSequence,0,0');
    }

    stopSequence++;
  }

  // Append to stop_times.txt
  final stopTimesFile = File('${datasetDir.path}/stop_times.txt');
  final sink = stopTimesFile.openWrite(mode: FileMode.append);

  for (var i = 0; i < trips.length; i++) {
    for (final entry in trips[i]) {
      sink.writeln(entry);
    }
  }
  await sink.close();

  final totalEntries = trips.fold<int>(0, (sum, t) => sum + t.length);
  print('Added $totalEntries stop_times entries');

  // Append trips to trips.txt
  final tripsFile = File('${datasetDir.path}/trips.txt');
  final tripsSink = tripsFile.openWrite(mode: FileMode.append);

  for (final startTime in tripStartTimes) {
    final tripId = '1_SPH_$startTime';
    tripsSink.writeln('1,SPH,$tripId,Douglas - Airport - Castletown - Port Erin,0,');
  }
  await tripsSink.close();
  print('Added ${tripStartTimes.length} trip entries to trips.txt');

  // Update calendar.txt with SPH service
  final calendarFile = File('${datasetDir.path}/calendar.txt');
  final calendarLines = await calendarFile.readAsLines();

  // Check if SPH already exists
  final hasSPH = calendarLines.any((line) => line.startsWith('SPH,'));
  if (!hasSPH) {
    final calendarSink = calendarFile.openWrite(mode: FileMode.append);
    calendarSink.writeln('SPH,0,0,0,0,0,0,1,20260101,20261231');
    await calendarSink.close();
    print('Added SPH service to calendar.txt');
  } else {
    print('SPH service already exists in calendar.txt');
  }

  print('Done!');
}
