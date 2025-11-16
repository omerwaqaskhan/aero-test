"""
Test Hybrid Data Source Manager
Demonstrates API-first with scraping fallback
"""
import asyncio
from datetime import date, timedelta
from search_booking_module.scraping.hybrid_data_source import (
    HybridDataSourceManager,
    DataSourceStrategy,
    DataSourceType
)

print("\n" + "="*80)
print("🔄 HYBRID DATA SOURCE MANAGER")
print("="*80)

print("\n📊 CURRENT SITUATION:")
print("   ├─ API Access: ❌ Not yet (will get later)")
print("   ├─ Scraping: ✅ Available")
print("   ├─ Strategy: SCRAPING_ONLY (for now)")
print("   └─ Cost: $0-65/month")

# ============================================================================
# Scenario 1: Current Setup (No API Yet)
# ============================================================================

print("\n" + "="*80)
print("📦 SCENARIO 1: NO API ACCESS YET (Current Situation)")
print("="*80)

manager_current = HybridDataSourceManager(
    strategy=DataSourceStrategy.SCRAPING_ONLY,
    enable_api=False,
    enable_scraping=True
)

print("\n✅ Configuration:")
print(f"   Strategy: {manager_current.strategy.value}")
print(f"   API Enabled: {manager_current.enable_api}")
print(f"   Scraping Enabled: {manager_current.enable_scraping}")
print(f"   API Providers: {len(manager_current.api_providers)}")
print(f"   Scrapers: {len(manager_current.scrapers)}")

print("\n💰 Cost: $0-65/month (proxies only, if needed)")
print("✅ Works NOW with your current setup!")

# ============================================================================
# Scenario 2: Got API Access
# ============================================================================

print("\n" + "="*80)
print("📦 SCENARIO 2: GOT API ACCESS (Future)")
print("="*80)

# Simulate having API access
import os
os.environ["BOOKING_COM_API_KEY"] = "demo_key_123"  # Simulated

manager_api_first = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_FIRST,
    enable_api=True,
    enable_scraping=True
)

print("\n✅ Configuration:")
print(f"   Strategy: {manager_api_first.strategy.value}")
print(f"   API Enabled: {manager_api_first.enable_api}")
print(f"   Scraping Enabled: {manager_api_first.enable_scraping}")
print(f"   API Providers: {len(manager_api_first.api_providers)}")
print(f"   Scrapers: {len(manager_api_first.scrapers)}")

print("\n💡 How it works:")
print("   1️⃣  Tries API first (fast, high quality)")
print("   2️⃣  If API fails → automatically uses scraping")
print("   3️⃣  Never completely fails (always has backup)")

print("\n💰 Cost: ~$200/month (mostly API, occasional scraping backup)")
print("✅ Perfect for production!")

# ============================================================================
# Scenario 3: API is Stable, Stop Scraping
# ============================================================================

print("\n" + "="*80)
print("📦 SCENARIO 3: API STABLE - STOP SCRAPING (Later)")
print("="*80)

manager_api_only = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_ONLY,
    enable_api=True,
    enable_scraping=False
)

print("\n✅ Configuration:")
print(f"   Strategy: {manager_api_only.strategy.value}")
print(f"   API Enabled: {manager_api_only.enable_api}")
print(f"   Scraping Enabled: {manager_api_only.enable_scraping}")
print(f"   API Providers: {len(manager_api_only.api_providers)}")
print(f"   Scrapers: {len(manager_api_only.scrapers)}")

print("\n💡 How it works:")
print("   1️⃣  Only uses API")
print("   2️⃣  No scraping at all (save proxy costs)")
print("   3️⃣  Fastest and cleanest")

print("\n💰 Cost: ~$300-500/month (API only)")
print("💵 Savings: $65/month (no proxy costs)")
print("✅ Best when API is reliable!")

# ============================================================================
# Scenario 4: Multiple APIs, Parallel Search
# ============================================================================

print("\n" + "="*80)
print("📦 SCENARIO 4: MULTIPLE APIs - PARALLEL (Production Scale)")
print("="*80)

# Simulate multiple APIs
os.environ["EXPEDIA_API_KEY"] = "demo_expedia_key"

manager_parallel = HybridDataSourceManager(
    strategy=DataSourceStrategy.PARALLEL,
    enable_api=True,
    enable_scraping=False
)

print("\n✅ Configuration:")
print(f"   Strategy: {manager_parallel.strategy.value}")
print(f"   API Enabled: {manager_parallel.enable_api}")
print(f"   Scraping Enabled: {manager_parallel.enable_scraping}")
print(f"   API Providers: {len(manager_parallel.api_providers)}")

