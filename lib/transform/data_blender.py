import copy
import json
import os
import re
import statistics as stats

import pandas as pd

from lib.tracking_decorator import TrackingDecorator

key_figure_group = "berlin-lor-housing-stock"

statistic_properties = [
    "apartments",
    "apartments_with_1_room",
    "apartments_with_2_rooms",
    "apartments_with_3_rooms",
    "apartments_with_4_rooms",
    "apartments_with_5_rooms",
    "apartments_with_6_rooms",
    "apartments_with_7_rooms_or_more",
    "apartments_rooms",
    "apartments_living_area",
    "residential_buildings",
    "residential_buildings_living_area",
    "residential_buildings_apartments",
    "residential_buildings_with_1_apartment",
    "residential_buildings_with_1_apartment_living_area",
    "residential_buildings_with_2_apartments",
    "residential_buildings_with_2_apartments_living_area",
    "residential_buildings_with_2_apartments_apartments",
    "residential_buildings_with_3_apartments",
    "residential_buildings_with_3_apartments_living_area",
    "residential_buildings_with_3_apartments_apartments"
]

statistics = [
    f"{key_figure_group}-2015-00",
    f"{key_figure_group}-2016-00",
    f"{key_figure_group}-2017-00",
    f"{key_figure_group}-2018-00",
    f"{key_figure_group}-2019-00",
    f"{key_figure_group}-2020-00",
    f"{key_figure_group}-2021-00",
    f"{key_figure_group}-2022-00"
]


@TrackingDecorator.track_time
def blend_data(source_path, results_path, clean=False, quiet=False):
    # Make results path
    os.makedirs(os.path.join(results_path), exist_ok=True)

    # Iterate over LOR area types
    for lor_area_type in ["districts", "forecast-areas", "district-regions", "planning-areas"]:

        # Initialize statistics
        json_statistics = {}

        # Iterate over statistics
        for statistics_name in statistics:
            year = re.search(r"\b\d{4}\b", statistics_name).group()
            half_year = re.search(r"\b\d{2}(?<!\d{4})\b", statistics_name).group()

            # Load geojson
            if lor_area_type == "districts":
                geojson = read_geojson_file(
                    os.path.join(source_path, "berlin-lor-geodata", f"berlin-lor-{lor_area_type}.geojson"))
            elif int(year) <= 2020:
                geojson = read_geojson_file(
                    os.path.join(source_path, "berlin-lor-geodata", f"berlin-lor-{lor_area_type}-until-2020.geojson"))
            elif int(year) >= 2021:
                # Beware: This statistics use the until-2020 nomenclature even beyond 2020
                geojson = read_geojson_file(
                    os.path.join(source_path, "berlin-lor-geodata", f"berlin-lor-{lor_area_type}-until-2020.geojson"))
            else:
                geojson = None

            # Load statistics
            csv_statistics = read_csv_file(os.path.join(source_path, statistics_name, f"{statistics_name}.csv"))

            # Load population statistics
            json_statistics_population = load_population_statistics(
                os.path.join(os.path.join(source_path, "berlin-lor-population-statistics"),
                             f"berlin-lor-population-{lor_area_type}-statistics.json"))

            # Extend geojson
            geojson_extended, json_statistics = extend_geojson(
                year=year,
                half_year=half_year,
                geojson=geojson,
                statistics_name=statistics_name,
                statistics=csv_statistics,
                json_statistics=json_statistics,
                json_statistics_population=json_statistics_population
            )

            # Write geojson file
            write_geojson_file(
                file_path=os.path.join(results_path, statistics_name,
                                       f"{key_figure_group}-{year}-{half_year}-{lor_area_type}.geojson"),
                statistic_name=f"{key_figure_group}-{year}-{half_year}-{lor_area_type}",
                geojson_content=geojson_extended,
                clean=clean,
                quiet=quiet
            )

        # Write json statistics file
        write_json_file(
            file_path=os.path.join(results_path, f"{key_figure_group}-statistics",
                                   f"{key_figure_group}-{lor_area_type}-statistics.json"),
            statistic_name=f"{key_figure_group}-{lor_area_type}-statistics",
            json_content=json_statistics,
            clean=clean,
            quiet=quiet
        )


def read_csv_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as csv_file:
            return pd.read_csv(csv_file, dtype={"id": "str"})
    else:
        return None


def read_geojson_file(file_path):
    with open(file=file_path, mode="r", encoding="utf-8") as geojson_file:
        return json.load(geojson_file, strict=False)


