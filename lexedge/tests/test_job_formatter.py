#!/usr/bin/env python
"""
Test script for the job formatter utility.
Demonstrates formatting job search results with HTML tags and clickable job titles.
"""

import sys
import os

# Add workspace root to path for testing (go up 3 levels from test file)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lexedge.utils.job_formatter import (
    format_jobs_with_html,
    format_jobs_summary,
    format_jobs_compact,
    format_jobs_titles_only
)

# Sample job data from the user's schema
SAMPLE_JOBS_DATA = {
    "total": 63,
    "results": [
        {
            "id": "test_JOB-d2a86557",
            "score": 1,
            "doc_type": "job",
            "tenant_id": "test",
            "job_id": "test_JOB-d2a86557",
            "title": "Renewable Energy Engineer",
            "description": "We are looking for a skilled Renewable Energy Engineer to join our Transportation team. The ideal candidate will have strong experience in Logistics, Node.js, CAD Software.",
            "requirements": "- 8 years of experience\n- Proficiency in React, Node.js, Logistics, TypeScript\n- Bachelor's in Computer Science",
            "responsibilities": "- Design and implement robust solutions\n- Collaborate with cross-functional teams\n- Mentor junior team members\n- Participate in project reviews",
            "location": "Austin, TX",
            "job_type": "Temporary",
            "department": "Security",
            "min_salary": 104000,
            "max_salary": 146000,
            "salary_currency": "USD",
            "min_experience": 4.740712,
            "max_experience": 9.505829,
            "posting_date": "2025-05-07T15:31:26Z"
        },
        {
            "id": "test_JOB-09390cd1",
            "title": "Environmental Scientist",
            "description": "We are looking for a skilled Environmental Scientist to join our Telecommunications team. The ideal candidate will have strong experience in Supply Chain Management, Logistics, Python.",
            "requirements": "- 8 years of experience\n- Proficiency in Logistics, Supply Chain Management, Sustainable Design, GIS\n- Master's in Computer Science",
            "responsibilities": "- Design and implement robust solutions\n- Collaborate with cross-functional teams\n- Mentor junior team members\n- Participate in project reviews",
            "location": "Los Angeles, CA",
            "job_type": "Temporary",
            "department": "Design",
            "min_salary": 118000,
            "max_salary": 165000,
            "salary_currency": "USD",
            "min_experience": 0.050886616,
            "max_experience": 2.963013,
            "posting_date": "2025-05-11T15:31:26Z"
        },
        {
            "id": "test_JOB-06c7cc5f",
            "title": "Telemedicine Specialist",
            "description": "We are looking for a skilled Telemedicine Specialist to join our Healthcare team. The ideal candidate will have strong experience in Electronic Health Records, HIPAA Compliance, React.",
            "requirements": "- 2 years of experience\n- Proficiency in Electronic Health Records, React, HIPAA Compliance, TypeScript\n- Master's in Computer Science",
            "responsibilities": "- Design and implement robust solutions\n- Collaborate with cross-functional teams\n- Mentor junior team members\n- Participate in project reviews",
            "location": "Denver, CO",
            "job_type": "Internship",
            "department": "Sales",
            "min_salary": 81000,
            "max_salary": 115000,
            "salary_currency": "USD",
            "min_experience": 4.2682195,
            "max_experience": 8.705496,
            "posting_date": "2025-05-22T15:31:26Z"
        },
        {
            "id": "test_JOB-646f2056",
            "title": "Machine Learning Engineer",
            "description": "We are looking for a skilled Machine Learning Engineer to join our Technology team. The ideal candidate will have strong experience in Kotlin, C++, Swift.",
            "requirements": "- 3 years of experience\n- Proficiency in SQL, Kotlin, Swift, Python\n- Bachelor's in Mechanical Engineering",
            "responsibilities": "- Design and implement robust solutions\n- Collaborate with cross-functional teams\n- Mentor junior team members\n- Participate in project reviews",
            "location": "Singapore",
            "job_type": "Temporary",
            "department": "Product",
            "min_salary": 145000,
            "max_salary": 192000,
            "salary_currency": "USD",
            "min_experience": 2.6559937,
            "max_experience": 6.5091906,
            "posting_date": "2025-05-24T15:31:26Z"
        }
    ],
    "facets": None,
    "query_time_ms": 45
}

def test_format_functions():
    """Test all formatting functions with sample data."""
    
    print("🧪 Testing Job Formatter Utility")
    print("=" * 50)
    
    # Test 1: Full HTML formatting
    print("\n📋 TEST 1: Full HTML Formatting")
    print("-" * 30)
    full_html = format_jobs_with_html(SAMPLE_JOBS_DATA, max_jobs=2)
    print(full_html)
    
    # Test 2: Jobs summary
    print("\n📊 TEST 2: Jobs Summary")
    print("-" * 30)
    summary = format_jobs_summary(SAMPLE_JOBS_DATA)
    print(summary)
    
    # Test 3: Compact format
    print("\n📝 TEST 3: Compact Format")
    print("-" * 30)
    compact = format_jobs_compact(SAMPLE_JOBS_DATA, max_jobs=3)
    print(compact)
    
    # Test 4: Titles only
    print("\n📜 TEST 4: Titles Only")
    print("-" * 30)
    titles = format_jobs_titles_only(SAMPLE_JOBS_DATA, max_jobs=4)
    print(titles)
    
    # Test 5: Empty data handling
    print("\n🔍 TEST 5: Empty Data Handling")
    print("-" * 30)
    empty_result = format_jobs_with_html({"total": 0, "results": []})
    print(empty_result)
    
    print("\n✅ All tests completed!")
    
    # Usage examples
    print("\n" + "=" * 50)
    print("💡 USAGE EXAMPLES")
    print("=" * 50)
    
    usage_examples = '''
# In your job tools, use the formatter like this:

from lexedge.utils.job_formatter import (
    format_jobs_with_html,
    format_jobs_compact,
    format_jobs_titles_only
)

def list_all_jobs():
    """Example job tool using the formatter."""
    # Your existing job search logic...
    jobs_data = search_jobs()  # Returns your schema format
    
    # Format for display
    formatted_jobs = format_jobs_with_html(jobs_data, max_jobs=10)
    
    return {
        "formatted_response": formatted_jobs,
        "total_jobs": jobs_data.get("total", 0)
    }

# Different formatting options:
# - format_jobs_with_html(jobs_data)          # Full details
# - format_jobs_compact(jobs_data, max_jobs=5) # Brief view
# - format_jobs_titles_only(jobs_data)         # Just titles
# - format_jobs_summary(jobs_data)             # Summary stats
    '''
    
    print(usage_examples)

if __name__ == "__main__":
    test_format_functions() 