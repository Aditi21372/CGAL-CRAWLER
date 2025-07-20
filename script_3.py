# Create CGAL patterns configuration
cgal_patterns = {
    "headers": [
        "CGAL/Exact_predicates_inexact_constructions_kernel.h",
        "CGAL/Point_2.h",
        "CGAL/Point_3.h", 
        "CGAL/Vector_2.h",
        "CGAL/Vector_3.h",
        "CGAL/Polygon_2.h",
        "CGAL/Polyhedron_3.h",
        "CGAL/Surface_mesh.h",
        "CGAL/Delaunay_triangulation_2.h",
        "CGAL/Delaunay_triangulation_3.h",
        "CGAL/Triangulation_2.h",
        "CGAL/Triangulation_3.h",
        "CGAL/Voronoi_diagram_2.h",
        "CGAL/Boolean_set_operations_2.h",
        "CGAL/Polygon_set_2.h",
        "CGAL/convex_hull_2.h",
        "CGAL/convex_hull_3.h",
        "CGAL/Alpha_shape_2.h",
        "CGAL/Alpha_shape_3.h",
        "CGAL/Arrangement_2.h",
        "CGAL/Simple_cartesian.h",
        "CGAL/Cartesian.h",
        "CGAL/Homogeneous.h",
        "CGAL/basic.h",
        "CGAL/number_utils.h",
        "CGAL/Polygon_mesh_processing/triangulate_faces.h",
        "CGAL/Polygon_mesh_processing/repair.h"
    ],
    "namespaces": [
        "using namespace CGAL",
        "CGAL::",
        "namespace CGAL"
    ],
    "search_patterns": [
        r"#include\s*[<\"]\s*CGAL/",
        r"CGAL::\w+",
        r"using\s+namespace\s+CGAL",
        r"typedef\s+CGAL::",
        r"CGAL::\w+\s*<",
        r"CGAL_\w+"
    ],
    "common_types": [
        "Point_2",
        "Point_3", 
        "Vector_2",
        "Vector_3",
        "Polygon_2",
        "Triangle_2",
        "Triangle_3",
        "Segment_2", 
        "Segment_3",
        "Line_2",
        "Line_3",
        "Plane_3",
        "Surface_mesh",
        "Polyhedron_3"
    ],
    "algorithms": [
        "convex_hull",
        "Delaunay_triangulation",
        "Voronoi_diagram",
        "Boolean_set_operations",
        "Alpha_shape",
        "minkowski_sum",
        "intersection",
        "do_intersect"
    ]
}

with open("cgal-github-crawler/config/cgal_patterns.json", "w") as f:
    json.dump(cgal_patterns, f, indent=2)

# Create logging configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/crawler.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "loggers": {
        "cgal_crawler": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}

with open("cgal-github-crawler/config/logging_config.json", "w") as f:
    json.dump(logging_config, f, indent=2)

print("Configuration files created:")
print("- config/cgal_patterns.json")
print("- config/logging_config.json")
print(f"CGAL patterns include {len(cgal_patterns['headers'])} headers and {len(cgal_patterns['search_patterns'])} search patterns")