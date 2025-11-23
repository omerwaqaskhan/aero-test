#!/bin/bash
# Script to update existing hotels with detailed information

echo "=========================================="
echo "Updating Existing Hotels with Details"
echo "=========================================="
echo ""
echo "This will re-scrape all existing hotels to get:"
echo "  - Rooms"
echo "  - Reviews"
echo "  - Amenities"
echo "  - Property Overview"
echo ""
echo "Options:"
echo "  1. Update all hotels (may take a while)"
echo "  2. Update first 10 hotels (test run)"
echo "  3. Update specific hotels by ID"
echo ""
read -p "Enter choice (1/2/3): " choice

case $choice in
    1)
        echo "Updating all hotels..."
        docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels
        ;;
    2)
        echo "Updating first 10 hotels (test run)..."
        docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels 10
        ;;
    3)
        read -p "Enter hotel IDs (comma-separated): " hotel_ids
        echo "Updating hotels: $hotel_ids"
        docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels "$hotel_ids"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done! Check the logs above for results."

