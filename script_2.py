# Create .env.example file
env_example_content = """# GitHub API Configuration
GITHUB_TOKEN=your_github_personal_access_token_here

# Rate Limiting Configuration
MAX_REQUESTS_PER_MINUTE=10
MAX_REPOSITORIES=100
MAX_FILES_PER_REPO=50

# Database Configuration  
DATABASE_PATH=data/cgal_crawler.db

# Crawler Behavior
SEARCH_DELAY_SECONDS=6
MAX_CONCURRENT_REQUESTS=3
TIMEOUT_SECONDS=30

# Output Configuration
RESULTS_DIR=results
LOG_LEVEL=INFO
EXPORT_FORMAT=csv,json

# Web Interface Configuration
FLASK_HOST=localhost
FLASK_PORT=5000
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here-change-this

# CGAL Pattern Configuration
CGAL_HEADER_PATTERNS=CGAL/Exact_predicates_inexact_constructions_kernel.h,CGAL/Point_2.h,CGAL/Point_3.h,CGAL/Polygon_2.h,CGAL/Delaunay_triangulation_2.h,CGAL/Surface_mesh.h
CGAL_NAMESPACE_PATTERNS=using namespace CGAL,CGAL::

# Search Configuration
SEARCH_QUERIES=include <CGAL,#include <CGAL/,using namespace CGAL,CGAL::
FILE_EXTENSIONS=cpp,hpp,h,cc,cxx
LANGUAGE_FILTER=C++
"""

with open("cgal-github-crawler/.env.example", "w") as f:
    f.write(env_example_content)

# Create .gitignore file
gitignore_content = """# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/*.log
*.log

# Results
results/*.csv
results/*.json
results/*.xlsx

# OS
.DS_Store
Thumbs.db

# Temporary files
temp/
tmp/
*.tmp

# Flask
instance/
.webassets-cache

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml
"""

with open("cgal-github-crawler/.gitignore", "w") as f:
    f.write(gitignore_content)
    
print("Configuration files created:")
print("- .env.example")  
print("- .gitignore")