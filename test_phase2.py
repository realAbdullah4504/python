#!/usr/bin/env python3
"""
Test script to verify Phase 2 pagination handlers work correctly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pagination_imports():
    """Test that all pagination imports work correctly"""
    try:
        from crawlers.pagination import IPaginationHandler, DataTablesPaginationHandler, PostbackPaginationHandler
        print("✅ Successfully imported all pagination handlers")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_datatables_handler():
    """Test basic functionality of DataTablesPaginationHandler"""
    try:
        from crawlers.pagination import DataTablesPaginationHandler
        
        handler = DataTablesPaginationHandler()
        
        # Test pagination type
        assert handler.get_pagination_type() == "datatables", "Should return correct pagination type"
        
        # Test has_more_data with empty response
        assert not handler.has_more_data({}, 10), "Empty response should return False"
        
        # Test has_more_data with data
        response_with_data = {"data": [{"id": 1}, {"id": 2}]}
        assert handler.has_more_data(response_with_data, 2), "Full page should return True"
        assert not handler.has_more_data(response_with_data, 3), "Partial page should return False"
        
        # Test data extraction
        data = handler.extract_data_from_response(response_with_data)
        assert len(data) == 2, "Should extract correct number of items"
        
        print("✅ DataTablesPaginationHandler basic functionality works")
        return True
    except Exception as e:
        print(f"❌ DataTablesPaginationHandler test failed: {e}")
        return False

def test_postback_handler():
    """Test basic functionality of PostbackPaginationHandler"""
    try:
        from crawlers.pagination import PostbackPaginationHandler
        
        # We can't fully test this without a real page object, but we can test the interface
        handler_type = PostbackPaginationHandler.get_pagination_type.__func__(None)
        assert handler_type == "postback", "Should return correct pagination type"
        
        print("✅ PostbackPaginationHandler interface works")
        return True
    except Exception as e:
        print(f"❌ PostbackPaginationHandler test failed: {e}")
        return False

def test_crawler_integration():
    """Test that the updated crawler functions can be imported"""
    try:
        from crawlers.crawl_unified import _crawl_pattern_based_portal, _crawl_table_based_portal
        print("✅ Updated crawler functions can be imported")
        return True
    except ImportError as e:
        print(f"❌ Crawler integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Phase 2 Pagination Handlers...")
    print("=" * 50)
    
    tests = [
        test_pagination_imports,
        test_datatables_handler,
        test_postback_handler,
        test_crawler_integration
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Phase 2 refactoring is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
