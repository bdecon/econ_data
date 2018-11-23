### BD Economics Current Population Survey Extract

Updated: October 16, 2018

Brian Dew, @bd_econ

-----

**UPDATE: v0.1 released.** Currently, the project includes three jupyter notebooks for working with monthly Current Population Survey public use microdata files. The microdata files can be downloaded from the [US Census Bureau's CPS FTP page](https://thedataweb.rm.census.gov/ftp/cps_ftp.html). 

The three notebooks are:

1) bd_CPS_dd.ipynb which reads settings from bd_CPS_details.py and creates a python dictionary with information needed to read the raw CPS microdata files in the next step, and adjust them to be more time consistent and useful. 

2) bd_CPS_reader.ipynb which reads the raw monthy CPS microdata files downloaded from Census and converts them into annual feather format files that can be read by python or R. The feather formet is particularly fast when the data are mostly integers or categorical, as in this case. 

3) bd_CPS_grapher.ipynb which creates line plots from the CPS feather file data and query strings. This program allows a user to make use of the CPS in a powerful way, by querying the (currently 1994-) dataset, applying calculations, and visualizing the results. 

A bunch of settings and other required code is also contained in the python file bd_CPS_details.py.

##### How to run/ update

Sometime in the middle of each month, the Census Bureau will release the previous month's CPS microdata in a compressed file on the [US CPS FTP page](https://thedataweb.rm.census.gov/ftp/cps_ftp.html). The full set of 1994 onward monthly microdata files are available to download here. A local folder should contain the unzipped CPS microdata files for each year to be converted to the bd CPS. Next, the data dictionary files that correspond to each microdata file should be downloaded and stored in the same folder as the microdata. Separately, to adjust wages for inflation the CPI for each of four US regions should be downloaded using the notebook `bd_CPS_cpi.ipynb`. 

The first step in generating the bd CPS is to run the data dictionary generator, which creates a pickled python dictionary that provides information needed for reading the raw monthly CPS microdata files. This is done by running the notebook called `bd_CPS_dd.ipynb`. 

The next step is to run the notebook called `bd_CPS_reader.ipynb`. This will create a feather file called `cpsYYYY.ft` for each year included in the command in the `bd_CPS_reader` notebook. The feather file can be read into pandas as a dataframe, and, as I understand but have not tested, can be read into R and other statistical software programs. The file contains a subset of variables that are most commonly used for research. 

##### bd CPS variables

The bd CPS contains several variables that are recodes of other CPS variables or combinations of CPS data and outside data. The two most important examples of this are the Labor Market Status (LMSTAT) and the real wage variables (RHRWAGE and RWKWAGE). 

Details on bd CPS variables are as follows:

* LMSTAT - Labor market status - Classifies all age 16+ observations into one of 12 labor market statuses. See bd_CPS_reader.ipynb for mapping.
* RHRWAGE - Real hourly wage - Available in ORG quartersample, this converts weekly pay to hourly where possible and then adjusts the wage using the not-seasonally-adjusted regional CPI (Northeast, Midwest, South, West). 
* RWKWAGE - Real weekly wage - Same as above, except the weekly pay (therefore factoring in hours worked).
* INDGRP - Industry group of first job - Consistent industry groups for first job: Construction and mining (also includes agriculture and the like), Manufacturing, Trade, transportation, and utilties, Finance and business services (also includes Information and the like), Leisure and hospitality, and Public administration. See bd_CPS_reader.ipynb for mapping. 
* UNEMPTYPE - type of unemployment: job loser, job leaver, new entrant, or re-entrant. 
* UNEMPDUR - duration of unemployment, in weeks.
* VETERAN - binary variable equal to 1 if served active duty armed forces.
* CERT - has a professional certification. 
* STATE - converstion of state FIPS code to two letter state abbreviation.
* EDUC - Highest level of education obtained - Maps the educational categories to five groups: Less than high school, High school, Some college, Bachelor degree, Advanced degree.
* WBHAO - race/ethnic group - Each observation is mapped to one of five racial/ethnic groups: White, Black, Hispanic, Asian, and Other. White is white non-Hispanic only, black is any black non-Hispanic, Asian is any Asian but not black and non-Hispanic, Other is Native American, Native Hawaiian, Pacific Islander, and other groups. Hispanic is someone of Hispanic ethncity of any race. 
* MARRIED - binary variable equal to 1 if married and otherwise 0.
* FORBORN - binary variable equal to 1 if born outside the US and otherwise 0.
* EMP - binary variable equal to 1 if employed and otherwise 0.

##### Long term road map 

A crude long-term road map includes the following: refactoring for speed, much expanded graphing capabilities, flexibility in aggregation types/periods, Panel storage of multiple records from same household, CPS matching of observations, CPS flow calculations, including the CPS ASEC, including the CPS supplements, going back to at least 1989, and more. 

##### Contact me

I would really appreciate feedback. I also welcome opportunities to work with people on projects that might make use of these notebooks. You can email me at brianwdew@gmail.com.
