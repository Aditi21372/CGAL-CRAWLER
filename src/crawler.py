"""
CGAL GitHub Crawler - Main crawler engine
Searches GitHub for C++ repositories using CGAL and analyzes them.
"""

import time
import logging
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Generator
from dataclasses import dataclass
from github import Github, RateLimitExceededException, GithubException
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .analyzer import CGALPatternAnalyzer, CGALAnalysisResult
from .database import DatabaseManager

logger = logging.getLogger('cgal_crawler.crawler')

@dataclass 
class CrawlerConfig:
    """Configuration for the CGAL crawler."""
    github_token: str
    max_requests_per_minute: int = 10
    max_repositories: int = 100
    max_files_per_repo: int = 50
    search_delay_seconds: int = 6
    max_concurrent_requests: int = 3
    timeout_seconds: int = 30
    database_path: str = "data/cgal_crawler.db"

class CrawlerStats:
    """Statistics tracking for crawler operations."""

    def __init__(self):
        self.start_time = datetime.now()
        self.repositories_found = 0
        self.repositories_processed = 0
        self.files_analyzed = 0
        self.cgal_files_found = 0
        self.api_requests_made = 0
        self.errors_encountered = 0
        self.current_repository = ""
        self._lock = threading.Lock()

    def increment_repos_found(self, count: int = 1):
        with self._lock:
            self.repositories_found += count

    def increment_repos_processed(self, count: int = 1):
        with self._lock:
            self.repositories_processed += count

    def increment_files_analyzed(self, count: int = 1):
        with self._lock:
            self.files_analyzed += count

    def increment_cgal_files(self, count: int = 1):
        with self._lock:
            self.cgal_files_found += count

    def increment_api_requests(self, count: int = 1):
        with self._lock:
            self.api_requests_made += count

    def increment_errors(self, count: int = 1):
        with self._lock:
            self.errors_encountered += count

    def set_current_repo(self, repo_name: str):
        with self._lock:
            self.current_repository = repo_name

    def get_runtime_seconds(self) -> int:
        return int((datetime.now() - self.start_time).total_seconds())

    def get_stats_dict(self) -> Dict[str, any]:
        with self._lock:
            return {
                'start_time': self.start_time.isoformat(),
                'runtime_seconds': self.get_runtime_seconds(),
                'repositories_found': self.repositories_found,
                'repositories_processed': self.repositories_processed,
                'files_analyzed': self.files_analyzed,
                'cgal_files_found': self.cgal_files_found,
                'api_requests_made': self.api_requests_made,
                'errors_encountered': self.errors_encountered,
                'current_repository': self.current_repository
            }

