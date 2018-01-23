clear all
set more off

/* Brian Dew, September 20, 2017
 Attempt to calculate for all years:
 1.) What share of workers are paid hourly; and
 2.) What share of workers receive overtime, tips, or commissions; and
 3.) Who are answering the survey as proxies */

cd "C:/Working/econ_data/micro/data/"

local keepit "year lfstat selfemp orgwgt paidhre otcrec proxy wholine reltoref otcamt"

use `keepit' using cepr_org_1979.dta, clear
forvalues y = 1980(1)2017 {
	qui append using "cepr_org_`y'.dta", keep(`keepit')
}

/* Round weights */
gen rndwgt = .
if year <= 2016 {
	replace rndwgt = round(orgwgt/12, 1)
}

if year == 2017 {
	replace rndwgt = round(orgwgt/9, 1)
}
gen proxy2 = 0

replace proxy2 = 1 if proxy == 2
table year reltoref [fw=rndwgt], c(n proxy2)

keep if lfstat==1
keep if selfemp==0
table year [fw=rndwgt], contents(mean paidhre mean otcrec mean otcamt) f(%9.4f)


**** METODO *****
* Proxy - Dummy variables?
* Stata table to csv/other portable output
