![](https://github.com/user-attachments/assets/7b02c861-0e44-4d8b-8425-4b1e3b038889)

Project Cura is transitIOM's independent GTFS dataset for the Isle of Man bus service. We use LLMS for fast, semantically-described updates to the dataset which, once validated, allow us to keep the dataset up to date with Bus Vannin's service changes without the need for manual data entry or reliance on them for new data.

## Download

Simply head to the [releases page](https://github.com/transitIOM/projectCura/releases) and download the latest release. Our feed comes in a zip file, as specified in the GTFS spec.

## Usage

We welcome use of our dataset in other projects, but please credit us under the terms of our license (below). The individual files of the feed are in the `dataset` folder. Scripts for updating or manipulating the dataset are in the `lib` folder, including validation in `lib/validator`. 

By installing [Just](https://github.com/casey/just), you can make use of our justfile. For example:

```bash
# Validate the dataset
just validate

# Build the dataset
just build
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)