"""
CGAL Pattern Analysis Module
Analyzes C++ code to detect CGAL library usage patterns.
"""

import re
import json
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger('cgal_crawler.analyzer')

@dataclass
class CGALAnalysisResult:
    """Results of CGAL pattern analysis for a file."""
    file_path: str
    has_cgal: bool
    headers_found: List[str]
    patterns_found: List[str]
    pattern_count: int
    confidence_score: float
    analysis_details: Dict[str, any]

class CGALPatternAnalyzer:
    """Analyzes C++ code files for CGAL usage patterns."""

    def __init__(self, config_path: str = "config/cgal_patterns.json"):
        """Initialize analyzer with CGAL patterns configuration."""
        self.patterns = self._load_patterns(config_path)
        self._compile_regex_patterns()

    def _load_patterns(self, config_path: str) -> Dict:
        """Load CGAL patterns from configuration file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Pattern config not found at {config_path}, using defaults")
            return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict:
        """Return default CGAL patterns if config file is not found."""
        return {
            "headers": [
                "CGAL/Exact_predicates_inexact_constructions_kernel.h",
                "CGAL/Point_2.h",
                "CGAL/Point_3.h",
                "CGAL/Polygon_2.h",
                "CGAL/Delaunay_triangulation_2.h"
            ],
            "namespaces": [
                "using namespace CGAL",
                "CGAL::"
            ],
            "search_patterns": [
                r'#include\s*[<"]\s*CGAL/'
                r"CGAL::\w+",
                r"using\s+namespace\s+CGAL"
            ]
        }

    def _compile_regex_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_patterns = []
        for pattern in self.patterns.get("search_patterns", []):
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")

    def analyze_file_content(self, content: str, file_path: str = "") -> CGALAnalysisResult:
        """Analyze file content for CGAL patterns."""
        if not content or not isinstance(content, str):
            return CGALAnalysisResult(
                file_path=file_path,
                has_cgal=False,
                headers_found=[],
                patterns_found=[],
                pattern_count=0,
                confidence_score=0.0,
                analysis_details={"error": "Empty or invalid content"}
            )

        # Analyze different aspects
        headers_found = self._find_cgal_headers(content)
        namespace_usage = self._find_namespace_usage(content)
        type_usage = self._find_type_usage(content)
        pattern_matches = self._find_pattern_matches(content)

        # Calculate metrics
        total_patterns = len(headers_found) + len(namespace_usage) + len(type_usage) + len(pattern_matches)
        has_cgal = total_patterns > 0
        confidence_score = self._calculate_confidence_score(headers_found, namespace_usage, type_usage, pattern_matches)

        all_patterns_found = []
        all_patterns_found.extend(headers_found)
        all_patterns_found.extend(namespace_usage)
        all_patterns_found.extend(type_usage)
        all_patterns_found.extend(pattern_matches)

        analysis_details = {
            "headers": headers_found,
            "namespace_usage": namespace_usage,
            "type_usage": type_usage,
            "pattern_matches": pattern_matches,
            "file_size": len(content),
            "line_count": content.count('\n') + 1
        }

        return CGALAnalysisResult(
            file_path=file_path,
            has_cgal=has_cgal,
            headers_found=headers_found,
            patterns_found=all_patterns_found,
            pattern_count=total_patterns,
            confidence_score=confidence_score,
            analysis_details=analysis_details
        )

    def _find_cgal_headers(self, content: str) -> List[str]:
        """Find CGAL header includes in the content."""
        headers_found = []

        # Look for #include <CGAL/...> patterns
        include_pattern = r'#include\s*[<"](CGAL/[^>"]+)[>"]'
        matches = re.findall(include_pattern, content, re.IGNORECASE)
        headers_found.extend(matches)

        # Check against known CGAL headers
        for header in self.patterns.get("headers", []):
            if header in content:
                if header not in headers_found:
                    headers_found.append(header)

        return list(set(headers_found))  # Remove duplicates

    def _find_namespace_usage(self, content: str) -> List[str]:
        """Find CGAL namespace usage patterns."""
        namespace_patterns = []

        # Look for "using namespace CGAL"
        if re.search(r'using\s+namespace\s+CGAL', content, re.IGNORECASE):
            namespace_patterns.append("using namespace CGAL")

        # Look for qualified CGAL usage (CGAL::)
        cgal_qualified = re.findall(r'CGAL::(\w+)', content)
        for match in cgal_qualified[:10]:  # Limit to first 10 matches
            namespace_patterns.append(f"CGAL::{match}")

        return list(set(namespace_patterns))

    def _find_type_usage(self, content: str) -> List[str]:
        """Find CGAL type usage patterns."""
        types_found = []

        for cgal_type in self.patterns.get("common_types", []):
            # Look for type usage in various contexts
            patterns = [
                rf'CGAL::{re.escape(cgal_type)}',
                rf'{re.escape(cgal_type)}\s*<',  # Template usage
                rf'typedef.*{re.escape(cgal_type)}',  # Typedef
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    types_found.append(cgal_type)
                    break  # Don't add duplicates

        return list(set(types_found))

    def _find_pattern_matches(self, content: str) -> List[str]:
        """Find matches using compiled regex patterns."""
        pattern_matches = []

        for pattern in self.compiled_patterns:
            matches = pattern.findall(content)
            pattern_matches.extend(matches[:5])  # Limit matches per pattern

        return list(set(pattern_matches))

    def _calculate_confidence_score(self, headers: List[str], namespaces: List[str], 
                                  types: List[str], patterns: List[str]) -> float:
        """Calculate confidence score for CGAL usage (0.0 to 1.0)."""
        score = 0.0

        # Header includes are strong indicators
        score += min(len(headers) * 0.3, 0.6)

        # Namespace usage is a good indicator  
        score += min(len(namespaces) * 0.2, 0.3)

        # Type usage indicates deeper integration
        score += min(len(types) * 0.1, 0.2)

        # Pattern matches provide additional confidence
        score += min(len(patterns) * 0.05, 0.1)

        return min(score, 1.0)

    def is_cpp_file(self, filename: str) -> bool:
        """Check if file is a C++ source file."""
        cpp_extensions = {'.cpp', '.hpp', '.h', '.cc', '.cxx', '.c++', '.hxx', '.h++'}
        return any(filename.lower().endswith(ext) for ext in cpp_extensions)

    def get_file_type_classification(self, file_path: str, analysis_result: CGALAnalysisResult) -> str:
        """Classify file type based on CGAL usage patterns."""
        if not analysis_result.has_cgal:
            return "non-cgal"

        if analysis_result.confidence_score >= 0.7:
            return "heavy-cgal-usage"
        elif analysis_result.confidence_score >= 0.4:
            return "moderate-cgal-usage"
        else:
            return "light-cgal-usage"

    def get_cgal_domain_hints(self, analysis_result: CGALAnalysisResult) -> List[str]:
        """Infer computational geometry domains based on patterns found."""
        domains = []

        # Domain keyword mapping
        domain_keywords = {
            "triangulation": ["Delaunay_triangulation", "Triangulation", "triangulate"],
            "convex_hull": ["convex_hull", "convex"],
            "boolean_operations": ["Boolean_set", "intersection", "union"],
            "mesh_processing": ["Surface_mesh", "Polyhedron", "mesh"],
            "arrangements": ["Arrangement", "curves"],
            "voronoi": ["Voronoi", "voronoi"],
            "alpha_shapes": ["Alpha_shape", "alpha"],
            "2d_geometry": ["Point_2", "Vector_2", "Polygon_2"],
            "3d_geometry": ["Point_3", "Vector_3", "Plane_3"]
        }

        all_patterns = analysis_result.patterns_found + analysis_result.headers_found
        all_text = " ".join(all_patterns).lower()

        for domain, keywords in domain_keywords.items():
            if any(keyword.lower() in all_text for keyword in keywords):
                domains.append(domain)

        return domains
