#### Challenge

https://github.com/adhocteam/homework/tree/master/slcsp

#### How to Execute Code and Tests

If more than one Python, use Python3 keyword to do the following commands:

```
python3 /path/to/calculate_slcsp.py
python3 -m discover unittest
```

If only Python 3:

```
python /path/to/calculate_slcsp.py
python -m discover unittest
```

#### Requirements

Python 3.6 

#### Assumptions

* Calculate the rate of a zip code's SLCSP, the benchmark plan
* Maintain the order of the slcsp.csv data
* Don't calculate zip code rates if zip code is in 1+ rate areas, leave blank

#### Python Entities 

* SLCSP - is a type of healthcare plan. It is the 'benchmark' for a rate area measured by having the 2nd lowest rate in the area.

* A plan has:
  - Coverage ('metal') level - Bronze to Catastrophic
  - Rate (premium cost / month)
  - Rate area 

* A rate area, represented as a tuple e.g. (IL, 14)  has:
  - State 
  - Number

#### Data Sources

* slcsp.csv
  - Headers: zip_code, rate_of_slcsp
* plans.csv
  - All US health plans
* zips.csv
  - Zip codes in more than one county
  - May not be able to identify county via rate area
  - May be able to associate a rate area for a zip code


