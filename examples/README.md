# Example: Analyzing the MT7927 Driver

This directory contains example outputs and usage demonstrations.

## Example 1: Analyze MT7927 Driver

```bash
# Run analyzer on MT7927 driver
python src/analyzer/analyzer.py path/to/mt7927e.sys -o mt7927-analysis.json

# View results
cat mt7927-analysis.json | jq '.'
```

## Example 2: Generate Driver Skeleton

```bash
# Generate Linux driver from analysis
python src/generator/generator.py \
    --analysis mt7927-analysis.json \
    --template network \
    --output ./mt7927-linux-driver
```

## Example 3: Build and Test

```bash
# Build the driver
cd mt7927-linux-driver
make

# Load the driver (requires sudo)
sudo insmod mt7927.ko

# Check kernel log
dmesg | tail -20

# Unload the driver
sudo rmmod mt7927
```

## Example Output Files

- `mt7927-analysis-example.json` - Sample analyzer output
- `driver-skeleton-example/` - Sample generated driver (coming soon)

## More Examples

See the [docs/](../docs/) directory for more detailed guides and tutorials.
