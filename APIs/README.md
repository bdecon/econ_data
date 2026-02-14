# APIs

## Economic Data APIs with Python

*Updated: February 2026*

Contact: Brian Dew, [bd-econ.com](https://bd-econ.com); email: brian.w.dew@gmail.com

Examples of retrieving economic data from public APIs using Python. Each notebook demonstrates the request, data cleaning, and visualization workflow using `requests` and `pandas`.

An API key is required for some sources (stored locally in `config.py`).

------

### Contents

**U.S. Government**

- [Bureau of Economic Analysis (BEA)](https://github.com/bdecon/econ_data/blob/master/APIs/BEA.ipynb): National accounts — consumer spending, GDP by industry, gross output. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/BEA.ipynb)

- [Bureau of Labor Statistics (BLS)](https://github.com/bdecon/econ_data/blob/master/APIs/BLS.ipynb): Unemployment rates by race/ethnicity. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/BLS.ipynb). See also: [guide](https://github.com/bdecon/econ_data/blob/master/APIs/BLS_guide.ipynb) (no API key needed), [prices](https://github.com/bdecon/econ_data/blob/master/APIs/BLS_Prices.ipynb).

- [Census Bureau — ACS](https://github.com/bdecon/econ_data/blob/master/APIs/Census_ACS.ipynb): American Community Survey — county income choropleth and state work-from-home rates (2023). [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/Census_ACS.ipynb)

- [Census Bureau — M3](https://github.com/bdecon/econ_data/blob/master/APIs/Census_TimeSeries_M3.ipynb): Manufacturers' new orders for nondefense capital goods. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/Census_TimeSeries_M3.ipynb)

- [Census Bureau — Trade](https://github.com/bdecon/econ_data/blob/master/APIs/Census_Trade.ipynb): U.S. exports by partner country. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/Census_Trade.ipynb)

- [Energy Information Administration (EIA)](https://github.com/bdecon/econ_data/blob/master/APIs/EIA.ipynb): U.S. crude oil production by region. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/EIA.ipynb)

- [FRED](https://github.com/bdecon/econ_data/blob/master/APIs/FRED.ipynb): Federal Reserve Bank of St. Louis — average hourly earnings by industry. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/FRED.ipynb)

- [Treasury](https://github.com/bdecon/econ_data/blob/master/APIs/Treasury.ipynb): Federal revenue by type from the Monthly Treasury Statement. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/Treasury.ipynb)

**International**

- [European Central Bank (ECB)](https://github.com/bdecon/econ_data/blob/master/APIs/ECB.ipynb): Government bond yields, exchange rates, and unemployment for Eurozone countries. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/ECB.ipynb)

- [International Labour Organization (ILO)](https://github.com/bdecon/econ_data/blob/master/APIs/ILO.ipynb): Unemployment rate by sex and age for Canada and G7 countries. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/ILO.ipynb)

- [International Monetary Fund (IMF)](https://github.com/bdecon/econ_data/blob/master/APIs/IMF.ipynb): CPI inflation and trade data via the SDMX API (uses `sdmx1` library). [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/IMF.ipynb)

- [Organization for Economic Cooperation and Development (OECD)](https://github.com/bdecon/econ_data/blob/master/APIs/OECD.ipynb): GDP per hour worked for Nordic countries and the US. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/OECD.ipynb). See also: [GDP growth](https://github.com/bdecon/econ_data/blob/master/APIs/OECD_Updated.ipynb).

- [UN ComTrade](https://github.com/bdecon/econ_data/blob/master/APIs/ComTrade.ipynb): Bilateral trade data by product — US exports/imports and a semiconductor trade network graph using HS 6-digit codes (public preview API, no key required). [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/ComTrade.ipynb)

- [World Bank](https://github.com/bdecon/econ_data/blob/master/APIs/World_Bank.ipynb): Foreign direct investment for Brazil and Chile. [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/World_Bank.ipynb)

**Other**

- [SEC EDGAR](https://github.com/bdecon/econ_data/blob/master/APIs/SEC_EDGAR.ipynb): Operating cash flow for the "Magnificent 7" from XBRL company facts (no API key required). [nbviewer](https://nbviewer.jupyter.org/github/bdecon/econ_data/blob/master/APIs/SEC_EDGAR.ipynb)
