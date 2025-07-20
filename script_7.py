# Create the Flask web application
web_app_content = '''"""
CGAL GitHub Crawler Web Interface
Flask web application providing a user interface for the crawler.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from threading import Thread
import time

from src.crawler import CGALGitHubCrawler, CrawlerConfig, CrawlerStats
from src.database import DatabaseManager
from src.analyzer import CGALPatternAnalyzer

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cgal-crawler-secret-key-change-this')

# Global variables
crawler_instance = None
crawler_thread = None
crawler_running = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_crawler_config():
    """Get crawler configuration from environment variables."""
    return CrawlerConfig(
        github_token=os.getenv('GITHUB_TOKEN', ''),
        max_requests_per_minute=int(os.getenv('MAX_REQUESTS_PER_MINUTE', 10)),
        max_repositories=int(os.getenv('MAX_REPOSITORIES', 100)),
        max_files_per_repo=int(os.getenv('MAX_FILES_PER_REPO', 50)),
        search_delay_seconds=int(os.getenv('SEARCH_DELAY_SECONDS', 6)),
        max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', 3)),
        timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', 30)),
        database_path=os.getenv('DATABASE_PATH', 'data/cgal_crawler.db')
    )

@app.route('/')
def index():
    """Main dashboard page."""
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        stats = db.get_statistics()
        repositories = db.get_all_repositories()[:10]  # Get top 10 repositories
        
        return render_template('index.html', 
                             stats=stats, 
                             repositories=repositories,
                             crawler_running=crawler_running)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', 
                             stats={}, 
                             repositories=[],
                             crawler_running=crawler_running,
                             error=str(e))

@app.route('/repositories')
def repositories():
    """Repository listing page."""
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        
        all_repos = db.get_all_repositories()
        total_repos = len(all_repos)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        repos = all_repos[start_idx:end_idx]
        
        # Pagination info
        total_pages = (total_repos + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('repositories.html',
                             repositories=repos,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             total_repos=total_repos)
    except Exception as e:
        logger.error(f"Error loading repositories: {e}")
        return render_template('repositories.html', 
                             repositories=[], 
                             error=str(e))

@app.route('/repository/<int:repo_id>')
def repository_detail(repo_id):
    """Repository detail page."""
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        # Get repository details
        repo = None
        all_repos = db.get_all_repositories()
        for r in all_repos:
            if r['id'] == repo_id:
                repo = r
                break
                
        if not repo:
            flash('Repository not found', 'error')
            return redirect(url_for('repositories'))
            
        # Get files for this repository
        files = db.get_files_by_repository(repo_id)
        
        # Analyze CGAL usage patterns
        analyzer = CGALPatternAnalyzer()
        file_analyses = []
        
        for file_data in files:
            if file_data.get('content'):
                analysis = analyzer.analyze_file_content(file_data['content'], file_data['file_path'])
                domains = analyzer.get_cgal_domain_hints(analysis)
                file_analyses.append({
                    'file': file_data,
                    'analysis': analysis,
                    'domains': domains
                })
                
        return render_template('repository_detail.html',
                             repository=repo,
                             files=files,
                             file_analyses=file_analyses)
    except Exception as e:
        logger.error(f"Error loading repository {repo_id}: {e}")
        flash(f'Error loading repository: {e}', 'error')
        return redirect(url_for('repositories'))

@app.route('/crawler')
def crawler_control():
    """Crawler control page."""
    config = get_crawler_config()
    
    # Check if GitHub token is configured
    token_configured = bool(config.github_token and config.github_token != 'your_github_personal_access_token_here')
    
    # Get rate limit info if token is configured
    rate_limit_info = {}
    if token_configured and not crawler_running:
        try:
            temp_crawler = CGALGitHubCrawler(config)
            rate_limit_info = temp_crawler.get_rate_limit_info()
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            
    return render_template('crawler.html',
                         config=config,
                         token_configured=token_configured,
                         rate_limit_info=rate_limit_info,
                         crawler_running=crawler_running)

@app.route('/start_crawler', methods=['POST'])
def start_crawler():
    """Start the crawler in a background thread."""
    global crawler_instance, crawler_thread, crawler_running
    
    if crawler_running:
        flash('Crawler is already running', 'warning')
        return redirect(url_for('crawler_control'))
        
    config = get_crawler_config()
    
    if not config.github_token or config.github_token == 'your_github_personal_access_token_here':
        flash('GitHub token not configured. Please set GITHUB_TOKEN environment variable.', 'error')
        return redirect(url_for('crawler_control'))
        
    try:
        # Get custom queries from form
        queries = []
        if request.form.get('query_cgal'):
            queries.append("CGAL language:C++")
        if request.form.get('query_include'):
            queries.append("#include <CGAL/ language:C++")
        if request.form.get('query_namespace'):
            queries.append("using namespace CGAL language:C++")
        if request.form.get('query_qualified'):
            queries.append("CGAL:: language:C++")
            
        custom_query = request.form.get('custom_query', '').strip()
        if custom_query:
            queries.append(custom_query)
            
        if not queries:
            queries = ["CGAL language:C++"]  # Default query
            
        # Update config with form values
        if request.form.get('max_repositories'):
            config.max_repositories = int(request.form.get('max_repositories'))
        if request.form.get('max_files_per_repo'):
            config.max_files_per_repo = int(request.form.get('max_files_per_repo'))
            
        # Start crawler in background thread
        crawler_instance = CGALGitHubCrawler(config)
        crawler_thread = Thread(target=run_crawler_background, args=(crawler_instance, queries))
        crawler_thread.daemon = True
        crawler_thread.start()
        
        crawler_running = True
        flash(f'Crawler started with {len(queries)} search queries', 'success')
        
    except Exception as e:
        logger.error(f"Error starting crawler: {e}")
        flash(f'Error starting crawler: {e}', 'error')
        
    return redirect(url_for('crawler_control'))

def run_crawler_background(crawler, queries):
    """Run crawler in background thread."""
    global crawler_running
    
    try:
        logger.info("Starting background crawl")
        result = crawler.run_crawl(queries)
        logger.info(f"Background crawl completed: {result}")
        
    except Exception as e:
        logger.error(f"Background crawl error: {e}")
    finally:
        crawler_running = False

@app.route('/stop_crawler', methods=['POST'])
def stop_crawler():
    """Stop the crawler (this is a simple implementation)."""
    global crawler_running
    
    crawler_running = False
    flash('Crawler stop requested (may take a moment to finish current operations)', 'info')
    return redirect(url_for('crawler_control'))

@app.route('/api/crawler/status')
def api_crawler_status():
    """API endpoint for crawler status."""
    global crawler_instance, crawler_running
    
    if not crawler_instance or not crawler_running:
        return jsonify({
            'running': False,
            'stats': {}
        })
        
    stats = crawler_instance.stats.get_stats_dict()
    
    return jsonify({
        'running': crawler_running,
        'stats': stats
    })

@app.route('/api/repositories')
def api_repositories():
    """API endpoint for repository data."""
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        repositories = db.get_all_repositories()
        return jsonify({
            'success': True,
            'repositories': repositories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/statistics')
def api_statistics():
    """API endpoint for crawler statistics."""
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        stats = db.get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/export')
def export_data():
    """Export data page."""
    return render_template('export.html')

@app.route('/export/csv')
def export_csv():
    """Export repository data as CSV."""
    import pandas as pd
    from io import StringIO
    from flask import Response
    
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        repositories = db.get_all_repositories()
        df = pd.DataFrame(repositories)
        
        output = StringIO()
        df.to_csv(output, index=False)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=cgal_repositories.csv'}
        )
    except Exception as e:
        flash(f'Error exporting CSV: {e}', 'error')
        return redirect(url_for('export_data'))

@app.route('/export/json')
def export_json():
    """Export repository data as JSON."""
    from flask import Response
    
    db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/cgal_crawler.db'))
    
    try:
        repositories = db.get_all_repositories()
        
        return Response(
            json.dumps(repositories, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=cgal_repositories.json'}
        )
    except Exception as e:
        flash(f'Error exporting JSON: {e}', 'error')
        return redirect(url_for('export_data'))

if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run Flask app
    host = os.getenv('FLASK_HOST', 'localhost')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
'''

with open("cgal-github-crawler/app.py", "w") as f:
    f.write(web_app_content)

print("Flask Web Application created: app.py")
print("Features included:")
print("- Dashboard with statistics")
print("- Repository browsing and search")
print("- Repository detail views")
print("- Crawler control interface")
print("- Real-time crawler status")
print("- Data export (CSV/JSON)")
print("- REST API endpoints")
print("- Rate limit monitoring")
print("- Configuration management")