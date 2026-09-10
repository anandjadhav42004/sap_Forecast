# Database Schema - SAP Prognos

The application uses an SQLite database (`inventory.db`) to simulate the SAP ECC/S4HANA backend.

## Table: `inventory`

| Column | Type | Description |
|--------|------|-------------|
| `store_id` | Integer | Primary Key (Composite) |
| `item_id` | Integer | Primary Key (Composite) |
| `current_stock` | Integer | Real-time on-hand inventory |
| `target_stock` | Integer | Maximum optimal stock level |
| `reorder_point` | Integer | Threshold that triggers a reorder alert |
| `safety_stock` | Integer | Buffer stock for demand variability |
| `lead_time_days` | Integer | Supplier delivery time |
| `incoming_stock` | Integer | Units currently in transit |
| `last_updated` | Timestamp | Last modified date |

## Reorder Logic
The reorder alert is triggered when:
`current_stock + incoming_stock < reorder_point`

The recommended reorder amount is:
`target_stock - (current_stock + incoming_stock)`
