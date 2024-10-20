# fileintegrity-monitor
A python script to monitor checksums of your files and detect possible data corruption as well as changed files.

# How it works
To detect data corruption, the script compares the current file modification timestamps with the ones from an index file.
If the modification timestamp didn't change, but the checksums are different, there is a possibility of data corruption.
The index file can be updated automatically if new files, or changed files with a different timestamp are detected, therefore a full rescan isn't needed.

The index file is stored in the directory you specify to scan. The file is called ".metadata.csv" and is hidden on windows as well as linux systems by default.

# What it can't do
This tool can't detect file corruption of files that have been changed and there was no rescan performed before the data corruption.

# Installation
```sh
git clone https://github.com/SURFER00/fileintegrity-monitor.git fileintegrity-monitor
pip install -r fileintegrity-monitor/requirements.txt
```

# Usage

To create a completely new index file you need to use this command:
```sh
python integrity-monitor.py create <dir_path>
```

If you want to check if there are corrupted files and automatically update the index file on valid changed files, execute:
```sh
python integrity-monitor.py monitor <dir_path>
```

If you only want to check the files but not update the index file, execute:
```sh
python integrity-monitor.py check <dir_path>
```
