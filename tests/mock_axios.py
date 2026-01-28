#!/usr/bin/env python3
"""
Mock Axios CLI for Testing

This script simulates the axios CLI tool for testing the AxiosProvider
without requiring a real Axios account.

Usage:
    Set up mock by adding this directory to PATH or symlink as 'axios':
    ln -s /path/to/tests/mock_axios.py /usr/local/bin/axios

    Then the AxiosProvider will call this instead of the real axios CLI.
"""

import sys
import json
import os


def main():
    """Main entry point for mock axios CLI."""

    # Parse command line arguments
    if '--version' in sys.argv:
        print("axios mock 0.4.0 (test version)")
        return 0

    if '--output-format' not in sys.argv or 'grades' not in sys.argv or 'list' not in sys.argv:
        print("Error: Invalid command", file=sys.stderr)
        return 1

    # Check environment variables for authentication
    customer_id = os.environ.get('AXIOS_CUSTOMER_ID', '')
    username = os.environ.get('AXIOS_USERNAME', '')
    password = os.environ.get('AXIOS_PASSWORD', '')
    student_id = os.environ.get('AXIOS_STUDENT_ID', '')

    # Validate credentials (mock validation)
    if not all([customer_id, username, password, student_id]):
        print("Error: Missing authentication credentials", file=sys.stderr)
        return 1

    # Mock authentication check
    if username == "invalid" or password == "wrong":
        print("Error: Invalid authentication credentials", file=sys.stderr)
        return 1

    # Return mock grade data
    mock_grades = [
        {
            "subject": "MATEMATICA",
            "value": 8.5,
            "kind": "Scritto",
            "date": "2024-10-15",
            "comment": "Test di algebra",
            "weight": 1.0
        },
        {
            "subject": "ITALIANO",
            "value": 7.0,
            "kind": "Orale",
            "date": "2024-10-20",
            "comment": "Interrogazione Dante",
            "weight": 1.0
        },
        {
            "subject": "INGLESE",
            "value": 9.0,
            "kind": "Scritto",
            "date": "2024-11-05",
            "comment": "Grammar test",
            "weight": 1.5
        },
        {
            "subject": "SCIENZE",
            "value": 6.5,
            "kind": "Pratico",
            "date": "2024-11-12",
            "comment": "Esperimento laboratorio",
            "weight": 1.0
        },
        {
            "subject": "STORIA",
            "value": 8.0,
            "kind": "Orale",
            "date": "2024-12-03",
            "comment": "Prima guerra mondiale",
            "weight": 1.0
        },
        {
            "subject": "MATEMATICA",
            "value": 7.5,
            "kind": "Scritto",
            "date": "2024-03-10",
            "comment": "Test geometria",
            "weight": 1.0
        },
        {
            "subject": "ITALIANO",
            "value": 8.5,
            "kind": "Scritto",
            "date": "2024-04-15",
            "comment": "Tema argomentativo",
            "weight": 1.5
        }
    ]

    # Output JSON
    print(json.dumps(mock_grades, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
