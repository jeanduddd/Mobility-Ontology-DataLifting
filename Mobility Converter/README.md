# Input file documentation

This tool is designed to be flexible. It supports three file types : CSV, JSON and GeoJSON<br>

### CSV files
The CSV format is used to convert data fomated in a classic table.<br>
Earch CSV file must represent only one entity at a time (space, indicator, record).
<br><br>
**CSV formating rules :**
* the file must contain the column names
* the separator used must be a semicolumn ';'

*Example `spaces.csv` file :*
```csv
hasSpaceType;hasSpaceID;hasName
Territory;0;France
Partition;Regions;Regions
Zone;1;PACA;
```
### JSON files
this file format is very flexible and the converter handle two types of JSON format.<br>For each, you can either use the classic json format as an array with objects inside brackets, or as a list of objects separated with commas
1. flat JSON<br>
This format is equivalent to a CSV file but formated as JSON objects<br>

*Example `indicator.json` file :*
```json
{
    "hasIndicatorType": "Presence",
    "hasCalculationMethod": "Ratio", 
    "hasObject": "Movers",
    "onTerritorySpaceID":"0",
    "onTerritoryName": "France"
},
{
    "hasIndicatorType": "Presence",
    "hasCalculationMethod": "Density", 
    "hasObject": "Trips",
    "onTerritorySpaceID":"2",
    "onTerritoryName": "Italy"
}
```
2. embedded JSON
this format enable let the tool deduce relations thanks to the file hierarchy :
* spaces inside spaces<br>

*Example `spaceInSpace.json` file :*
```json
[
  {
    "hasSpaceType": "Territory",
    "hasName": "France",
    "hasSpaceID": "0",
    "contains": [
      {
        "hasSpaceType": "Partition",
        "hasSpaceID": "Regions",
        "hasName": "Regions",
        "contains": [
          {
            "hasSpaceType": "Zone",
            "hasSpaceID": "1",
            "hasName": "PACA"
          }
        ]
      }
    ]
  }
]
```
* spaces inside indicators<br>

Example `spaceInIndicator.json` file :*
```json
[
  {
    "hasIndicatorType": "Presence",
    "hasCalculationMethod": "Ratio",
    "hasObject": "Movers",
    "hasTerritories": [
      {
        "onTerritoryName": "PACA",
        "onTerritorySpaceID": "1"
      },
      {
        "onTerritoryName": "Paris",
        "onTerritorySpaceID": "3"
      }
    ]
  }
]
```
* records inside indicators<br>

*Example `recordInIndicator.json` file :*
```json
{
  "hasIndicatorType": "Presence",
  "hasCalculationMethod": "Ratio",
  "hasObject": "Movers",
  "onTerritoryName": "France",
  "onTerritorySpaceID": "0",

  "hasRecords": [
    {
      "hasValue": "134.754",
      "onSpatialLocationID": "3",
      "onSpatialLocationName": "Paris"
    },
    {
      "hasValue": "13",
      "onSpatialLocationID": "1",
      "onSpatialLocationName": "PACA"
    }
  ]
}

```
### GeoJSON files
GeoJSON files are made to manipulate geometries. There are two distinct use cases

1. Autonomous space GeoJSON file<br>
This type of file contains both the geometries and the informations necessary to describe a space in the property section.<br>

*Example `spaces.geojson` file :*
```geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [5.7, 45.1],
            [5.8, 45.2],
            [5.6, 45.3],
            [5.7, 45.1]
          ]
        ]
      },
      "properties": {
        "hasSpaceType": "Territory",
        "hasName": "France",
        "hasSpaceID": "0"
      }
    },
    {
      "type": "Feature",
      "geometry": null,
      "properties": {
        "hasSpaceType": "Partition",
        "hasName": "Regions",
        "hasSpaceID": "1"
      }
    }
  ]
}

```

2. Spatial Join File
In this case, the GeoJSON file acts as an enrichment of the files that can't hold geometries. It only requires to have common name and ID properties to merge it correctly<br>

*Example `geometries.geojson` file :*
```geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [[[5.7,45.1],[5.8,45.2],[5.6,45.3],[5.7,45.1]]]},
      "properties": {
        "hasAssociatedSpaceID": "3",
        "hasAssociatedName": "Paris"
      }
    }
  ]
}
```

## Mandatory Fields

In order to generate the knowledge graph, each object mun have at least some necessaty information.<br>Ever property must be entered in the config file in order to classify it in the write category and process correctly the input files.<br>Every non mandatory properties can also be found in the config file


### Spaces
* `hasSpaceID` : Unique identifier of the space
* `hasName` : Name of the space
* `hasSpaceType` : Type of the space (Territory, Partition, Zone)

### Indicators
* `hasIndicatorType` : Type of the indicator (Presence, Fluctuation, Attractiveness, etc...)
* `hasObject` : The observed object
* `hasCalculationMethod` : The calculation method used to compute the indicator (Count, Ratio, Density)
* `onTerritoryName` : The name of the Territory the indicator is defined on
* `onTerritorySpaceID` : The spaceID of the Territory the indicator is defined on
> **Exception embedded JSON (indicator contains spaces) :** If spaces are directly embedded into the indicator, properties `onTerritoryName` and `onTerritorySpaceID` are not mandatory, as it is deduced from the child objects.


### Records
* `hasValue` : The value of the record
* `linkedIndicatorType`, `linkedObject`, `linkedCalculationMethod`, `linkedIndicatorTerritoryName`, `linkedIndicatorTerritorySpaceID` : The infomation defining the indicator the record is linked to
> **Exception enbedded JSON (indicator contains records) :** 
If records are directly embedded into the indicator, properties `linkedIndicatorType`, `linkedObject`, `linkedCalculationMethod`, `linkedIndicatorTerritoryName` and `linkedIndicatorTerritorySpaceID` are not mandatory, as it is deduced from the parent objects. The only property required is `hasValue`

### GeoJSON
* **file used to add geometry information to files that cannot have any (as CSV or JSON):** The required properties are `hasAssociatedSpaceID` and `hasAssociatedName` used to find the correct space with which to associate the geometry
* **Autonomous space file :** The same space properties defined before are required. Property `geometry` is mandatory by definition of the GeoJSON format, even if it can hold the value 'null'