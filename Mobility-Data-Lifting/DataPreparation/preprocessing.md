## Pre-processing to format the original dataset<br>
### Presence file
The following transformations were performed on the original presence dataset:

**1. Data Cleaning & Filtering**
- **Removed invalid rows:** Deleted abnormal records (rows where the name and code shared the same 6-digit number).
- **Cleaned spatial locations:** Removed `code = 0` and `name = grenoble` from the record's location columns, to separate the territory the indicator is defined on from the specific spatial location of the record itself.
- **Handled aggregated time:** Cleared `start_time` and `end_time` when both equaled `0`, as this indicates aggregated time rather than a specific time interval.
- **Cleaned partition values:** Removed empty or `"none"` values from the partition column.
- **Cleaned indicator and status columns:** Cleaned the `status` and `indicator` columns. The `indicator` column now strictly contains indicator types (Presence, Fluctuation, and Attractiveness) and the `status` column only contains transportation modes, trip purposes, or empty values.

**2. Data Restructuring & Standardization**
- **Standardized indicator types:** Capitalized all indicator types (e.g., *Presence*, *Fluctuation*).
- **Separated mixed attributes:** The values from the `status` column were extracted into two new columns (`activity` and `transportation mode`) to separate them properly.
- **Mapped to SKOS concepts:** Renamed ambiguous or abbreviated values to match SKOS terminology. For instance, the generic word "other" (used for both transportation mode and trip purpose) was distinguished into explicit values ("otherTransportationMode" or "otherTripPurpose").
- **Added missing context:** 
  - Created a new column to specify the observed object (`Trips` or `Movers`).
  - Added explicit parent territory columns for the indicators (`territoryName = Grenoble` and `territoryID = 0`).
  - Created a new CSV file containing partitions and territories to complete the spaces, as the record/presence file did not contain them and their hierarchy.
- **Restructured result metrics:** Since the mapping tool can only process one result value per row, the three original result columns (value, total, density) cannot be handled simultaneously. To resolve this, you must either duplicate the rows to stack the results into a single column, or launch the mapping process multiple times (once for each specific column).


### Partitions files
- **Homogenized area properties:** Renamed the property describing the area (in square meters) to ensure consistent column naming across all partition files.