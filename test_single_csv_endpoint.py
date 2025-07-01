#!/usr/bin/env python3
"""Test script for the single CSV import endpoint."""

import requests

def test_csv_import(source: str = "taaft", replace_existing: bool = False):
    """Test the unified CSV import endpoint."""
    url = "http://localhost:8000/admin/import-csv"
    
    # Open the CSV file
    with open("app/sample/theresanaiforthat.csv", "rb") as f:
        files = {"file": ("theresanaiforthat.csv", f, "text/csv")}
        data = {
            "source": source,
            "replace_existing": str(replace_existing).lower()
        }
        
        response = requests.post(url, files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_supported_sources():
    """Test different source values."""
    sources = ["taaft", "theresanaiforthat", "theresanaiforthat.com", "invalid"]
    
    for source in sources:
        print(f"\n--- Testing source: {source} ---")
        try:
            test_csv_import(source=source)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Testing Single CSV Import Endpoint ===")
    
    # Test with default TAAFT source
    print("\n1. Testing with TAAFT source:")
    test_csv_import()
    
    # Test all supported sources
    print("\n2. Testing all sources:")
    test_supported_sources()