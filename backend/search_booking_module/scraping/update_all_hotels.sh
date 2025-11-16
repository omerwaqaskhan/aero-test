#!/bin/bash
# Script to update ALL existing hotels with detailed information

echo "=========================================="
echo "Updating ALL Hotels with Details"
echo "=========================================="
echo ""
echo "This will re-scrape all 100 hotels to get:"
echo "  - Rooms"
echo "  - Reviews"
echo "  - Amenities"
echo "  - Property Overview"
echo ""
echo "Estimated time: ~15-20 minutes"
echo ""
read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Starting update process..."
echo "This will run in the background. Check logs with:"
echo "  docker compose logs -f backend | grep -i 'rescrape\|updated\|rooms\|reviews'"
echo ""

# Run in background and save output to log file
docker compose exec -d backend python -m search_booking_module.scraping.rescrape_hotels > /tmp/hotel_update.log 2>&1

echo "Update process started in background!"
echo "Monitor progress: tail -f /tmp/hotel_update.log"
echo "Or check logs: docker compose logs -f backend"

