# Dataset Directory

Place your raw dataset file `consolidated_traffic_data.csv` here (or pass custom paths via CLI).

## Expected Schema
The dataset should contain standard flow-level statistical metrics:
- `duration`: Flow duration in microseconds
- `total_fiat`, `total_biat`: Total forward / backward inter-arrival time
- `min_fiat`, `min_biat`, `max_fiat`, `max_biat`, `mean_fiat`, `mean_biat`: FWD/BWD inter-arrival time statistics
- `flowPktsPerSecond`, `flowBytesPerSecond`: Flow packet and byte rate
- `min_flowiat`, `max_flowiat`, `mean_flowiat`, `std_flowiat`: Overall flow inter-arrival time statistics
- `min_active`, `mean_active`, `max_active`, `std_active`: Active flow duration statistics
- `min_idle`, `mean_idle`, `max_idle`, `std_idle`: Idle flow duration statistics
- `traffic_type`: Target application traffic category label
