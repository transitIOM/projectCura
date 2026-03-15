set windows-shell := ["cmd.exe", "/c"]

[windows]
build:
	powershell -Command "Compress-Archive -Path dataset\* -DestinationPath bin\cura-gtfs.zip -Force"

[windows]
validate:
	powershell -Command "Set-Location ./lib/validator; if ($?) { uv run manual_validator.py }"

[unix]
build:
	zip -r cura-gtfs.zip dataset
	
[unix]
validate:
    cd ./lib/validator && uv run manual_validator.py
