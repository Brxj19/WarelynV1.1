# Warelyn Warehouse and Location Knowledge

## What is a warehouse in Warelyn?

A warehouse is a physical storage facility. Each warehouse has a name and can contain multiple locations. Stock is tracked per product per warehouse per location.

## What is a warehouse location?

A location is a specific storage position inside a warehouse: a zone, rack, aisle, bin, shelf, or pallet position. Locations allow you to know not just how much stock you have but exactly where it is. Example: Warehouse A → Zone B → Rack 3 → Bin 7.

## How to create a warehouse

Go to Warehouses, click Create Warehouse. Enter the name and address. Click Save. After creating the warehouse, open it and add locations.

## How to add locations to a warehouse

Open a warehouse. Click Add Location. Enter the location name (e.g. A-01, Rack-1-Shelf-2). Repeat for all locations. Locations are used when receiving stock, picking, and doing cycle counts.

## How is stock assigned to a location?

Stock is assigned to a location when it is received through a purchase receipt and put away. During putaway, INVENTORY_MANAGER specifies which location the goods go to. The stock ledger records the location.

## What is the difference between on-hand and available stock at location level?

On-hand is the total physical quantity at a location. Reserved is the quantity reserved for confirmed sales orders. Available = on-hand minus reserved. Reservations are at the product-warehouse level, not the location level, so a single reservation may draw from any location in the warehouse.

## How to transfer stock between locations?

Go to Inventory, Stock Transfers. Select the source warehouse and location, the destination warehouse and location, the product, and the quantity. Click Commit Transfer. The ledger records a TRANSFER_OUT from the source and TRANSFER_IN at the destination.

## What is warehouse utilisation?

Warehouse utilisation is the percentage of locations that contain stock, compared to the total number of locations in the warehouse. A utilisation of 85% means 85% of the locations have at least some stock. View this on the INVENTORY_MANAGER dashboard.

## How to do a physical stock check for one location?

Use a cycle count session. Create a session for the warehouse. Add only the products in the specific location. Count. Submit. Reconcile. The system adjusts stock to match the physical count.

## What happens to a location when all stock is moved out?

The location still exists but shows zero stock. It can receive new stock in the future. Locations are not deleted when empty — they are permanent structural elements of the warehouse.
