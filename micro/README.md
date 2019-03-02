# micro

------

## BD Economics microdata examples

------

Updated: March 2, 2019

Contact: Brian Dew, twitter: @bd_econ; email: brian.w.dew@gmail.com

Goal: Working with public-use microdata using jupyter notebooks and python.

Some examples use the [bd CPS](https://github.com/bdecon/econ_data/tree/master/bd_CPS), a set of annual CPS extracts. 

------

### Contents

- [CPS-ASEC_median_income.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS-ASEC_median_income.ipynb): Replicates (closely) the published median wage estimate from the Annual Social and Economic Supplement to the Current Population Survey. 

- [CPS_Disability_NILF_CBSA.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS_Disability_NILF_CBSA.ipynb): Generates a map showing share of age 16-64 population that is out of work due to disability, for each metro area in the US. Uses raw Current Population Survey monthly data.

- [CPS_EPOP_P10wage_CBSA.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS_EPOP_P10wage_CBSA.ipynb): Generates a scatter plot showing the relationship between the employed share of the population and the first decile real hourly wage for each metro area. Uses bd CPS as the source

- [CPS_Example_Notebook_UPDATED.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS_Example_Notebook_UPDATED.ipynb): Example of using the struct method to read a fixed-width format monthly Current Population Survey data file. 

- [CPS_Matching_Flow_Disabled_to_Work.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS_Matching_Flow_Disabled_to_Work.ipynb): Example of matching one-year apart bd CPS observations to measure the employed share of age 25-54 people who were not working the year before due to disability or illness. 

- [CPS_NILF.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS_NILF.ipynb): Create line chart showing contributions to labor force participation rate since March 2001. Uses bd CPS data.

- [CPS_PECERT_Mapper.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/CPS_PECERT_Mapper.ipynb): Create a choropleth map of the US showing what percent of each state's population has a professional certification. Uses bd CPS as data source

- [bd_CPS_benchmark.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/bd_CPS_benchmark.ipynb): Several examples of benchmarking bd CPS results to published estimates. Used to check validity of bd CPS extract. 

- [bd_CPS_flow_MM.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/bd_CPS_flow_MM.ipynb): Create line chart showing what percent of newly employed people were not in the labor force last month. Uses month-to-month matching of bd CPS data.

- [bd_CPS_flow_YY.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/bd_CPS_flow_YY.ipynb): Create a line share showing the share of unemployed people with a job one year later. Uses one-year apart matching of bd CPS data.

- [bd_CPS_grapher.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/bd_CPS_grapher.ipynb): Tool for graphing common labor economics statistics from bd CPS data. For example, the unemployment rate, union membership rate, share part-time for economic reasons, share retired, etc.

- [bd_CPS_grapher_two_lines.ipynb](https://github.com/bdecon/econ_data/blob/master/micro/bd_CPS_grapher_two_lines.ipynb): Draft version of bd_CPS_grapher.ipynb that can create more complex line charts from bd CPS data.

