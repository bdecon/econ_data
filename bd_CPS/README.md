# bd CPS
## BD Economics Current Population Survey Extract

v0.4.1, updated: May 6, 2021

Working with Current Population Survey (CPS) public use microdata using jupyter notebooks and python.

Brian Dew, twitter: @bd_econ, email: brian.w.dew@gmail.com

### Contents
- [Example](#example)
- [Overview](#overview)
- [How to run/ update](#directions)
- [How to add a variable](#directions2)
- [bd CPS variables](#variables)
- [Long-term roadmap](#roadmap)
- [Acknowledgements](#acknowledgements)
- [Contact me](#contact)
- [List of CPS related links](#links)
- [Project dependencies](#dependencies)

-----

<a name="example"/>

### Example

Input (after running programs on raw data downloaded from Census):

```
import pandas as pd

df = (pd.read_feather('cps2017.ft')
        .query('MONTH == 10 and 25 <= AGE <= 54')
        .groupby('EDUC')
        .PWSSWGT
        .sum())
```

Output:

```
EDUC

ADV     16551343.0
COLL    30948892.0
HS      33313412.0
LTHS    11389192.0
SC      33637956.0

Name: PWSSWGT, dtype: float32
```

The above arbitrary example calculates how many age 25-54 people are in each of five educational categories in October 2017. It shows, for example, that about 16.6 million have advanced degrees.

<a name="overview"/>

### Overview

**UPDATE: v0.4.1 released.** The bd CPS is a series of jupyter notebooks I wrote to work with monthly Current Population Survey public use microdata. If the notebooks, or any part of them, could be helpful to you, please feel free to use them or modify them in any way. When set up correctly, the notebooks generate annual [feather](https://github.com/wesm/feather) files, for the years from 1989-present, which contain cleaned-up partial extracts of basic monthly CPS data. The raw source microdata files and data dictionaries can be downloaded from the [US Census Bureau's CPS page](https://www.census.gov/data/datasets/time-series/demo/cps/cps-basic.html). 

The bd CPS notebooks include:

1) `bd_CPS_dd.ipynb` reads settings from bd_CPS_details.py and creates a python dictionary with information needed to read the raw CPS microdata files in the next step, and adjust them to be more time-consistent and useful. The program requires downloading the CPS data dictionary text files from the Census CPS page. 

2) `bd_CPS_reader.ipynb` reads the raw monthy CPS microdata files downloaded from Census and converts them into annual feather format files that can be read by python or R. The feather format is particularly fast when the data are mostly integers or categorical, as in this case. Works for years 1994-onward.

3) `bd_CPS_1989-93.ipynb` creates partial extracts for 1989-93. It is a work in progress, but creates many variables that are consistent with those in the 1994-onward extracts.

Settings and other required code are also contained in the python file bd_CPS_details.py. There is additionally a notebook that downloads regional consumer price index data from BLS (used as the price deflator for real wage series), as well as a separate notebook that generates a unique (over time) household ID for CPS households from mid-1995 onward. Lastly, the bd CPS incorporates several supplements and revisions to the basic monthly CPS.

<a name="directions"/>

### How to run/ update

The Wednesday following the release of the jobs report, the Census Bureau will release the related previous-month CPS public use microdata in a compressed file on the [Basic Monthly CPS page](https://www.census.gov/data/datasets/time-series/demo/cps/cps-basic.html). The full set of 1994 onward monthly microdata files are available to download on the Census CPS page. NBER [hosts](https://www.nber.org/data/cps_basic.html) the 1989 to 1993 files. For the bd CPS program to work, a local folder must contain the relevant uncompressed CPS microdata files. Next, the data dictionary files that correspond to each microdata file should be downloaded and stored in the same folder as the microdata. Separately, to adjust wages for inflation the CPI for each of four US regions should be downloaded using the notebook `bd_CPS_cpi.ipynb` (requires a [free BLS API key](https://data.bls.gov/registrationEngine/)). Version 0.4 of the bd CPS can also generate a unique CPSID for all households, by running `bd_CPS_id.ipynb`.

The first step in generating the bd CPS is to run the data dictionary generator, which creates a pickled python dictionary that provides information needed for reading the raw monthly CPS microdata files. This is done by running the notebook called `bd_CPS_dd.ipynb`. To run the bd CPS for 2000, 2001, and 2002, which utilize revised 2000-based weights and revised union data, or for December 2007, which uses revised weights, or for 2015-16, which uses separate data to identify persons with professional certifications, or for May 2020 onward, which include the COVID-19 supplemental questions, you'll also need to download and unzip the related source files and run `bd_CPS_revisions_reader.ipynb`.

The next step is to run the notebook called `bd_CPS_reader.ipynb`. This will create a feather file called `cpsYYYY.ft` for each year included in the command in the `bd_CPS_reader` notebook. The feather file can be read into pandas as a dataframe, and, as I understand but have not tested, can be read into R and other statistical software programs. The file contains a subset of variables that are most commonly used for research. 

<a name="directions2"/>

### How to add a variable

To include an additional CPS variable in your local version of the bd CPS extract, add the variable name (from the Census data dictionary) to the list of variables names in `VarList` in `bd_CPS_details.py` and re-run `bd_CPS_dd.ipynb` and `bd_CPS_reader.ipynb`.

<a name="variables"/>

### bd CPS variables

The bd CPS contains several variables that are recodes of other CPS variables or combinations of CPS data and outside data. The two most important examples of this are the labor force status (`LFS`) and the real wage variables (`RHRWAGE` and `RWKWAGE`). 

The bd CPS includes a [codebook](https://github.com/bdecon/econ_data/blob/master/bd_CPS/codebook.txt) that shows which variables are available for which dates, and what values the variables include. 

Details on selected bd CPS variables are as follows:

* `LFS` - Labor force status - Employed, Unemployed, or Not in Labor Force (NILF).
* `COW1` - Class of worker on first job: Federal Government, State Government, Local Government, Private, Self-employed Incorporated, Self-employed Unincorporated, Without Pay. 
* `NILFREASON` - Reason for non-participation in the labor market: Discouraged, Disabled/Ill, Family, Retired, In School, Other (currently available 1994-onward only).
* `HRWAGE` - Hourly wage - Available in ORG quartersample. 
* `WKEARN` - Usual weekly earnings - Same as above, except the usual weekly pay (therefore factoring in hours worked).
* `WKEARNADJ` - Usual weekly earnings with topcode replaced with estimated mean above topcode. 
* `HRWAGEADJ` - Hourly wage but also includes wages based on imputed hours for observations where usual weekly hours vary and uses WKEARNADJ.
* `MINWAGE` - equal to 1 if worker is paid the federal minimum wage or less. 
* `PAIDHRLY` - equal to 1 if paid hourly and 0 if person has earnings but is not paid hourly.
* `INDGRP` - Industry group of first job - Consistent industry groups for first job: Construction and mining (also includes agriculture and the like), Manufacturing, Trade, transportation, and utilties, Finance and business services (also includes Information and the like), Leisure and hospitality, and Public administration. See bd_CPS_reader.ipynb for mapping. 
* `INDM` - Major industry group on fisrst job. More groups than INDGRP. 
* `UNEMPTYPE` - type of unemployment: job loser, job leaver, new entrant, or re-entrant. 
* `UNEMPDUR` - duration of unemployment, in weeks. Slight definition change in 1994 revamp.
* `VETERAN` - binary variable equal to 1 if served active duty armed forces.
* `UNION` - equal to 1 if a union member or covered by a union contract.
* `UNIONMEM` - equal to 1 if a union member.
* `CERT` - has a professional certification (available 2015-onward).
* `STATE` - conversion of state FIPS code to two letter state abbreviation.
* `REGION` - Census region (Northeast, South, Midwest, West)
* `CBSA` - center-based statistical area (where identified).
* `CSA` - consolidated statistical area (where identified).
* `EDUC` - Highest level of education obtained - Maps the educational categories to five groups: Less than high school, High school, Some college, Bachelor degree, Advanced degree.
* `EDUCDT` - Detailed highest level of education attained.
* `WBHAO` - race/ethnic group - Each observation is mapped to one of five racial/ethnic groups: White, Black, Hispanic, Asian, and Other. White is white non-Hispanic only, black is any black non-Hispanic, Asian is any Asian but not black and non-Hispanic, Other is Native American, Native Hawaiian, Pacific Islander, and other groups. Hispanic is someone of Hispanic ethnicity of any race. 
* `WBHAOM` - race/ethnic group - white, non-Hispanic only, black, non-Hispanic only, Asian or Pacific Islander, non-Hispanic only, Native American, non-Hispanic only, persons of more than one racial group but non-Hispanic, and Hispanic, and race/ethnicity. Available 2003 onward, only.
* `MARRIED` - binary variable equal to 1 if married and otherwise 0.
* `FORBORN` - binary variable equal to 1 if born outside the US and otherwise 0.
* `CTYBIRTH` - country of birth.
* `SCHENR` - binary variable equal to 1 if enrolled in high school, college, or university and otherwise 0. 
* `PTECON` - binary variable equal to 1 if usually part-time for economic reasons and otherwise 0.
* `WORKFT` - equal to one if person worked full time during the reference week (35 hours or more) regardless of whether they usually work full-time.
* `ABSTYPE` - reason person is not at work or working part time during the reference week.
* `PRNMCHLD` - number of own children under age 18 (available November 1999-onward).
* `DISABILITY` - binary equal to one if person has any of six disabilities (available June 2008 onward).
* `CPSID` - unique (over time, in bd CPS) household ID  (available 1998-onward; OPTIONAL - run the reader, run `bd_CPS_id` and then re-run the reader, to add the `CPSID`).
* `BASICWGT` - weight equal to `PWSSWGT` before 1998 and `PWCMPWGT` after. The weight variables use the 2000-based revised weights for the years 2000-2002 and the December 2007 revised weights.

<a name="roadmap"/>

### Long-term road map 

The following items are included in the proposed version 1.0: Cleaned-up industry, occupation, and geography codes, complete coverage for CPSID, new CPSIDP for persons within households, new longitudinal weights, and CPI data without an API key. I'd love help, comments, or suggestions. See [active issues](https://github.com/bdecon/econ_data/issues) on the project's github repo.

Separately, if someone is willing to fund some server space, I would *really* like to put the actual bd_CPS data online. This would make it possible for people to easily use the fruits of my labor, which, I think, make CPS analysis much easier for people who like python and R instead of Stata. Please contact me if you want to chip in for this (brian.w.dew@gmail.com).

<a name="acknowledgements"/>

### Acknowlegements

Many many thanks to John Schmitt for countless hours of kind and patient guidance. Many thanks to the staff and management of CEPR for giving me the chance to learn about the CPS. Thanks to EPI, and Ben Zipperer in particular, for providing very helpful documentation. Thanks to NBER, FRBATL, FRBKC, IPUMS, Urban Institute, Tom Augspurger, and staff of BLS and Census, for making analysis of the CPS easier by putting helpful information online. The bd CPS is basically just translating a lot of other people's work into python code.

<a name="contact"/>

### Contact me

I would really appreciate feedback, especially if you spot an error. I also welcome opportunities to work with people on projects that might make use of these notebooks, and would be most grateful for any help in making the project better! Feel free to email me at brian.w.dew@gmail.com.


<a name="links"/>

### List of CPS related links

[BLS regional CPI](https://www.bls.gov/cpi/regional-resources.htm)

[CEPR data CPS extracts](http://ceprdata.org/cps-uniform-data-extracts/)

[FRBATL Labor Market Status Categorization](https://www.frbatlanta.org/chcs/human-capital-currents/2015/0612-measuring-labor-market-status-using-basic-data.aspx)

[FRBKC CPS resources](https://www.kansascityfed.org/research/kcdc/cps)

[FRBKC Psuedocode](https://www.kansascityfed.org/research/kcdc/cps/coreinfo/pseudocode/hrswk)

[US Census Bureau's Basic Monthly CPS page](https://www.census.gov/data/datasets/time-series/demo/cps/cps-basic.html)

[NBER CPS Basic Data](http://www.nber.org/data/cps_basic.html)

[NBER CPS Supplements](https://www.nber.org/data/current-population-survey-data.html)

Tom Augspurger CPS in Python examples:

[Part 1: Using Python to tackle the CPS](http://tomaugspurger.github.io/tackling%20the%20cps.html)

[Part 2: Using Python to tackle the CPS](http://tomaugspurger.github.io/tackling%20the%20cps%20%28part%202%29.html)

[Part 3: Using Python to tackle the CPS](http://tomaugspurger.github.io/tackling%20the%20cps%20%28part%203%29.html)

[Part 4: Using Python to tackle the CPS](http://tomaugspurger.github.io/tackling%20the%20cps%20%28part%204%29.html)

------

<a name="dependencies"/>

### Project dependencies

In addition to the files in this repo, to run the bd_CPS notebook, you will need:

- CPS microdata files from Census for 1994-present and from NBER (renamed slightly) for 1989-93;

- Data dictionary files from Census for 1994-present and from NBER for 1989-93;

- Revised data from Census for 2000-based weights, and corrected union data (2000-2003);

- Revised data from Census for revised December 2007 weights;

- Additional data from Census for 2015-16 professional certification variables;

- Additional data on COVID-19, covering May 2020 onward;

- BLS API code (to retrieve CPI data, free but requires registration);

- Python 3.7 installation (I recommend miniconda);

- pandas 0.24 or later;

- numpy 1.12 or later;

- jupyter;

- feather-format; and

- requests package to access BLS API

