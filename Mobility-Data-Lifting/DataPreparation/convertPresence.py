import pandas as pd

df = pd.read_csv("presence.csv", sep=';', dtype=str)

TransportMapping = {
    "Pts": "PublicTransportation",
    "Other": "OtherTransportationMode"
}
ActivityMapping = {
    "Other": "OtherTripPurpose"
}

Activities = ["Work","Home","Studying","Shopping","Leisure","OtherTripPurpose"]
TransportationModes = ["Walk","Bike","Car","PublicTransportation","OtherTransportationMode"]

#remove the strange name and code spaces
df = df[~df["name"].str.fullmatch(r"^\d{6}$", na=False)]

#drop the unused columns
df = df.drop(["total_multi","value_multi","time","space"],axis=1)

#remove code 0 and name grenble from code and name column
df["code"] = df["code"].replace("0", None)
df["name"] = df["name"].replace("grenoble", None)

#capitalize status and indicator columns
df["status"] = df["status"].str.capitalize()
df["indicator"] = df["indicator"].str.capitalize()

#rename the abreviated or ambigous mode and activity
modesMask = df["indicator"] == "Modes"
activityMask = df["indicator"] == "Activity"
df.loc[modesMask, "status"] = df.loc[modesMask, "status"].map(TransportMapping).fillna(df.loc[modesMask, "status"])
df.loc[activityMask, "status"] = df.loc[activityMask, "status"].map(ActivityMapping).fillna(df.loc[activityMask, "status"])

#add the corresponding object in a new column
df.loc[df["status"].isin(Activities + ["Activity"]), "linkedObject"] = "Trips"
df.loc[df["status"].isin(TransportationModes + ["Modes"]), "linkedObject"] = "Movers"
df.loc[df["indicator"].isin(["Attractiveness"]), "linkedObject"] = "Movers"
df.loc[df["indicator"].isin(["Fluctuation"]), "linkedObject"] = "Movers"

#update the "modes" and "activity" values in status and indicator columns
df.loc[df["indicator"].isin(["Modes", "Activity"]), "indicator"] = "Presence"
df.loc[df["status"].isin(["Modes", "Activity"]), "status"] = None

#add activity and transportation mode columns
df["activity"] = None
df["transportationMode"] = None

#fill activity and transportation mode columns with the corresponding purpose or transportation mode to separate them
df.loc[df["status"].isin(Activities), "activity"] = df.loc[df["status"].isin(Activities), "status"]
df.loc[df["status"].isin(TransportationModes), "transportationMode"] = df.loc[df["status"].isin(TransportationModes), "status"]
df = df.drop(columns=["status"])

#add the territory the records' indicator is defined on
df["linkedIndicatorTerritoryName"] = "grenoble"
df["linkedIndicatorTerritorySpaceID"] = "0"

#remove start and end time when they both equals to 0
if "start" in df.columns and "end" in df.columns:
    zeroMask = (df["start"].isin([0, "0"])) & (df["end"].isin([0, "0"]))
    df.loc[zeroMask, ["start", "end"]] = None

#we separate the result values, as a line can only contain one result value.
dfFinal = pd.DataFrame()
results = ["total","value","density"]

for map in [["total","Count"],["value","Ratio"],["density","Density"]]:
  newDF = df.copy()
  newDF["linkedCalculationMethod"] = map[1]
  columnsToDrop = [col for col in results if col != map[0]]
  newDF = newDF.drop(columns=columnsToDrop, axis=1)
  if map[1]=="Count":
      idxToDelete = df.index[df["indicator"] == "Attractiveness" ].tolist()
      newDF.drop(labels = idxToDelete, axis=0, inplace = True)
  if map[1]=="Density":
    idxToDelete = df.index[(df["indicator"] == "Attractiveness") | (df["indicator"] == "Fluctuation") ].tolist()
    newDF.drop(labels = idxToDelete, axis=0, inplace = True)

  newDF = newDF.rename(columns={map[0]: "total"})
  dfFinal = pd.concat([dfFinal,newDF], ignore_index=True)

#we create a dataframe to complete the spaces, as the record file did not create the partition, the territory and their hierarchy
remainingSpaces = pd.DataFrame(columns=["spaceID","name","spaceType","parentID"])
partitions = df["partition"].copy().drop_duplicates().tolist()
partitions.remove("none")
print(partitions)

for partition in partitions:
  remainingSpaces.loc[len(remainingSpaces.index)] = [partition, partition, "Partition",0]
  print([partition, partition, "Partition"])
remainingSpaces.loc[len(remainingSpaces.index)] = ["0", "grenoble", "Territory",None]

remainingSpaces.to_csv("partitions&grenoble.csv",sep=";",index=False)

#clean the partition column
dfFinal.loc[dfFinal["partition"] == "none", "partition"] = None
dfFinal = dfFinal.rename(columns={"partition": "parentID"})
dfFinal.to_csv("cleanedPresence.csv",sep=";",index=False)

