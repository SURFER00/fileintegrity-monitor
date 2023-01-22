import argparse, csv, hashlib, os, progressbar, re, subprocess, time
from os.path import exists

black = "\033[0;30m"
red = "\033[0;31m"
green = "\033[0;32m"
yellow = "\033[0;33m"
blue = "\033[0;34m"
magenta = "\033[0;35m"
cyan = "\033[0;36m"
white = "\033[0;37m"
bright_black = "\033[0;90m"
bright_red = "\033[0;91m"
bright_green = "\033[0;92m"
bright_yellow = "\033[0;93m"
bright_blue = "\033[0;94m"
bright_magenta = "\033[0;95m"
bright_cyan = "\033[0;96m"
bright_white = "\033[0;97m"

metadata_file_path = "\\.metadata.csv"
verbose = False

parser = argparse.ArgumentParser()

def hash(path):
    try:
        fileHandle = open(path, "rb")
    except IOError:
        return
    m5Hash = hashlib.md5()
    while True:
        data = fileHandle.read(8192)
        if(not data):
            break
        m5Hash.update(data)
    fileHandle.close()
    return m5Hash.hexdigest()

def scanTree(path):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if(entry.is_dir(follow_symlinks=False)):
            yield from scanTree(entry.path) 
        else:
            yield entry

def create(path):
	start_time = time.perf_counter()
	
	metadata_file = open(path + metadata_file_path, "w", newline="", encoding="utf-8")
	metadata = csv.DictWriter(metadata_file, fieldnames=['path', 'hash', 'mtime'])

	'''Hide metadata file on windows systems'''
	if(os.name == "nt"):
		subprocess.check_call(["attrib", "+H", path + metadata_file_path])

	'''Write table header information'''
	metadata.writeheader()
	
	files = []
	total = 0

	print("Getting directory structure...")
	for entry in scanTree(path):
		if(entry.is_file()):
			if(entry.path == path + metadata_file_path): continue
			files.append(entry)
			total += 1

	widgets = ['Creating metadata... ',
			progressbar.Percentage(),
			" ",
			progressbar.Bar('█'),
			" ",
			progressbar.Counter(format='%(value)d/' + str(total)),
			" ",
			progressbar.Timer(format= '%(elapsed)s'),
			" ",
			progressbar.ETA()
			]

	bar = progressbar.ProgressBar(max_value=total,
								widgets=widgets).start()
	
	'''Get metadata from files and store information in metadata table'''
	progress = 0
	for entry in files:
		fhash = hash(entry.path)
		mtime = os.path.getmtime(entry.path)
		relpath = os.path.relpath(entry.path, path)
		metadata.writerow({'path':relpath, 'hash':fhash, 'mtime':mtime})
		printVerbose({'path':relpath, 'metadata_hash':fhash,'metadata_mtime':mtime})
		bar.update(progress) 
		progress += 1
	
	bar.finish()
	metadata_file.close()

	end_time = time.perf_counter()
	print(f"\nScan took about {round(end_time - start_time, 1)}s")
	

