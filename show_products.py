import sys
sys.path.insert(0, '.')
from scripts.printify_product_publisher import PrintifyPublisher

pub = PrintifyPublisher()

print("=== ALL PRODUCTS ===")
products = pub.list_products()
for p in products:
    profit = p.price_usd - p.cost_usd
    print(f"{p.product_type.upper():8} | {p.title[:40]:40} | ${p.price_usd:6.2f} | Profit: ${profit:5.2f}")

print()
print("=== INVENTORY SUMMARY ===")
stats = pub.get_inventory_stats()
print(f"Total Products: {stats['total_products']}")
print(f"Total Potential Profit: ${stats['total_potential_profit']:.2f}")
print()
print("By Type:")
for ptype, count in sorted(stats['products_by_type'].items()):
    print(f"  {ptype.upper()}: {count}")