print("\n💡 How it works:")
print("   1️⃣  Queries all APIs simultaneously")
print("   2️⃣  Merges results (deduplicates)")
print("   3️⃣  Maximum hotel coverage")

print("\n💰 Cost: ~$500-800/month (multiple APIs)")
print("✅ Best for maximum coverage!")

# ============================================================================
# Demonstrate Dynamic Switching
# ============================================================================

print("\n" + "="*80)
print("🔄 DYNAMIC STRATEGY SWITCHING")
print("="*80)

print("\n💡 Example: Start without API, add it later\n")

# Start with scraping only
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.SCRAPING_ONLY,
    enable_api=False,
    enable_scraping=True
)
print(f"1️⃣  Initial: {manager.strategy.value} (no API yet)")

# ... later, when you get API access ...
manager.enable_source(DataSourceType.API)
manager.switch_strategy(DataSourceStrategy.API_FIRST)
print(f"2️⃣  Updated: {manager.strategy.value} (got API!)")

# ... even later, when API is stable ...
manager.disable_source(DataSourceType.SCRAPING)
manager.switch_strategy(DataSourceStrategy.API_ONLY)
print(f"3️⃣  Final: {manager.strategy.value} (API only, save $65/month)")

# ============================================================================
# Cost Comparison
# ============================================================================

print("\n" + "="*80)
print("💰 COST COMPARISON")
print("="*80)

costs = [
    ("Now (Scraping Only)", "$0-65", "No API yet"),
    ("API First", "$200-300", "API + scraping backup"),
    ("API Only", "$300-500", "Stop scraping, save $65"),
    ("Parallel (Multi-API)", "$500-800", "Maximum coverage"),
]

print(f"\n{'Phase':<30} {'Cost/Month':<15} {'Notes':<30}")
print("-" * 80)
for phase, cost, notes in costs:
    print(f"{phase:<30} {cost:<15} {notes:<30}")

# ============================================================================
# Migration Path
# ============================================================================

print("\n" + "="*80)
print("🛣️  RECOMMENDED MIGRATION PATH")
print("="*80)

path = [
    ("Phase 1: NOW", "scraping_only", "$0-65", "No API yet"),
    ("Phase 2: Got API", "api_first", "$200-300", "Use API, keep scraping backup"),
    ("Phase 3: API Stable", "api_only", "$300-500", "Stop scraping, save costs"),
    ("Phase 4: Scale", "parallel", "$500-800", "Multiple APIs, max coverage"),
]

for i, (phase, strategy, cost, description) in enumerate(path, 1):
    if i == 1:
        marker = "← You are here!"
    else:
        marker = ""
    
    print(f"\n{i}. {phase:<20} {marker}")
    print(f"   Strategy: {strategy}")
    print(f"   Cost: {cost}/month")
    print(f"   Description: {description}")

# ============================================================================
# Key Takeaways
# ============================================================================

print("\n" + "="*80)
print("🎯 KEY TAKEAWAYS")
print("="*80)

print("""
✅ RIGHT NOW:
   • Use SCRAPING_ONLY strategy (no API needed)
   • Cost: $0-65/month
   • Works with your current setup (81 hotels)

✅ WHEN YOU GET API:
   • Switch to API_FIRST strategy
   • Keep scraping as backup
   • Cost: ~$200/month
   • Seamless migration!

✅ WHEN API IS STABLE:
   • Switch to API_ONLY strategy
   • Stop scraping completely
   • Save $65/month on proxies
   • Fastest and cleanest

✅ FOR MAXIMUM COVERAGE:
   • Use PARALLEL strategy
   • Multiple APIs simultaneously
   • Cost: $500-800/month
   • Best quality data

🔄 The system adapts automatically - no code changes needed!
Just update environment variables and restart.

📖 Read: backend/HYBRID_DATA_SOURCE_GUIDE.md for full documentation
""")

print("="*80 + "\n")

# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """Example of using the hybrid manager."""
    
    print("="*80)
    print("📝 EXAMPLE CODE")
    print("="*80)
    
    print("""
from search_booking_module.scraping.hybrid_data_source import (
    HybridDataSourceManager,
    DataSourceStrategy
)

# Current setup (no API)
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.SCRAPING_ONLY,
    enable_api=False,
    enable_scraping=True
)

# Search hotels
hotels, source = await manager.search_hotels(
    destination="London",
    check_in=date.today() + timedelta(days=7),
    check_out=date.today() + timedelta(days=10),
    guests=2,
    rooms=1
)

print(f"Found {len(hotels)} via {source.value}")

# Later, when you get API...
manager.enable_source(DataSourceType.API)
manager.switch_strategy(DataSourceStrategy.API_FIRST)
# Now uses API first, scraping as backup!

# Get stats
stats = manager.get_stats()
print(stats)
    """)
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(example_usage())

