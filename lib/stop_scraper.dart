import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:html/parser.dart' show parse;
import 'package:http/http.dart' as http;

Future<void> main(List<String> arguments) async {
  if (arguments.isEmpty) {
    print('Please provide a URL as a command line argument.');
    return;
  }

  final url = arguments[0];
  final atcoCodes = <String>{}; // To avoid duplicates
  final controller = StreamController<Map<String, dynamic>>();

  try {
    print('Fetching HTML from $url...');
    final response = await http.get(Uri.parse(url));

    if (response.statusCode != 200) {
      print('Failed to load page: ${response.statusCode}');
      return;
    }

    final document = parse(response.body);
    final stopLinks = document.querySelectorAll('th.stop-name a');

    if (stopLinks.isEmpty) {
      print('No stop links found. Please check the URL or HTML structure.');
      return;
    }

    print('Found ${stopLinks.length} stop links. Processing...');

    // Start the "Writer Thread" (Consumer)
    final writerDone = _writeStopsStream(controller.stream);

    // Start the "Downloader Thread" (Producer)
    for (var link in stopLinks) {
      final href = link.attributes['href'];
      if (href == null) continue;

      // Extract ATCO code from URL (assuming format /stops/ATCO_CODE)
      final uri = Uri.parse(href);
      final segments = uri.pathSegments;
      if (segments.isEmpty) continue;

      final atcoCode = segments.last;

      if (atcoCodes.contains(atcoCode)) {
        continue;
      }
      atcoCodes.add(atcoCode);

      print('Fetching details for stop $atcoCode...');
      try {
        final apiResponse = await http.get(
          Uri.parse('https://bustimes.org/api/stops/?atco_code=$atcoCode'),
        );

        if (apiResponse.statusCode == 200) {
          final data = jsonDecode(apiResponse.body);
          Map<String, dynamic>? stopData;

          if (data is Map<String, dynamic> && data.containsKey('results')) {
            final results = data['results'];
            if (results is List && results.isNotEmpty) {
              stopData = results[0];
            }
          } else if (data is List && data.isNotEmpty) {
            stopData = data[0];
          } else if (data is Map<String, dynamic>) {
            stopData = data;
          }

          if (stopData != null) {
            controller.add(stopData);
          }
        } else {
          print(
            'Failed to get API data for $atcoCode: ${apiResponse.statusCode}',
          );
        }
      } catch (e) {
        print('Error fetching API for $atcoCode: $e');
      }

      // Be nice to the API
      await Future.delayed(Duration(milliseconds: 100));
    }

    // Close the controller when we're done downloading
    await controller.close();

    // Wait for the writer to finish
    await writerDone;
  } catch (e) {
    print('An error occurred: $e');
  } finally {
    if (!controller.isClosed) {
      await controller.close();
    }
  }
}

Future<void> _writeStopsStream(Stream<Map<String, dynamic>> stopStream) async {
  final file = File('temp_stops.txt');
  final sink = file.openWrite(mode: FileMode.append);

  await for (final stop in stopStream) {
    final buffer = StringBuffer();

    final atcoCode = stop['atco_code'] ?? '';
    String commonName = stop['common_name'] ?? '';
    commonName = commonName.replaceFirst(" / ", ", ");

    // Extract location from [lon, lat] list
    String locationString;
    if (stop['location'] is List && (stop['location'] as List).length >= 2) {
      final loc = stop['location'] as List;
      final lon = loc[0];
      final lat = loc[1];
      locationString =
          '[\n                $lon,\n                $lat\n            ]';
    } else {
      locationString = '[]';
    }

    buffer.writeln(
      'Add a new stop to stops.txt. repeat the name for tts unless it is manx worded in which case spell it so it would be pronounced properly. if the stop/stand is a shelter use location type 0, if it is a sign use type 4. keep wheelchair boaridng blank. if i give you a duplicate atco code tell me and dont modify or add anything. use the data below for the fields they relate to:',
    );
    buffer.writeln('            "atco_code": "$atcoCode",');
    buffer.writeln('            "common_name": "$commonName",');
    buffer.writeln('            "location": $locationString,');
    buffer.writeln(); // Empty line
    buffer.writeln(); // Couple of newlines as requested

    sink.write(buffer.toString());
    await sink.flush(); // Ensure it's written as it comes
  }

  await sink.close();
  print('Writer finished. Results saved to ${file.path}');
}
