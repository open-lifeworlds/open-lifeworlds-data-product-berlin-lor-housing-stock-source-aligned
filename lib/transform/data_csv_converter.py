import os

import pandas as pd

from lib.tracking_decorator import TrackingDecorator


@TrackingDecorator.track_time
def convert_data_to_csv(source_path, results_path, clean=False, quiet=False):
    # Iterate over files
    for subdir, dirs, files in sorted(os.walk(source_path)):

        # Make results path
        subdir = subdir.replace(f"{source_path}/", "")
        os.makedirs(os.path.join(results_path, subdir), exist_ok=True)

        for file_name in sorted(files):
            source_file_path = os.path.join(source_path, subdir, file_name)
            convert_file_to_csv(source_file_path, clean=clean, quiet=quiet)


def convert_file_to_csv(source_file_path, clean=False, quiet=False):
    source_file_name, source_file_extension = os.path.splitext(source_file_path)
    file_path_csv = f"{source_file_name}.csv"

    # Check if result needs to be generated
    if clean or not os.path.exists(file_path_csv):
        # Determine engine
        if source_file_extension == ".xlsx":
            engine = "openpyxl"
        elif source_file_extension == ".xls":
            engine = None
        else:
            return

        year = os.path.basename(source_file_name).split(sep="-")[4]
        half_year = os.path.basename(source_file_name).split(sep="-")[5]

        # Set default values
        drop_columns = []

        try:
            dataframes = []

            if source_file_name.endswith(f"{year}-{half_year}"):

                sheets = ["Tab. 7", "Tab. 8", "Tab. 9", "Tab. 10", "Tab. 11", "Tab. 12", "Tab. 13", "Tab. 14",
                          "Tab. 15", "Tab. 16", "Tab. 17", "Tab. 18"]
                skiprows = 11
                names = ["id", "name", "apartments", "apartments_with_1_room", "apartments_with_2_rooms",
                         "apartments_with_3_rooms", "apartments_with_4_rooms", "apartments_with_5_rooms",
                         "apartments_with_6_rooms", "_", "apartments_with_7_rooms_or_more", "apartments_rooms",
                         "apartments_living_area",
                         "residential_buildings", "residential_buildings_living_area",
                         "residential_buildings_apartments",
                         "residential_buildings_with_1_apartment", "residential_buildings_with_1_apartment_living_area",
                         "residential_buildings_with_2_apartment", "residential_buildings_with_2_apartment_living_area",
                         "residential_buildings_with_2_apartment_apartments",
                         "residential_buildings_with_3_apartment", "residential_buildings_with_3_apartment_living_area",
                         "residential_buildings_with_3_apartment_apartments"]
                drop_columns = ["name", "_"]
            else:
                sheets = []
                skiprows = 0
                names = []
                drop_columns = []

            # Iterate over sheets
            for sheet in sheets:
                dataframes.append(
                    pd.read_excel(source_file_path, engine=engine, sheet_name=sheet, skiprows=skiprows,
                                  usecols=list(range(0, len(names))), names=names)
                        .drop(columns=drop_columns, errors="ignore")
                        .dropna()
                        .replace("–", 0)
                        .assign(id=lambda x: x["id"].astype(str).str.zfill(8))
                )

            # Concatenate data frames
            dataframe = pd.concat([df.set_index("id") for df in dataframes], axis=0).reset_index()

            # Write csv file
            if dataframe.shape[0] > 0:
                dataframe.to_csv(file_path_csv, index=False)
                if not quiet:
                    print(f"✓ Convert {os.path.basename(file_path_csv)}")
            else:
                if not quiet:
                    print(dataframe.head())
                    print(f"✗️ Empty {os.path.basename(file_path_csv)}")
        except Exception as e:
            print(f"✗️ Exception: {str(e)}")
    elif not quiet:
        print(f"✓ Already exists {os.path.basename(file_path_csv)}")