def write_geojson_file(file_path, statistic_name, geojson_content, clean, quiet):
    if not os.path.exists(file_path) or clean:

        # Make results path
        path_name = os.path.dirname(file_path)
        os.makedirs(os.path.join(path_name), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as geojson_file:
            json.dump(geojson_content, geojson_file, ensure_ascii=False)

            if not quiet:
                print(f"✓ Blend data from {statistic_name} into {os.path.basename(file_path)}")


def write_json_file(file_path, statistic_name, json_content, clean, quiet):
    if not os.path.exists(file_path) or clean:

        # Make results path
        path_name = os.path.dirname(file_path)
        os.makedirs(os.path.join(path_name), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(json_content, json_file, ensure_ascii=False)

            if not quiet:
                print(f"✓ Aggregate data from {statistic_name} into {os.path.basename(file_path)}")


def extend_geojson(year, half_year, geojson, statistics_name, statistics, json_statistics, json_statistics_population):
    geojson_extended = copy.deepcopy(geojson)

    # Check for missing files
    if statistics is None:
        print(f"✗️ No data in {statistics_name}")

    # Check if file needs to be created
    for feature in sorted(geojson_extended["features"], key=lambda feature: feature["properties"]["id"]):
        feature_id = feature["properties"]["id"]
        area_sqm = feature["properties"]["area"]
        area_sqkm = area_sqm / 1_000_000
        inhabitants = get_inhabitants(json_statistics_population, year, feature_id)

        # Filter statistics
        statistic_filtered = statistics[statistics["id"].astype(str).str.startswith(feature_id)]

        # Check for missing data
        if statistic_filtered.shape[0] == 0 or \
                inhabitants is None or inhabitants == 0:
            print(f"✗️ No data in {statistics_name} for id={feature_id}")
            continue

        # Blend data
        feature = blend_data_into_feature(feature=feature, statistics=statistic_filtered, area_sqkm=area_sqkm,
                                          inhabitants=inhabitants)

        # Build structure
        if year not in json_statistics:
            json_statistics[year] = {}
        if half_year not in json_statistics[year]:
            json_statistics[year][half_year] = {}

        # Add properties
        json_statistics[year][half_year][feature_id] = feature["properties"]

    # Calculate average and median values
    for year, half_years in json_statistics.items():
        for half_year, feature_ids in half_years.items():
            values = {}

            for feature_id, properties in feature_ids.items():
                for property_name, property_value in properties.items():
                    if property_name in statistic_properties:
                        if property_name not in values:
                            values[property_name] = []
                        values[property_name].append(property_value)

            json_statistics[year][half_year]["average"] = {key: stats.mean(lst) for key, lst in values.items()}
            json_statistics[year][half_year]["median"] = {key: stats.median(lst) for key, lst in values.items()}

    return geojson_extended, json_statistics


def blend_data_into_feature(feature, statistics, area_sqkm, inhabitants):
    # Add new properties
    for property_name in statistic_properties:
        add_property_with_modifiers(feature, statistics, property_name, area_sqkm, inhabitants)

    return feature


def add_property(feature, statistics, property_name):
    if statistics is not None and property_name in statistics:
        try:
            feature["properties"][f"{property_name}"] = float(statistics[property_name].sum())
        except ValueError:
            feature["properties"][f"{property_name}"] = 0


def add_property_with_modifiers(feature, statistics, property_name, total_area_sqkm, inhabitants):
    if statistics is not None and property_name in statistics:
        try:
            feature["properties"][f"{property_name}"] = float(statistics[property_name].sum())
            if total_area_sqkm is not None:
                feature["properties"][f"{property_name}_per_sqkm"] = round(
                    float(statistics[property_name].sum()) / total_area_sqkm, 2)
            if inhabitants is not None:
                feature["properties"][f"{property_name}_per_inhabitant"] = round(
                    float(statistics[property_name].sum()) / inhabitants, 2)
        except ValueError:
            feature["properties"][f"{property_name}"] = 0

            if total_area_sqkm is not None:
                feature["properties"][f"{property_name}_per_sqkm"] = 0
            if inhabitants is not None:
                feature["properties"][f"{property_name}_per_inhabitant"] = 0
        except TypeError:
            feature["properties"][f"{property_name}"] = 0

            if total_area_sqkm is not None:
                feature["properties"][f"{property_name}_per_sqkm"] = 0
            if inhabitants is not None:
                feature["properties"][f"{property_name}_per_inhabitant"] = 0

def load_population_statistics(file_path):
    with open(file=file_path, mode="r", encoding="utf-8") as json_file:
        return json.load(json_file, strict=False)


def get_inhabitants(population_statistics, year, feature_id):
    try:
        return population_statistics[year]["02"][feature_id]["inhabitants"]
    except KeyError:
        print(f"✗️ No population data for id={feature_id}")
        return None
