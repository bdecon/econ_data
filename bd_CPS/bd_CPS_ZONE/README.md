# ZONE: CPS Geographic Zones

ZONE is a geographic variable for the Current Population Survey (CPS) that divides the United States into 70 zones. It provides subnational granularity for economic, demographic, and policy analysis while maintaining complete coverage and adequate sample sizes. Available from September 1995 to the present.

## Design Goals

ZONE balances three objectives:

1. **Coverage**: Every CPS observation is assigned to a zone (0% missing rate)
2. **Statistical significance**: Zones maintain sufficient sample sizes (~4,000+ observations ages 25-54) for meaningful analysis
3. **Economic significance**: Zones reflect distinct labor market characteristics, carving out major metros where education and industry composition differ substantially from surrounding areas

## Variables

| Variable | Description | Values |
|----------|-------------|--------|
| `ZONE` | Geographic zone | 70 categories (e.g., CHICAGO_METRO, OH, CA_BALANCE) |
| `ZONEERA` | OMB delineation era | ERA1, ERA2, ERA3, ERA4 |

## Zone Types

ZONE comprises four types of geographic areas:

| Type | Count | Description | Examples |
|------|-------|-------------|----------|
| Metro | 25 | Large CBSAs carved out as distinct zones | CHICAGO_METRO, LA_METRO, BOSTON_METRO |
| Standalone State | 25 | Entire state forms one zone (no carve-outs) | OH, TN, NV |
| State Balance | 16 | State remainder after metro carve-outs | CA_BALANCE, TX_BALANCE, NY_BALANCE |
| Combined Region | 4 | Multi-state remainders combined | MOUNTAIN_BALANCE, MO_IL_BALANCE |

**Total: 70 zones**

### Metro Zones (25)

Major metropolitan areas carved out based on CBSA codes. These areas have distinct labor market characteristics (typically 10+ percentage point higher college attainment) compared to their state remainders.

| Zone | Metropolitan Area |
|------|-------------------|
| NYC_CITY | New York City (5 boroughs) |
| NY_METRO | New York suburbs (Nassau, Suffolk, Westchester, etc.) |
| LA_METRO | Los Angeles-Long Beach-Anaheim |
| CHICAGO_METRO | Chicago-Naperville-Elgin |
| DALLAS_METRO | Dallas-Fort Worth-Arlington |
| HOUSTON_METRO | Houston-The Woodlands-Sugar Land |
| DC_METRO | Washington-Arlington-Alexandria |
| PHILLY_METRO | Philadelphia-Camden-Wilmington |
| MIAMI_METRO | Miami-Fort Lauderdale-Pompano Beach |
| ATLANTA_METRO | Atlanta-Sandy Springs-Alpharetta |
| BOSTON_METRO | Boston-Cambridge-Newton |
| BAYAREA_METRO | San Francisco-Oakland + San Jose-Sunnyvale |
| PHOENIX_METRO | Phoenix-Mesa-Chandler |
| RIVERSIDE_METRO | Riverside-San Bernardino-Ontario |
| SEATTLE_METRO | Seattle-Tacoma-Bellevue |
| MINNEAPOLIS_METRO | Minneapolis-St. Paul-Bloomington |
| SANDIEGO_METRO | San Diego-Chula Vista-Carlsbad |
| TAMPA_METRO | Tampa-St. Petersburg-Clearwater |
| DENVER_METRO | Denver-Aurora-Lakewood |
| ORLANDO_METRO | Orlando-Kissimmee-Sanford |
| STLOUIS_METRO | St. Louis |
| DETROIT_METRO | Detroit-Warren-Dearborn |
| PORTLAND_METRO | Portland-Vancouver-Hillsboro |
| KANSASCITY_METRO | Kansas City |
| ALBUQUERQUE_METRO | Albuquerque |

**NYC Split**: New York City is split into NYC_CITY (5 boroughs) and NY_METRO (NY suburbs) because of their distinct characteristics. The NJ portion of the NYC metropolitan area falls to NJ_BALANCE.

