# Create the base HTML template
base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CGAL GitHub Crawler{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            width: 250px;
            background: #2c3e50;
            padding-top: 20px;
        }
        
        .sidebar .nav-link {
            color: #ecf0f1;
            margin: 5px 15px;
            border-radius: 5px;
        }
        
        .sidebar .nav-link:hover, .sidebar .nav-link.active {
            background: #34495e;
            color: #ffffff;
        }
        
        .main-content {
            margin-left: 250px;
            padding: 20px;
        }
        
        .stat-card {
            border-left: 4px solid #007bff;
        }
        
        .stat-card.success { border-left-color: #28a745; }
        .stat-card.warning { border-left-color: #ffc107; }
        .stat-card.info { border-left-color: #17a2b8; }
        .stat-card.danger { border-left-color: #dc3545; }
        
        .code-snippet {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.875em;
            overflow-x: auto;
        }
        
        .cgal-header {
            color: #007bff;
            font-weight: bold;
        }
        
        .pattern-match {
            background: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .status-running { color: #28a745; }
        .status-stopped { color: #dc3545; }
        .status-warning { color: #ffc107; }
        
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            .main-content {
                margin-left: 0;
            }
        }
    </style>
    
    {% block extra_head %}{% endblock %}
</head>
<body>
    <!-- Sidebar -->
    <nav class="sidebar">
        <div class="px-3">
            <h4 class="text-white mb-4">
                <i class="fas fa-code-branch"></i>
                CGAL Crawler
            </h4>
            
            <ul class="nav nav-pills flex-column">
                <li class="nav-item">
                    <a class="nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">
                        <i class="fas fa-dashboard"></i> Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if request.endpoint == 'repositories' %}active{% endif %}" href="{{ url_for('repositories') }}">
                        <i class="fas fa-folder"></i> Repositories
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if request.endpoint == 'crawler_control' %}active{% endif %}" href="{{ url_for('crawler_control') }}">
                        <i class="fas fa-robot"></i> Crawler Control
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if request.endpoint == 'export_data' %}active{% endif %}" href="{{ url_for('export_data') }}">
                        <i class="fas fa-download"></i> Export Data
                    </a>
                </li>
            </ul>
        </div>
    </nav>
    
    <!-- Main Content -->
    <div class="main-content">
        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- Page Content -->
        {% block content %}{% endblock %}
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    
    {% block extra_scripts %}{% endblock %}
</body>
</html>
'''

# Create index/dashboard template  
index_template = '''{% extends "base.html" %}

{% block title %}Dashboard - CGAL GitHub Crawler{% endblock %}

{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <h1>
            <i class="fas fa-dashboard"></i>
            CGAL GitHub Crawler Dashboard
        </h1>
        <p class="text-muted">Discover and analyze C++ projects using the CGAL computational geometry library.</p>
    </div>
</div>

<!-- Statistics Cards -->
<div class="row mb-4">
    <div class="col-lg-3 col-md-6 mb-3">
        <div class="card stat-card success h-100">
            <div class="card-body">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="fas fa-folder fa-2x text-success"></i>
                    </div>
                    <div>
                        <h4 class="mb-1">{{ stats.get('total_repositories', 0) }}</h4>
                        <p class="text-muted mb-0">Repositories</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-lg-3 col-md-6 mb-3">
        <div class="card stat-card info h-100">
            <div class="card-body">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="fas fa-file-code fa-2x text-info"></i>
                    </div>
                    <div>
                        <h4 class="mb-1">{{ stats.get('total_files', 0) }}</h4>
                        <p class="text-muted mb-0">Total Files</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-lg-3 col-md-6 mb-3">
        <div class="card stat-card warning h-100">
            <div class="card-body">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="fas fa-code fa-2x text-warning"></i>
                    </div>
                    <div>
                        <h4 class="mb-1">{{ stats.get('cgal_files', 0) }}</h4>
                        <p class="text-muted mb-0">CGAL Files</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-lg-3 col-md-6 mb-3">
        <div class="card stat-card {% if crawler_running %}success{% else %}danger{% endif %} h-100">
            <div class="card-body">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="fas fa-robot fa-2x {% if crawler_running %}text-success{% else %}text-danger{% endif %}"></i>
                    </div>
                    <div>
                        <h6 class="mb-1 {% if crawler_running %}status-running{% else %}status-stopped{% endif %}">
                            {% if crawler_running %}RUNNING{% else %}STOPPED{% endif %}
                        </h6>
                        <p class="text-muted mb-0">Crawler Status</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Recent Repositories -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-star"></i>
                    Top Repositories by Stars
                </h5>
            </div>
            <div class="card-body">
                {% if repositories %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Repository</th>
                                    <th>Description</th>
                                    <th>Language</th>
                                    <th>Stars</th>
                                    <th>CGAL Files</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for repo in repositories %}
                                <tr>
                                    <td>
                                        <a href="{{ repo.html_url }}" target="_blank" class="text-decoration-none">
                                            <i class="fab fa-github"></i>
                                            {{ repo.full_name }}
                                        </a>
                                    </td>
                                    <td>
                                        <small>{{ (repo.description or '')[:100] }}{% if repo.description and repo.description|length > 100 %}...{% endif %}</small>
                                    </td>
                                    <td>
                                        {% if repo.language %}
                                            <span class="badge bg-secondary">{{ repo.language }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <i class="fas fa-star text-warning"></i>
                                        {{ repo.stars }}
                                    </td>
                                    <td>
                                        <span class="badge bg-info">{{ repo.cgal_files_count or 0 }}</span>
                                    </td>
                                    <td>
                                        <a href="{{ url_for('repository_detail', repo_id=repo.id) }}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-eye"></i>
                                            View
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="text-center mt-3">
                        <a href="{{ url_for('repositories') }}" class="btn btn-primary">
                            <i class="fas fa-list"></i>
                            View All Repositories
                        </a>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <h5>No repositories found</h5>
                        <p class="text-muted">Start the crawler to begin discovering CGAL repositories.</p>
                        <a href="{{ url_for('crawler_control') }}" class="btn btn-primary">
                            <i class="fas fa-robot"></i>
                            Start Crawler
                        </a>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

{% if error %}
<div class="row mt-4">
    <div class="col-12">
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i>
            Error: {{ error }}
        </div>
    </div>
</div>
{% endif %}

{% endblock %}

{% block extra_scripts %}
<script>
// Auto-refresh stats if crawler is running
{% if crawler_running %}
setInterval(function() {
    // Refresh page to update stats
    // In a production app, you would use AJAX to update just the stats
    window.location.reload();
}, 30000); // Refresh every 30 seconds
{% endif %}
</script>
{% endblock %}
'''

# Create the base template file
with open("cgal-github-crawler/templates/base.html", "w") as f:
    f.write(base_template)

# Create the index template file
with open("cgal-github-crawler/templates/index.html", "w") as f:
    f.write(index_template)

print("HTML Templates created:")
print("- templates/base.html (main layout)")
print("- templates/index.html (dashboard)")
print("Template features:")
print("- Responsive Bootstrap design")
print("- Sidebar navigation")
print("- Statistics cards")
print("- Repository table")
print("- Real-time updates")
print("- Font Awesome icons")