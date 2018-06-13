import csv
from enum import Enum
# import pandas as pd
from pathlib import Path
import logging

__author__ = 'lorenamesa'

CURRENT_DIR_PATH = Path(__file__).resolve().parent
DATA_DIR_PATH = '{}/data'.format(CURRENT_DIR_PATH)

logger = logging.getLogger(__name__)

# Simple Data Exploration
# Included as example for how may use some Python libraries not in the standard library to explore

# Zips Metadata
# zips_df = pd.read_csv('{}/zips.csv'.format(DATA_DIR_PATH))
# zips_headers = zips_df.columns.values  # ['zipcode' 'state' 'county_code' 'name' 'rate_area']
# zips_df_shape = zips_df.shape  # (51541, 5)

# unique_zip_codes = zips_df.zipcode.unique()
# num_unique_zip_codes = unique_zip_codes.size   # 38804 unique zipcodes

# zips_df['rate_area_display'] = '('+ zips_df.state.astype(str) + ',' + zips_df.rate_area.astype(str) + ')'
# print(zips_df.rate_area_display)  # 477
# print(zips_df.rate_area_display.unique().size) == size

# SLCSP Metadata
# slcsp_df = pd.read_csv('{}/slcsp.csv'.format(DATA_DIR_PATH))
# slcsp_headers = slcsp_df.columns.values  # ['zipcode' 'rate']
# slcsp_df_shape = slcsp_df.shape  # (51, 2)
# print(slcsp_headers, slcsp_df_shape)

# Plans Metadata
# plans_df = pd.read_csv('{}/plans.csv'.format(DATA_DIR_PATH))
# plans_headers = plans_df.columns.values  # ['plan_id' 'state' 'metal_level' 'rate' 'rate_area']
# plans_df_shape = plans_df.shape  # (22240, 5)
# print(plans_headers, plans_df_shape)


class MetalLevel(Enum):
    """
    Enum of Health Care plans coverage ('metal level') level
    """
    Bronze = 'Bronze'
    Silver = 'Silver'
    Platinum = 'Platinum'
    Catastrophic = 'Catastrophic'


class RateArea(object):
    """
    Python class representing a RateArea, the representation of a geographic area
    with associated plans.
    """

    def __init__(self, state, rate_area, zipcodes, counties, plans=None):
        """
        :param  state       str postal abreivation of a state
        :param  rate_area   numeric region in the state for the rates
        :param  zipcodes    set of zipcodes the ratearea is in effect for
        :param  counties    set of counties the ratearea is in effect for
        """
        self.state = state
        self.rate_area = rate_area
        self.zipcodes = set(zipcodes)
        self.counties = set(counties)
        self.plans = set(plans) if plans else set([])
        self.slcsp = None

    def __str__(self):
        return '({},{})'.format(self.state, self.rate_area)

    def update_zipcodes(self, zipcodes):
        if not isinstance(zipcodes, list):
            zipcodes = list(zipcodes)
        self.zipcodes.update(zipcodes)

    def update_counties(self, counties):
        if not isinstance(counties, list):
            counties = list(counties)
        self.counties.update(counties)

    def update_plans(self, plans):
        if not self.plans:
            self.plans = set([])
        if not isinstance(plans, list):
            plans = list(plans)
        self.plans.update(plans)

    def get_slcsp_rate(self):
        if self.slcsp:
            return float(self.slcsp.monthly_premium)
        else:
            return None

    def calculate_slcsp(self):
        """
        Calculates the SLCSP for the RateArea by filtering to the silver metal level and sets
        the RestArea slcsp attribute to the second lowest plan monthly premium (unique val) or uses the lowest
        if only one plan available

        If none, no action

        :return None
        """
        if not self.plans:
            return

        silver_plans = list(filter(lambda p: p.metal_level == MetalLevel.Silver, self.plans))

        if len(silver_plans) == 1:
            silver_plans[0].update_is_slcsp(True)
            self.slcsp = silver_plans[0]

        else:
            unique_vals = {}
            for plan in silver_plans:
                if not unique_vals.get(plan.monthly_premium):
                    unique_vals[plan.monthly_premium] = plan

            unique_vals = sorted(list(unique_vals.values()), key=lambda p: p.monthly_premium)
            self.slcsp = unique_vals[1]
            unique_vals[1].update_is_slcsp(True)


class Plan(object):

    def __init__(self, plan_id, metal_level, monthly_premium, rate_area, is_slcsp=False):
        """
        :param  plan_id - str alphanumeric character for plan_id
        :param  metal_level - enum representing the metal level, or coverage level
        :param  monthly_premium - monthly premium as float
        :param  rate_area - rate area represented as str of '(state, num)'
        :param  is_slcsp - default false, bool representing if plan is slcsp for it's rate_area
        """
        self.plan_id = plan_id
        self.metal_level = MetalLevel(metal_level)  # .name for str, .value for value
        self.monthly_premium = float(monthly_premium)
        self.rate_area_number = rate_area
        self.is_slcsp = is_slcsp

    def update_is_slcsp(self, value):
        self.is_slcsp = value


