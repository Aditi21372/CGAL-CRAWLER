# CGAL GitHub Crawler

> A research data-collection pipeline that **crawls GitHub for C++ repositories using the CGAL library**, analyzes exactly *how* it's used, stores findings in SQLite, and surfaces everything through a Flask dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![PyGithub](https://img.shields.io/badge/PyGithub-GitHub%20API-181717?style=flat&logo=github)

## Why

CGAL (Computational Geometry Algorithms Library) is widely used but poorly instrumented — there's no easy way to answer questions like *which CGAL headers do real projects rely on most?* or *how is the library actually adopted in the wild?* This tool collects that evidence at scale.

## What it does

- 🔍 **Searches GitHub** (via PyGithub) for C++ repositories containing CGAL usage
- 🧠 **Pattern-analyzes** every candidate file against a configurable ruleset — `cgal_patterns.json` — of known CGAL headers (`Delaunay_triangulation_2.h`, `convex_hull_3.h`, `Surface_mesh.h`, …) and namespace patterns
- ⏱️ **Respects the API** — token-bucket style rate limiting, configurable request spacing, bounded concurrency, and graceful handling of `RateLimitExceededException`
- 💾 **Persists** repository, file, and pattern stats in SQLite via a `DatabaseManager`
- 📊 **Dashboards** it all in a Flask web UI: crawl controls, live stats, and per-repository drill-down

## Architecture

```
   GitHub Code Search ──►  Crawler Engine (src/crawler.py)
   (PyGithub, search      • CrawlerConfig: rate limits, bounds
    queries, filters)     • ThreadPoolExecutor, retries
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
      Pattern Analyzer   DatabaseManager   CrawlerStats
      (src/analyzer.py)  (src/database.py) (live progress)
      header/namespace   SQLite storage    exported as
      regex matching                       csv / json
              │
              ▼
      Flask Dashboard (app.py)
      index · crawler · repositories
```

## Quick start

```bash
git clone https://github.com/Aditi21372/CGAL-CRAWLER.git
cd CGAL-CRAWLER
pip install -r requirements.txt

cp .env.example .env      # add your GITHUB_TOKEN
python app.py             # dashboard at http://localhost:5000
```

## Configuration

Everything is environment-driven (see `.env.example`):

| Variable                  | Default            | Purpose                              |
|---------------------------|--------------------|--------------------------------------|
| `GITHUB_TOKEN`            | — (required)       | Personal access token for the API    |
| `MAX_REQUESTS_PER_MINUTE` | `10`               | Rate-limit ceiling                   |
| `MAX_REPOSITORIES`        | `100`              | Crawl breadth                        |
| `MAX_FILES_PER_REPO`      | `50`               | Crawl depth per repository           |
| `MAX_CONCURRENT_REQUESTS` | `3`                | Parallel file fetches                |
| `DATABASE_PATH`           | `data/cgal_crawl…` | SQLite output                        |
| `EXPORT_FORMAT`           | `csv,json`         | Result export formats                |

---

Built by [@Aditi21372](https://github.com/Aditi21372) · [More projects](https://github.com/Aditi21372?tab=repositories)
