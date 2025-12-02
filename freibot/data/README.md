# Data Directory

This directory contains all data files for Freibot.

## Structure

- `vectorstore/` - ChromaDB vector database
- `files/` - Raw input files (PDFs, HTMLs, etc.)
- `processed_files/` - Intermediate processing artifacts

## Usage

Place PDF files in `files/` and run the indexing pipeline to populate `vectorstore/`.
