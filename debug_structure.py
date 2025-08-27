#!/usr/bin/env python3
import os

# Check the current working directory and file structure
print("Current working directory:", os.getcwd())
print("\nFiles in current directory:")
for item in os.listdir('.'):
    print(f"  {item}")

print("\nChecking Templates directory:")
if os.path.exists('Templates'):
    print("Templates directory exists!")
    print("Files in Templates:")
    for item in os.listdir('Templates'):
        print(f"  {item}")
    print(f"index.html exists: {os.path.exists('Templates/index.html')}")
else:
    print("Templates directory NOT found!")

print("\nChecking Static directory:")
if os.path.exists('Static'):
    print("Static directory exists!")
    print("Subdirectories in Static:")
    for item in os.listdir('Static'):
        print(f"  {item}")
else:
    print("Static directory NOT found!")
