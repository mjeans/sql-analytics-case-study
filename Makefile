.PHONY: build query test all clean

build:
	python scripts/build_demo_database.py

query: build
	python scripts/run_queries.py
	python scripts/render_results.py

test:
	python -m unittest discover -s tests -v

all: query test

clean:
	rm -f data/analytics_demo.sqlite
