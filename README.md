# Python File Integrity Monitor
A python script to monitor checksums of your files and detect possible data corruption as well as changed files.

# How it works
To detect data corruption, the script compares the current file modification timestamps with the ones from an index file.
If the modification timestamp didn't change, but the checksums are different, there is a possibility of data corruption.
The index file can be updated automatically if new files, or valid changed files are detected, therefore a full rescan isn't needed.
