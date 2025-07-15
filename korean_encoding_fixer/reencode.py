#!/opt/homebrew/bin/python3
import os
from sys import argv
import unicodedata

# Gather the target path from the command line arguments or set a default
if len(argv) > 1:
    target_path = argv[1]
else:
    target_path = os.path.expanduser("~/Downloads/")

print("This script will list potential Korean filename encoding fixes in the specified path.")
input('\nTarget: {}\n\nPress <Enter> to continue...'.format(target_path))

def list_files_to_fix(path):
    changes = []
    for root, dirs, files in os.walk(path):
        for entry in files:
            nfc = unicodedata.normalize('NFC', entry)
            if entry != nfc:
                changes.append((entry, nfc))  # Only filenames are stored
            else:
                new_encoding = ''
                do_rename = False
                try:
                    new_encoding = entry.encode('iso-8859-1').decode('euc-kr')
                    do_rename = True
                except UnicodeEncodeError:
                    pass
                except UnicodeDecodeError:
                    n_entry = entry.replace('_', '­')
                    try:
                        new_encoding = n_entry.encode('iso-8859-1').decode('euc-kr')
                        do_rename = True
                    except UnicodeDecodeError:
                        pass
                if entry != new_encoding and do_rename:
                    changes.append((entry, new_encoding))  # Only filenames are stored

    return changes

# Get the list of proposed changes
proposed_changes = list_files_to_fix(target_path)

# Display all proposed changes
print(f"\nThe following {len(proposed_changes)} changes have been proposed:")
for original, new in proposed_changes:
    print(f'{original} --> {new}')

# Ask for confirmation to apply changes
input("\nPress <Enter> to apply these changes or Ctrl+C to abort.")

for original, new in proposed_changes:
    original_path = os.path.join(target_path, original)
    new_path = os.path.join(target_path, new)
    os.rename(original_path, new_path)
    print(f'Renamed "{original}" to "{new}"')

print("All changes applied successfully.")

input('Press <Enter> to exit.')