class CGALGitHubCrawler:
    """Main crawler class for searching GitHub repositories with CGAL usage."""

    def __init__(self, config: CrawlerConfig):
        """Initialize the crawler with configuration."""
        self.config = config
        self.github = Github(config.github_token)
        self.db = DatabaseManager(config.database_path)
        self.analyzer = CGALPatternAnalyzer()
        self.stats = CrawlerStats()

        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Initialize database
        self.db.initialize_database()

    def search_repositories(self, query: str = "CGAL language:C++", max_repos: Optional[int] = None) -> Generator[Dict, None, None]:
        """Search GitHub for repositories matching the query."""
        max_repos = max_repos or self.config.max_repositories

        try:
            logger.info(f"Searching GitHub with query: {query}")
            search_result = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )

            self.stats.increment_repos_found(min(search_result.totalCount, max_repos))
            logger.info(f"Found {search_result.totalCount} repositories, processing up to {max_repos}")

            processed = 0
            for repo in search_result:
                if processed >= max_repos:
                    break

                self._enforce_rate_limit()

                try:
                    repo_data = {
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'description': repo.description,
                        'html_url': repo.html_url,
                        'clone_url': repo.clone_url,
                        'language': repo.language,
                        'stargazers_count': repo.stargazers_count,
                        'forks_count': repo.forks_count,
                        'size': repo.size,
                        'created_at': repo.created_at.isoformat() if repo.created_at else '',
                        'updated_at': repo.updated_at.isoformat() if repo.updated_at else '',
                        'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else '',
                        'owner': {
                            'login': repo.owner.login,
                            'type': repo.owner.type
                        }
                    }

                    self.stats.increment_api_requests()
                    processed += 1
                    yield repo_data

                except Exception as e:
                    logger.error(f"Error processing repository {repo.full_name}: {e}")
                    self.stats.increment_errors()
                    continue

        except GithubException as e:
            logger.error(f"GitHub API error during repository search: {e}")
            self.stats.increment_errors()

    def analyze_repository(self, repo_data: Dict) -> Tuple[int, List[Dict]]:
        """Analyze a repository for CGAL usage and return repo_id and analyzed files."""
        self.stats.set_current_repo(repo_data['full_name'])
        logger.info(f"Analyzing repository: {repo_data['full_name']}")

        # Insert repository into database
        repo_id = self.db.insert_repository(repo_data)

        try:
            # Get repository object from GitHub
            repo = self.github.get_repo(repo_data['full_name'])
            self.stats.increment_api_requests()

            # Search for C++ files
            cpp_files = self._find_cpp_files(repo)

            analyzed_files = []
            cgal_files_count = 0
            all_patterns = set()

            # Analyze each file
            for file_data in cpp_files[:self.config.max_files_per_repo]:
                self._enforce_rate_limit()

                try:
                    # Get file content
                    file_content = self._get_file_content(repo, file_data)
                    if not file_content:
                        continue

                    # Analyze for CGAL patterns
                    analysis_result = self.analyzer.analyze_file_content(
                        file_content, file_data['path']
                    )

                    self.stats.increment_files_analyzed()

                    if analysis_result.has_cgal:
                        cgal_files_count += 1
                        self.stats.increment_cgal_files()
                        all_patterns.update(analysis_result.patterns_found)

                        # Store file data with analysis
                        file_data.update({
                            'content': file_content,
                            'cgal_headers': ','.join(analysis_result.headers_found),
                            'cgal_patterns': ','.join(analysis_result.patterns_found),
                            'pattern_count': analysis_result.pattern_count
                        })

                        # Insert file into database
                        file_id = self.db.insert_file(file_data, repo_id)
                        file_data['id'] = file_id

                        analyzed_files.append(file_data)

                except Exception as e:
                    logger.error(f"Error analyzing file {file_data.get('path', 'unknown')}: {e}")
                    self.stats.increment_errors()
                    continue

            # Update repository with CGAL statistics
            self.db.update_repository_cgal_stats(
                repo_id, 
                cgal_files_count, 
                ','.join(all_patterns)
            )

            self.stats.increment_repos_processed()
            logger.info(f"Repository {repo_data['full_name']}: Found {cgal_files_count} CGAL files")

            return repo_id, analyzed_files

        except Exception as e:
            logger.error(f"Error analyzing repository {repo_data['full_name']}: {e}")
            self.stats.increment_errors()
            return repo_id, []

    def _find_cpp_files(self, repo) -> List[Dict]:
        """Find C++ files in the repository."""
        cpp_files = []
        cpp_extensions = {'.cpp', '.hpp', '.h', '.cc', '.cxx', '.c++', '.hxx'}

        try:
            # Search for files with C++ extensions
            for ext in ['.cpp', '.h', '.hpp']:
                try:
                    search_query = f"extension:{ext[1:]}"
                    contents = repo.get_contents("", ref=repo.default_branch)

                    self.stats.increment_api_requests()

                    cpp_files.extend(self._search_files_recursive(repo, contents, cpp_extensions))

                    if len(cpp_files) >= self.config.max_files_per_repo:
                        break

                except Exception as e:
                    logger.debug(f"Error searching for {ext} files: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error finding C++ files in repository: {e}")

        return cpp_files[:self.config.max_files_per_repo]

    def _search_files_recursive(self, repo, contents, extensions: set, depth: int = 0) -> List[Dict]:
        """Recursively search for files with specific extensions."""
        files = []
        max_depth = 3  # Limit recursion depth

        if depth > max_depth:
            return files

        for content in contents:
            if content.type == "file":
                if any(content.name.lower().endswith(ext) for ext in extensions):
                    files.append({
                        'name': content.name,
                        'path': content.path,
                        'sha': content.sha,
                        'size': content.size,
                        'html_url': content.html_url,
                        'download_url': content.download_url
                    })
            elif content.type == "dir" and depth < max_depth:
                try:
                    self._enforce_rate_limit()
                    subcontents = repo.get_contents(content.path)
                    self.stats.increment_api_requests()
                    files.extend(self._search_files_recursive(repo, subcontents, extensions, depth + 1))
                except Exception as e:
                    logger.debug(f"Error accessing directory {content.path}: {e}")
                    continue

        return files

    def _get_file_content(self, repo, file_data: Dict) -> Optional[str]:
        """Get the content of a file from GitHub."""
        try:
            if file_data.get('size', 0) > 1048576:  # Skip files larger than 1MB
                logger.debug(f"Skipping large file: {file_data['path']}")
                return None

            file_obj = repo.get_contents(file_data['path'])
            self.stats.increment_api_requests()

            if file_obj.encoding == 'base64':
                content = base64.b64decode(file_obj.content).decode('utf-8', errors='ignore')
                return content
            else:
                return file_obj.content

        except Exception as e:
            logger.debug(f"Error getting content for {file_data['path']}: {e}")
            return None

    def _enforce_rate_limit(self):
        """Enforce GitHub API rate limiting."""
        current_time = time.time()

        # Reset request count if we're in a new minute window
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time

        # If we've hit the rate limit, wait
        if self.request_count >= self.config.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()

        # Enforce minimum delay between requests
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.config.search_delay_seconds:
            sleep_time = self.config.search_delay_seconds - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def run_crawl(self, queries: List[str] = None) -> Dict[str, any]:
        """Run the complete crawling process."""
        if queries is None:
            queries = [
                "CGAL language:C++",
                "#include <CGAL/ language:C++", 
                "using namespace CGAL language:C++",
                "CGAL:: language:C++"
            ]

        logger.info(f"Starting crawl with {len(queries)} search queries")

        all_repositories = []
        processed_repos = set()

        for query in queries:
            logger.info(f"Processing query: {query}")

            for repo_data in self.search_repositories(query):
                # Skip duplicates
                if repo_data['full_name'] in processed_repos:
                    continue

                processed_repos.add(repo_data['full_name'])

                try:
                    repo_id, analyzed_files = self.analyze_repository(repo_data)
                    repo_data['id'] = repo_id
                    repo_data['analyzed_files'] = analyzed_files
                    all_repositories.append(repo_data)

                except Exception as e:
                    logger.error(f"Failed to analyze repository {repo_data['full_name']}: {e}")
                    self.stats.increment_errors()
                    continue

                # Check if we've hit the repository limit
                if len(all_repositories) >= self.config.max_repositories:
                    logger.info(f"Reached maximum repository limit of {self.config.max_repositories}")
                    break

            if len(all_repositories) >= self.config.max_repositories:
                break

        final_stats = self.stats.get_stats_dict()
        final_stats['repositories'] = all_repositories

        logger.info(f"Crawl completed. Processed {len(all_repositories)} repositories, "
                   f"found {final_stats['cgal_files_found']} CGAL files")

        return final_stats

    def get_rate_limit_info(self) -> Dict[str, int]:
        """Get current GitHub API rate limit information."""
        try:
            rate_limit = self.github.get_rate_limit()
            self.stats.increment_api_requests()

            return {
                'core_remaining': rate_limit.core.remaining,
                'core_limit': rate_limit.core.limit,
                'core_reset_time': rate_limit.core.reset.isoformat(),
                'search_remaining': rate_limit.search.remaining,
                'search_limit': rate_limit.search.limit,
                'search_reset_time': rate_limit.search.reset.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {}