**Orlando**: Carved out despite a smaller sample size due to Florida's large population and Orlando's distinct tourism-driven economy.

### Standalone States (25)

These states have no metro carve-outs. The entire state forms a single zone.

AL, AK, AR, CT, HI, IA, ID, KY, LA, MS, MT, NC, ND, NE, NV, OH, OK, RI, SC, SD, TN, UT, VT, WV, WY

### State Balance Zones (16)

State remainders after metro areas are carved out.

CA_BALANCE, CO_BALANCE, FL_BALANCE, GA_BALANCE, IN_BALANCE, KS_BALANCE, MA_BALANCE, MI_BALANCE, MN_BALANCE, NJ_BALANCE, NY_BALANCE, OR_BALANCE, PA_BALANCE, TX_BALANCE, VA_BALANCE, WA_BALANCE, WI_BALANCE

### Combined Region Zones (4)

Multi-state remainders combined to achieve sufficient sample sizes.

| Zone | States | Description |
|------|--------|-------------|
| NH_ME | NH, ME | Northern New England |
| MOUNTAIN_BALANCE | AZ, CO, NM | Mountain region remainder (after Phoenix, Denver, Albuquerque) |
| MO_IL_BALANCE | MO, IL | MO/IL remainder (after Kansas City, St. Louis, Chicago) |
| MD_DE_BALANCE | MD, DE | MD/DE remainder (after DC metro, Philadelphia) |

## Eras

ZONE boundaries depend on OMB metropolitan area delineations, which change over time. ZONEERA identifies which delineation applies to each observation.

| Era | Date Range | OMB Version | Notes |
|-----|------------|-------------|-------|
| ERA1 | Sep 1995 - Apr 2004 | 1999 OMB (MSA/PMSA codes) | Pre-CBSA era |
| ERA2 | May 2004 - Jul 2015 | 2003 OMB (CBSA codes) | |
| ERA3 | May 2014 - Jul 2026 | 2013 OMB (CBSA codes) | Overlaps ERA2 |
| ERA4 | May 2025 - Present | 2020 OMB (CBSA codes) | Overlaps ERA3 |

### Era Transitions and Overlapping Dates

Era date ranges overlap because CPS phases in new geographic definitions gradually through its rotation panel design. During transitions, different respondents in the same month may have different ZONEERA values based on their Month-in-Sample (MIS) rotation group.

- **ERA1 to ERA2** (May 2004): Hard cutover when CPS switched from MSA to CBSA codes
- **ERA2 to ERA3** (May 2014 - Jul 2015): 16-month phase-in via MIS rotation
- **ERA3 to ERA4** (May 2025 - Jul 2026): 16-month phase-in via MIS rotation

For analysis requiring consistent boundaries, filter to a single ZONEERA value or use months outside the transition periods.

### Sample Size Shifts at Era Boundaries

CPS sample redesigns coincide with era transitions and can substantially change sample sizes by zone, independent of any ZONE methodology changes. For example, the 2014 redesign (ERA2→ERA3) reduced Minnesota's representation by ~45% while increasing Louisiana's by ~50%, even though total CPS sample size remained stable. These shifts reflect updated sampling frames based on new Census data, not changes in ZONE definitions.

## Data Availability

- **Start date**: September 1995
- **Missing rate**: 0% (all observations assigned)
- **Pre-September 1995**: ZONE and ZONEERA are not available (geographic codes were suppressed June-August 1995 during CPS sample redesign)

## Shapefiles

Zone boundary shapefiles are available for each era:

| File | Era |
|------|-----|
| `zone_era1_1995_2004.shp` | ERA1 |
| `zone_era2_2004_2015.shp` | ERA2 |
| `zone_era3_2015_2026.shp` | ERA3 |
| `zone_era4_2026_plus.shp` | ERA4 |

## Maps

![ERA3 Zone Map](visualizations/zone_era3_detail.png)

Detailed maps for each era are in the `visualizations/` folder.
