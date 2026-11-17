.PHONY: all verify

all: verify

verify:
	python3 verify_binaries.py
