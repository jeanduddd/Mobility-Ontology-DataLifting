## Pre-processing to format the original dataset<br>
### Presence file
The following transformations were performed on the original presence dataset:

**1. Data Cleaning & Filtering**
The following transformations have been made using the **[convertPresence](./convertPresence)** script :
- **Removed invalid rows:** Deleted abnormal records (rows where the name and code shared the same 6-digit number).
- **Standardized spatial locations:** Empty the cells values in the `code` and `name` columns when `code = 0` and `name = grenoble`. This specific value represents the global territory the indicator is defined on, not a specific spatial zone for the record. Leaving the cell empty prevents the tool from linking the record to the territory,correctly reflecting that the data is spatially aggregated.
- **Standardized time intervals:** Replaced `start_time` and `end_time` cell values with empty/null values when both equaled 0. A value of 0 indicates an aggregated time over the whole period, rather than a specific time interval. This prevent from linking the record to an interval of duration 0.
- **Standardized partition values:** Replaced the string "none" with truly empty cells in the partition column, without deleting the corresponding rows.
- **Cleaned indicator and status columns:** Cleaned the `status` and `indicator` columns. The `indicator` column now strictly contains indicator types (Presence, Fluctuation, and Attractiveness) and the `status` column only contains transportation modes, trip purposes, or empty values.

**2. Data Restructuring & Standardization**
The following transformations have been made using the **[convertPresence](./convertPresence)** script :
- **Standardized indicator types:** Capitalized all indicator types (e.g., *Presence*, *Fluctuation*).
- **Separated mixed attributes:** The values from the `status` column were extracted into two new columns (`activity` and `transportation mode`) to separate them properly.
- **Mapped to SKOS concepts:** Renamed ambiguous or abbreviated values to match SKOS terminology. For instance, the generic word "other" (used for both transportation mode and trip purpose) was distinguished into explicit values ("otherTransportationMode" or "otherTripPurpose").
- **Added missing context:** 
  - Created a new column to specify the observed object (`Trips` or `Movers`).
  - Added explicit parent territory columns for the indicators (`territoryName = Grenoble` and `territoryID = 0`).
- **Restructured result metrics:** Since the mapping tool can only process one result value per row, the three original result columns (`value`, `total`, `density`) cannot be handled simultaneously. The chosen approach was to duplicate and stack the dataset. The script processes the dataframe multiple times to extract each metric into a single shared column, assigning the correct `linkedCalculationMethod` to each:
  - The `total` column values are mapped to the **Count** method.
  - The `value` column values are mapped to the **Ratio** method.
  - The `density` column values are mapped to the **Density** method.
This logic is applied depending on the indicator. For example, 'Attractiveness' only generates Ratio records, 'Fluctuation' generates only Count and Ratio records, and 'Presence' generates Count, Ratio and Density records.


### Partition files
- **Homogenized area properties:** Renamed the property describing the area (in square meters) to ensure consistent column naming across all partition files. This change have been made manually.

### Space file creation
- **Generated space hierarchy:** Created a new CSV file containing the definitions of partitions and territories. This was necessary to complete the record file, as the original `presence` dataset only contained specific spatial zones and lacked these elements and their hierarchical relationships.