class RateAreasPlansProcessor(object):
    rate_areas = {}
    zipcodes_to_rate_areas = {}

    @classmethod
    def parse_plan_name(cls, name):
        return name.capitalize().strip()

    @classmethod
    def _load_rate_areas(cls, zips_data):
        with open(zips_data, 'r') as zips_csvfile:
            zips_reader = csv.DictReader(zips_csvfile)
            for row in zips_reader:
                state = row.get('state')
                rate_area_number = row.get('rate_area')
                rate_area_display = '({},{})'.format(state, rate_area_number)
                rate_area_obj = RateAreasPlansProcessor.rate_areas.get(rate_area_display)
                zipcode = row.get('zipcode')
                name = row.get('name')

                # Track zipcode to rate areas in a map, this'll let us easily skip ambiguous
                # zip codes that are in more than one rate area and therefore the SLCSP cannot be found
                if RateAreasPlansProcessor.zipcodes_to_rate_areas.get(zipcode):
                    RateAreasPlansProcessor.zipcodes_to_rate_areas[zipcode].update([rate_area_display])
                else:
                    RateAreasPlansProcessor.zipcodes_to_rate_areas[zipcode] = {rate_area_display}

                if rate_area_obj:
                    rate_area_obj.update_zipcodes([zipcode])
                    rate_area_obj.update_counties([name])
                else:
                    rate_area_obj = RateArea(state=state, rate_area=rate_area_number, zipcodes=[zipcode],
                                             counties=[name])
                    RateAreasPlansProcessor.rate_areas[rate_area_display] = rate_area_obj

    @classmethod
    def _load_plans(cls, plans_data, plan_type):
        with open(plans_data, 'r') as plans_csvfile:
            plans_reader = csv.DictReader(plans_csvfile)
            for row in plans_reader:
                metal_level = RateAreasPlansProcessor.parse_plan_name(row.get('metal_level', ''))
                if metal_level and metal_level == plan_type:

                    rate_area_number = row.get('rate_area')
                    state = row.get('state')
                    rate_area_display = '({},{})'.format(state, rate_area_number)

                    # Since plans do not have zipcode info, we don't add to zipcode_to_rate_area map
                    plan = Plan(plan_id=row.get('plan_id'), metal_level=metal_level, monthly_premium=row.get('rate'),
                                rate_area=rate_area_display)

                    # Map silver plans to rate areas (a rate area has plans ...), but first check rate area exists
                    rate_area_obj = RateAreasPlansProcessor.rate_areas.get(rate_area_display)
                    if not rate_area_obj:
                        rate_area_obj = RateArea(
                            state=state, rate_area=rate_area_number, zipcodes=[], counties=[], plans=[plan]
                        )
                        RateAreasPlansProcessor.rate_areas[rate_area_display] = rate_area_obj
                    else:
                        rate_area_obj.update_plans([plan])

    @classmethod
    def _calculate_zipcode_slcsp(cls, slcsp_data):
        output_data = []

        with open(slcsp_data, 'r') as slcsp_csvfile:
            slcsp_reader = csv.DictReader(slcsp_csvfile)
            slcsp_headers = slcsp_reader.fieldnames

            for row in slcsp_reader:
                zipcode = row.get('zipcode')
                rate_areas = RateAreasPlansProcessor.zipcodes_to_rate_areas.get(zipcode)
                rate = None
                if not rate_areas:
                    logging.info('Skipping zipcode {} as no matching rate area'.format(zipcode))
                elif len(rate_areas) > 1:
                    logging.info('Skipping zipcode {} as more than 1 matching rate area: {}'.format(zipcode, rate_areas))
                else:
                    zipcode_rate_area = list(rate_areas)[0]
                    rate_area_obj = RateAreasPlansProcessor.rate_areas.get(zipcode_rate_area)
                    rate_area_obj.calculate_slcsp()
                    if rate_area_obj.slcsp:
                        rate = rate_area_obj.get_slcsp_rate()

                output_data.append({'zipcode': int(zipcode), 'rate': rate})

        return output_data, slcsp_headers

    @classmethod
    def load(cls, plans_data, zips_data, slcsp_data):

        # Load all zips to create rate areas
        RateAreasPlansProcessor._load_rate_areas(zips_data)

        # Load only silver plans
        RateAreasPlansProcessor._load_plans(plans_data, MetalLevel.Silver.name)

        # Load zips in slcsp data
        # 1. If zip has no matching RateArea do nothing
        # 2. Elif zip has more than one rate area do nothing
        # 3. Else if zip has one rate area calculate slcsp
        output_data, slcsp_headers = RateAreasPlansProcessor._calculate_zipcode_slcsp(slcsp_data)

        with open(slcsp_data, 'w') as slcsp_csvfile:
            slcsp_writer = csv.DictWriter(slcsp_csvfile, fieldnames=slcsp_headers)
            slcsp_writer.writeheader()
            for row in output_data:
                slcsp_writer.writerow(row)

if __name__ == '__main__':

    RateAreasPlansProcessor.load(
        plans_data='{}/plans.csv'.format(DATA_DIR_PATH),
        zips_data='{}/zips.csv'.format(DATA_DIR_PATH),
        slcsp_data='{}/slcsp.csv'.format(DATA_DIR_PATH)
    )
