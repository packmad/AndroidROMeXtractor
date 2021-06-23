# AndroidROMeXtractor

This project is a python3 wrapper to several tools/scripts to unpack Android ROMs, and has been designed to work only and exclusively with Docker (because of all the crazy dependencies).




## Credits
This software was developed at [Eurecom](https://www.eurecom.fr/) for the paper: *"Trust, But Verify: A Longitudinal Analysis Of Android OEM Compliance and Customization"* [[PDF](http://s3.eurecom.fr/docs/oakland21_pox.pdf)] [[Bibtex](http://s3.eurecom.fr/bibs/oakland21_pox.bib)] [[Video](https://www.youtube.com/watch?v=Giy7JZRbADc)]


## Setup

Clone the project (important: submodules!) and build the image:
```bash
git clone https://github.com/packmad/AndroidROMeXtractor.git
git submodule update --init --recursive
docker build -t arx .
```

## Run

Helper script for local run:
```bash
./docker_local_rom.sh <absolute/path/on/host/ROM_name.ext>
```

Run script on all files in a directory:
```bash
for f in <absolute/path/>*; do ./docker_local_rom.sh $f >> log.txt ; done
```


## Disclaimer

We share this tool for reproducibility of our experiments.
However, this software is a prototype that grew out of control during development as we encountered new formats and the quality of the code has definitely been affected.

We do not plan to maintain this code, but any contributions are welcome: just send a PR!
