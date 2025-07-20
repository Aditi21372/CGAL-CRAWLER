# Let me create the complete project structure and all necessary files
import os
import json

# Create the main project directory structure
directories = [
    "cgal-github-crawler",
    "cgal-github-crawler/src",
    "cgal-github-crawler/config", 
    "cgal-github-crawler/data",
    "cgal-github-crawler/logs",
    "cgal-github-crawler/results",
    "cgal-github-crawler/templates",
    "cgal-github-crawler/static/css",
    "cgal-github-crawler/static/js",
    "cgal-github-crawler/tests"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    
print("Directory structure created successfully!")
print("Directories created:")
for directory in directories:
    print(f"  - {directory}")