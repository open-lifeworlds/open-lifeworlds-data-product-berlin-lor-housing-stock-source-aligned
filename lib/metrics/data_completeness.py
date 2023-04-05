import json
import os
import unittest

file_path = os.path.realpath(__file__)
script_path = os.path.dirname(file_path)

data_path = os.path.join(script_path, "..", "..", "data")

key_figure_group = "berlin-lor-housing-stock"

statistic_properties = [
    "apartments", "apartments_with_1_room", "apartments_with_2_rooms", "apartments_with_3_rooms",
    "apartments_with_4_rooms", "apartments_with_5_rooms", "apartments_with_6_rooms",
    "apartments_with_7_rooms_or_more", "apartments_rooms", "apartments_living_area",
    "residential_buildings", "residential_buildings_living_area", "residential_buildings_apartments",
    "residential_buildings_with_1_apartment", "residential_buildings_with_1_apartment_living_area",
    "residential_buildings_with_2_apartment", "residential_buildings_with_2_apartment_living_area",
    "residential_buildings_with_2_apartment_apartments",
    "residential_buildings_with_3_apartment", "residential_buildings_with_3_apartment_living_area",
    "residential_buildings_with_3_apartment_apartments"
]


class FilesTestCase(unittest.TestCase):
    pass


for year in [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]:
    for half_year in ["00"]:
        for lor_area_type in ["districts", "forecast-areas", "district-regions", "planning-areas"]:
            file = os.path.join(data_path, f"{key_figure_group}-{year}-{half_year}",
                                f"{key_figure_group}-{year}-{half_year}-{lor_area_type}.geojson")
            setattr(
                FilesTestCase,
                f"test_{key_figure_group}_{year}_{half_year}_{lor_area_type}".replace('-', '_'),
                lambda self, file=file: self.assertTrue(os.path.exists(file))
            )


class PropertiesTestCase(unittest.TestCase):
    pass


for year in [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]:
    for half_year in ["00"]:
        for lor_area_type in ["districts", "forecast-areas", "district-regions", "planning-areas"]:
            file = os.path.join(data_path, f"{key_figure_group}-{year}-{half_year}",
                                f"{key_figure_group}-{year}-{half_year}-{lor_area_type}.geojson")
            if os.path.exists(file):
                with open(file=file, mode="r", encoding="utf-8") as geojson_file:
                    geojson = json.load(geojson_file, strict=False)

                for feature in geojson["features"]:
                    feature_id = feature["properties"]["id"]
                    setattr(
                        PropertiesTestCase,
                        f"test_{key_figure_group}_{year}_{half_year}_{lor_area_type}_{feature_id}".replace('-', '_'),
                        lambda self, feature=feature: self.assertTrue(
                            all(property in feature["properties"] for property in statistic_properties))
                    )

if __name__ == '__main__':
    unittest.main()
