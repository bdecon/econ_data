### BD Economics Current Population Survey Extract

Updated: October 13, 2018

Brian Dew, @bd_econ

-----

**The bd CPS is a work in progress.** Currently, the project includes three jupyter notebooks for working with monthly Current Population Survey public use microdata files. The microdata files can be downloaded from the [US Census Bureau's CPS FTP page](https://thedataweb.rm.census.gov/ftp/cps_ftp.html). 

The three notebooks are:

1) bd_CPS_dd.ipynb which reads settings from bd_CPS_details.py and creates a python dictionary with information needed to read the raw CPS microdata files in the next step, and adjust them to be more time consistent and useful. 

2) bd_CPS_reader.ipynb which reads the raw monthy CPS microdata files downloaded from Census and converts them into annual feather format files that can be read by python or R. The feather formet is particularly fast when the data are mostly integers or categorical, as in this case. 

3) bd_CPS_grapher.ipynb which creates line plots from the CPS feather file data and query strings. This program allows a user to make use of the CPS in a powerful way, by querying the (currently 1994-) dataset, applying calculations, and visualizing the results. 

##### Contact me

I would really appreciate feedback. I also welcome opportunities to work with people on projects that might make use of these notebooks. You can email me at brianwdew@gmail.com.
