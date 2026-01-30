import 'dart:convert';
import 'dart:io';

void main() async {
  final descriptionsFile = File('lib/route_descriptions.json');
  final colorsFile = File('lib/route_colors.json');
  final outputFile = File('dataset/routes.txt');

  Map<String, String> descriptions = {};
  if (await descriptionsFile.exists()) {
    descriptions = Map<String, String>.from(
      jsonDecode(await descriptionsFile.readAsString()),
    );
  }

  Map<String, String> colors = {};
  if (await colorsFile.exists()) {
    colors = Map<String, String>.from(
      jsonDecode(await colorsFile.readAsString()),
    );
  }

  // Define Networks from User Input
  final networks = {
    1: ["3", "3a", "3b", "N3", "X3"],
    2: [
      "1",
      "1a",
      "1h",
      "N1",
      "2",
      "2a",
      "11",
      "11a",
      "12",
      "12a",
      "8",
      "8s",
      "29",
    ],
    3: [
      "5",
      "5a",
      "5c",
      "5j",
      "N5",
      "6",
      "6a",
      "6c",
      "6f",
      "4",
      "4b",
      "4n",
      "14",
      "14b",
      "14c",
    ],
    4: ["15", "21", "21b", "21h", "22", "22a", "22h", "25", "25h"],
    5: ["16", "16b", "16d", "20", "20a", "17k", "18a", "18k", "19c"],
  };

  final csvBuffer = StringBuffer();

  csvBuffer.writeln(
    'route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_url,route_color,route_text_color,route_sort_order,network_id',
  );

  int sortOrder = 1;

  for (var entry in networks.entries) {
    final netId = entry.key;
    final routes = entry.value;

    for (var shortName in routes) {
      final longName =
          descriptions[shortName] ?? ""; 
      var color = colors[shortName] ?? "";
      if (color.startsWith('#')) {
        color = color.substring(1); 
      }

      // Escape long name for CSV
      final escapedLongName = '"$longName"';


      // route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_url,route_color,route_text_color,route_sort_order,network_id
      csvBuffer.writeln(
        '$shortName,BV,$shortName,$escapedLongName,,3,,$color,FFFFFF,$sortOrder,$netId',
      );

      sortOrder++;
    }
  }

  await outputFile.writeAsString(csvBuffer.toString());
  print('Generates routes.txt');
}