def check(path, update=True):
	start_time = time.perf_counter()

	'''Pivot metadata to path column'''

	if not exists(path + metadata_file_path):
		print("No metadata file found!")
		create(path)
		return

	print("Opening metadata table...")
	metadata_file = open(path + metadata_file_path, "r", encoding="utf-8")
	metadata = csv.DictReader(metadata_file, fieldnames=['path', 'hash', 'mtime'])
	metadata_pivot = dict()

	'''Pivot metadata table to path column'''

	print("Pivoting table to path column...")
	for row in metadata:
		metadata_pivot[row['path']] = {'hash':row['hash'], 'mtime':row['mtime']}
		printVerbose(str(row) + " -> \"" + row['path'] + "\":" + str({'hash':row['hash'], 'mtime':row['mtime']}))
	
	'''Check metadata'''

	print("Getting directory structure...")

	files = []
	total = 0
	for entry in scanTree(path):
		if(entry.is_file()):
			if(entry.path == path + metadata_file_path): continue
			files.append(entry)
			total += 1

	print("Comparing metadata to current state...")

	widgets = ['Checking... ',
			progressbar.Percentage(),
			" ",
			progressbar.Bar('█'),
			" ",
			progressbar.Counter(format='%(value)d/' + str(total)),
			" ",
			progressbar.Timer(format= '%(elapsed)s'),
			" ",
			progressbar.ETA()
			]

	bar = progressbar.ProgressBar(max_value=total,
								widgets=widgets).start()
	
	new_metadata = []
	changes = []

	corrupted = 0
	changed = 0
	new = 0
	total = 0

	'''Compare current metadata to metadata table and check file integrity'''
	for entry in files:
		current_hash = hash(entry.path)
		current_mtime = os.path.getmtime(entry.path)
		relpath = os.path.relpath(entry.path, path)
		data = {'path':relpath, 'current_hash':current_hash, 'current_mtime':current_mtime}
		if(relpath in metadata_pivot):
			metadata_hash = metadata_pivot[relpath]['hash']
			metadata_mtime = float(metadata_pivot[relpath]['mtime'])
			data.update({'path':relpath, 'metadata_hash':metadata_hash,'current_hash':current_hash,'metadata_mtime':metadata_mtime,'current_mtime':current_mtime})
			if(metadata_hash != current_hash):
				if(metadata_mtime == current_mtime):
					'''Files that are possibly corrupted'''
					corrupted += 1
					data.update({'flag':1})
					changes.append(data)
					'''Keep old data so the error does't go away on next scan (keep metadata values and not the new values)'''
					new_metadata.append({'path':relpath, 'hash':metadata_hash, 'mtime':metadata_mtime})
				else:
					'''Files that have changed'''
					changed += 1
					data.update({'flag':2})
					changes.append(data)
					new_metadata.append({'path':relpath, 'hash':current_hash, 'mtime':current_mtime})
			else:
				'''Files that haven't changed'''
				new_metadata.append({'path':relpath, 'hash':current_hash, 'mtime':current_mtime})
		else:
			'''Files that aren't in metadata'''
			new += 1
			data.update({'flag':3})
			changes.append(data)
			new_metadata.append({'path':relpath, 'hash':current_hash, 'mtime':current_mtime})
		total += 1
		bar.update(total)
		printVerbose(data)

	bar.finish()
	metadata_file.close()

	'''Update metadata table to new version'''
	if(update):
		if(changed != 0 or new != 0 or total < len(metadata_pivot)-1):
			print("Writing new metadata...")
			subprocess.check_call(["attrib", "-H", path + metadata_file_path])
			metadata_file = open(path + metadata_file_path, "w", newline="", encoding="utf-8")
			subprocess.check_call(["attrib", "+H", path + metadata_file_path])
			metadata = csv.DictWriter(metadata_file, fieldnames=['path', 'hash', 'mtime'])
			metadata.writeheader()
			for entry in new_metadata:
				metadata.writerow(entry)
				printVerbose(str(entry))
			metadata_file.close()
		else:
			print("No changed, new or removed files. Skipping metadata update...")

	print("\nTotal number of processed files: " + str(total))
	print("Number of new files: " + str(new))
	print("Number of changed files: " + str(changed))
	print("Number of corrupted files: " + str(corrupted))
	if(corrupted != 0):
		print(red + "\nContents of some files have changed without changing the modification timestamp!")
		print("Possible data corruption detected!\n" + white)
		print("List of possibly corrupted files:")
		for entry in changes:
			if entry["flag"] == 1:
				print(entry)
	
	end_time = time.perf_counter()
	print(f"\nScan took about {round(end_time - start_time, 1)}s")

def printVerbose(str):
	if(verbose): print(str)

def printHelp():
	parser.print_help()
	

def main():
	parser.add_argument('command', metavar='command', nargs=1, help='Available commands: create (write-only), check (check only/read-only), monitor (update table after scan)')
	parser.add_argument('path', metavar='path', nargs=1, help='Path of the root folder')
	parser.add_argument('-v', '--verbose', action='store_true', help="Verbose")
	try:
		args = parser.parse_args()
	except argparse.ArgumentError:
		printHelp()
		return
	if(args.verbose):
		global verbose
		verbose = True
	
	'''Strip backslash and quotes at the end of the path'''
	args.path[0] = re.sub('\\"$', '', args.path[0])

	if(args.command[0] == "create"):
		create(args.path[0])
	if(args.command[0] == "check"):
		check(args.path[0], False)
	if(args.command[0] == "monitor"):
		check(args.path[0], True)

if __name__ == '__main__':
	main()