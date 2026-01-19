import 'dart:io';
import 'dart:convert';

void main() async {
  final stopsFile = File('dataset/stops.txt');
  final tempStopsFile = File('temp_stops.txt');

  if (!stopsFile.existsSync() || !tempStopsFile.existsSync()) {
    print('Missing files');
    return;
  }

  final existingStops = <String>{};
  final stopsLines = await stopsFile.readAsLines();
  if (stopsLines.isNotEmpty) {
    for (var i = 1; i < stopsLines.length; i++) {
      final parts = stopsLines[i].split(',');
      if (parts.isNotEmpty) {
        existingStops.add(parts[0].trim());
      }
    }
  }

  final tempStopsContent = await tempStopsFile.readAsString();
  final stopBlocks = tempStopsContent.split('Add a new stop to stops.txt.');

  final newStops = <String>[];
  final duplicates = <String>[];

  for (var block in stopBlocks) {
    if (block.trim().isEmpty) continue;

    final atcoMatch = RegExp(r'"atco_code":\s*"([^"]+)"').firstMatch(block);
    final nameMatch = RegExp(r'"common_name":\s*"([^"]+)"').firstMatch(block);
    final locMatch = RegExp(
      r'"location":\s*\[\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*\]',
    ).firstMatch(block);

    if (atcoMatch == null || nameMatch == null) continue;

    final atcoCode = atcoMatch.group(1)!;
    final commonName = nameMatch.group(1)!;

    if (existingStops.contains(atcoCode)) {
      duplicates.add(atcoCode);
      continue;
    }

    double lat = 0;
    double lon = 0;
    if (locMatch != null) {
      lon = double.parse(locMatch.group(1)!);
      lat = double.parse(locMatch.group(2)!);
    }

    final ttsName = expandTts(commonName);
    final locationType = commonName.toLowerCase().contains('shelter') ? 0 : 4;

    // stop_id,stop_name,tts_stop_name,stop_lat,stop_lon,location_type,wheelchair_boarding
    final csvLine =
        '$atcoCode,"$commonName","$ttsName",$lat,$lon,$locationType,';
    newStops.add(csvLine);
    existingStops.add(atcoCode);
  }

  if (duplicates.isNotEmpty) {
    print('Duplicates found and skipped: ${duplicates.join(', ')}');
  }

  if (newStops.isNotEmpty) {
    final sink = stopsFile.openWrite(mode: FileMode.append);
    for (var stop in newStops) {
      sink.writeln(stop);
      print('Added: $stop');
    }
    await sink.close();
    print('Added ${newStops.length} new stops.');
  } else {
    print('No new stops to add.');
  }
}

String expandTts(String name) {
  var tts = name;

  tts = tts.replaceAll('MER', 'Manx Electric Railway');
  tts = tts.replaceAll('Prom', 'Promenade');
  tts = tts.replaceAll('No.', 'Number');

  final manxRules = {
    'Anagh Coar': 'Anna-kuh',
    'Ballacreggan': 'Ba-la-kreg-an',
    'Ballasalla': 'Ba-la-sal-a',
    'Ballabeg': 'Ba-la-beg',
    'Ballakeighan': 'Ba-la-keen',
    'Ballalough': 'Ba-la-lock',
    'Ballafesson': 'Ba-la-fess-un',
    'Ballagawne': 'Ba-la-gown',
    'Ballastrang': 'Ba-la-strong',
    'Ballalonna': 'Ba-la-lon-a',
    'Port-E-Chee': 'Port-uh-Chee',
    'Croit-E-Caley': 'Kret-uh-Kay-lee',
    'Cooil': 'Keel',
    'Reayrt': 'Ree-ert',
    'Cronk-Y-Berry': 'Krongk-uh-Berry',
    'Reayrt-Y-Sheer': 'Ree-ert-uh-Sheer',
  };

  manxRules.forEach((key, value) {
    tts = tts.replaceAll(RegExp(key, caseSensitive: false), value);
  });

  return tts;
}
