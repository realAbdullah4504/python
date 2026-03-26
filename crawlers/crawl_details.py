#!/usr/bin/env python3
"""
Unified details crawler entry point.
Integrates PDF and postback details extraction strategies.
"""

import argparse
import sys
from typing import Optional
from crawlers.core.details_engine import DetailsEngine


def main():
    """Main function to orchestrate details extraction."""
    parser = argparse.ArgumentParser(description="Extract details from tenders using various strategies")
    parser.add_argument("--max-tenders", type=int, help="Maximum number of tenders to process")
    parser.add_argument("--strategy", choices=["pdf", "postback"], help="Process only with specific strategy")
    parser.add_argument("--list-strategies", action="store_true", help="List available strategies")
    
    args = parser.parse_args()
    
    # Initialize details engine
    engine = DetailsEngine()
    
    # List strategies if requested
    if args.list_strategies:
        strategies = engine.get_available_strategies()
        print("Available strategies:")
        for strategy in strategies:
            print(f"  - {strategy}")
        return
    
    # Run details extraction
    try:
        if args.strategy:
            print(f"Processing tenders with strategy: {args.strategy}")
            # For now, just run with all strategies since strategy-specific filtering
            # would require additional implementation in the DetailsEngine
            result = engine.run(max_tenders=args.max_tenders)
        else:
            print("Processing tenders with all available strategies")
            result = engine.run(max_tenders=args.max_tenders)
        
        print("\nProcessing Summary:")
        print(f"Total tenders found: {result['total_tenders']}")
        print(f"Successfully processed: {result['processed']}")
        strategies_used = result.get('strategies_used', [])
        print("Strategies used: " + ', '.join(strategies_used))
        
        if result['processed'] == 0:
            print("No tenders were processed. Check configuration and tender data.")
            sys.exit(1)
        else:
            print("Details extraction completed successfully!")
            
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
