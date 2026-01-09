set windows-shell := ["cmd.exe", "/c"]

[windows]
build:
	powershell -Command "Compress-Archive -Path dataset\* -DestinationPath bin\cura-gtfs.zip -Force"

[unix]
build:
	tar -czvf cura-gtfs.zip dataset/*