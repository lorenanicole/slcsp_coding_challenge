import unittest
from pathlib import Path
from calculate_slcsp import RateArea, Plan, RateAreasPlansProcessor, MetalLevel

CURRENT_DIR_PATH = Path(__file__).resolve().parent
FIXTURE_DIR_PATH = '{}/fixtures'.format(CURRENT_DIR_PATH)


class TestRateArea(unittest.TestCase):
    def setUp(self):
        self.plan_one = Plan(plan_id='MOARMONIES123', metal_level='Silver', monthly_premium=231.01, rate_area='(AK, 99)')
        self.plan_two = Plan(plan_id='CHEAPO11', metal_level='Silver', monthly_premium=301.01, rate_area='(AK, 99)')
        self.rate_areas = [
            RateArea(state='FL', rate_area=12, zipcodes=[12345], counties=['Under Da Sea']),
            RateArea(state='AK', rate_area=99, zipcodes=[90210], counties=['Snow Hut'], plans=[self.plan_one])
        ]

    def test_rate_area_does_not_set_sclsp_when_no_plans(self):
        rate_area = self.rate_areas[0]
        rate_area.calculate_slcsp()

        self.assertEqual(rate_area.get_slcsp_rate(), None)

    def test_rate_area_finds_sclsp_when_one_silver_plan(self):
        rate_area = self.rate_areas[1]
        rate_area.calculate_slcsp()

        self.assertEqual(rate_area.get_slcsp_rate(), self.plan_one.monthly_premium)
        self.assertEqual(rate_area.slcsp.plan_id, self.plan_one.plan_id)

    def test_rate_area_finds_sclsp_when_more_one_silver_plan(self):
        rate_area = self.rate_areas[1]
        rate_area.update_plans([self.plan_two])

        rate_area.calculate_slcsp()

        self.assertNotEqual(rate_area.get_slcsp_rate(), self.plan_one.monthly_premium)
        self.assertNotEqual(rate_area.slcsp.plan_id, self.plan_one.plan_id)

        self.assertEqual(rate_area.get_slcsp_rate(), self.plan_two.monthly_premium)
        self.assertEqual(rate_area.slcsp.plan_id, self.plan_two.plan_id)


class TestRateAreasPlansProcessor(unittest.TestCase):
    def setUp(self):
        self.rate_area_dummy_data = '{}/dummy_zips.csv'.format(FIXTURE_DIR_PATH)
        self.plans_dummy_data = '{}/dummy_plans.csv'.format(FIXTURE_DIR_PATH)
        self.slcsp_dummy_data = '{}/dummy_slcsp.csv'.format(FIXTURE_DIR_PATH)

    def tearDown(self):
        print('Invoking teardown')
        RateAreasPlansProcessor.rate_areas = {}
        RateAreasPlansProcessor.zipcodes_to_rate_areas = {}

    def test_processor_loads_rateareas(self):
        RateAreasPlansProcessor._load_rate_areas(self.rate_area_dummy_data)

        self.assertEqual(len(RateAreasPlansProcessor.rate_areas.keys()), 4)
        self.assertEqual(
            list(RateAreasPlansProcessor.rate_areas.keys()), ['(CA,50)', '(IL,12)', '(IL,11)', '(PR,42)']
                         )

    def test_processor_loads_silver_plans(self):
        RateAreasPlansProcessor._load_plans(self.plans_dummy_data, MetalLevel.Silver.name)

        self.assertEqual(len(RateAreasPlansProcessor.rate_areas.keys()), 4)
        self.assertEqual(
            list(RateAreasPlansProcessor.rate_areas.keys()),
            ['(CA,50)', '(IL,12)', '(IL,11)', '(PR,42)']
        )
        self.assertEqual(len(RateAreasPlansProcessor.rate_areas['(CA,50)'].plans), 4)
        self.assertEqual(len(RateAreasPlansProcessor.rate_areas['(IL,12)'].plans), 1)
        self.assertEqual(len(RateAreasPlansProcessor.rate_areas['(IL,11)'].plans), 1)
        self.assertEqual(len(RateAreasPlansProcessor.rate_areas['(PR,42)'].plans), 1)

    def test_processor_calculates_slscp(self):
        RateAreasPlansProcessor._load_rate_areas(self.rate_area_dummy_data)
        RateAreasPlansProcessor._load_plans(self.plans_dummy_data, MetalLevel.Silver.name)
        output_data, slcsp_headers = RateAreasPlansProcessor._calculate_zipcode_slcsp(self.slcsp_dummy_data)

        # Test that one plan silver plan -> the slscp rate
        expected_area_one_plan_sets_rate = {'zipcode': 55555, 'rate': 101.11}
        self.assertEqual(len(RateAreasPlansProcessor.rate_areas['(PR,42)'].plans), 1)

        # Test that many plans + redundant prices finds unique second lowest rate
        expected_unique_second_lowest_rate = {'zipcode': 90210, 'rate': 303.13}
        self.assertEqual(len(RateAreasPlansProcessor.rate_areas['(CA,50)'].plans), 4)

        # Test that zipcode in two areas is unable to locate a slscp
        expected_no_slcsp_in_too_many_ares = {'zipcode': 32032, 'rate': None}
        self.assertEqual(len(RateAreasPlansProcessor.zipcodes_to_rate_areas['32032']), 2)

        # [{'zipcode': 60647, 'rate': 123.12}, {'zipcode': 90210, 'rate': 258.33}, {'zipcode': 55555, 'rate': 101.11}, {'zipcode': 32032, 'rate': None}]
        print(output_data)

        self.assertEqual(
            output_data,
            [{'zipcode': 60647, 'rate': 123.12}, expected_unique_second_lowest_rate,
             expected_area_one_plan_sets_rate, expected_no_slcsp_in_too_many_ares]
        )

        self.assertEqual(slcsp_headers, ['zipcode', 'rate'])
