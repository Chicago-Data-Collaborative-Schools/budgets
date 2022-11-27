# Harmonized budget from CPS Budget Books
This repo takes a collection of XLSX exports of the annual CPS Budget Books. Those files can be downloaded by going to the [CPS Budget page](https://www.cps.edu/about/finance/budget/), choosing "Interactive Reports" and then "Export Data."

- The script modifies the files, replacing references to specific years in the column names with "fiscal_year" and "previous_year"
- It also adds a fiscal year column
- The choice of included columns varies somewhat from year to year

## Labels and indexes
Some labeled values have been pulled out into a separate index (fund names, unit names, etc). The _id_ values are consistent over time, but the names vary slightly. Having a separate table preserves all actual used labels, but allows us to use the latest one across all years for consistency.

## Joining other data
- Join on finance_id in the school_ids db to then join other data by school_id
- Finance_id matches dept_id in the positions data



