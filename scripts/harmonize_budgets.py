import glob 
import pandas as pd
import sqlite3 

files = sorted(glob.glob(f"../raw/*.xlsx"))


def clean_columns(df:pd.DataFrame)->pd.DataFrame:
    df = df.convert_dtypes()
    lowercase = { 
        c: c.lower().strip().replace(' ', '_') 
        for c in df.columns }
    df = df.rename(columns=lowercase)
    return df


def rename_bb_columns(df:pd.DataFrame, fiscal_year:int)->pd.DataFrame:
    prior = str(fiscal_year - 1)
    prior_columns = {c: c.replace(f'fy{prior}', 'prior_year') for c in df.columns if f'fy{prior}' in c}
    fiscal_year_columns = {c: c.replace(f'fy{fiscal_year}', 'fiscal_year') for c in df.columns if f'fy{fiscal_year}' in c}
    df = (
        df.rename(columns = prior_columns)
          .rename(columns = fiscal_year_columns)
    )
    if 'same' in df.columns:
      df = df.rename(columns = {"same": "account"})
    return df
  
# Pulls out an index of ids that are constant but refer to a label that 
# varies over time (e.g. dept names), and sets the most recent label as active
# This allows for consistent labels but preserves the historical data
def get_reference_table(df:pd.DataFrame, id:str, label:str, index:str)->pd.DataFrame:
    
    latest_values = (
        df[[id, label, index]]
            .drop_duplicates()
            .groupby(id)
            [index].agg('max')
            .reset_index()
            .assign(current_label = 1)
    )
    
    ref = (
        df[[id, label, index]]
            .drop_duplicates()
            .merge(latest_values, how='left', on=[id, index])
            .assign(current_label = lambda df: df.current_label.fillna(0))
    )
    
    return ref


# Read, reshape, and unify the budget book files
frames = {}
combined_budgets = pd.DataFrame()
for f in files:
    fiscal_year = f[-7:-5]
    print(fiscal_year)
    frames[fiscal_year] = (
        pd.read_excel(f)
            .pipe(clean_columns)
            .pipe(rename_bb_columns, int(fiscal_year))
            .assign(fiscal_year = f"FY{fiscal_year}")
    )
    combined_budgets = combined_budgets.append(frames[fiscal_year])
    

# Create a sqlite db 
conn = sqlite3.connect('../exports/budgets.db')
cursor = conn.cursor()

cb = combined_budgets

units = get_reference_table(cb, 'unit', 'unit_name', 'fiscal_year')
units.to_sql("units", conn)

fund_grants = get_reference_table(cb, 'fund_grant', 'fund_grant_name', 'fiscal_year')
fund_grants.to_sql("fund_grants", conn)

programs = get_reference_table(cb, 'program', 'program_name', 'fiscal_year')
programs.to_sql("programs", conn)

accounts = get_reference_table(cb, 'account', 'account_name', 'fiscal_year')
accounts.to_sql("accounts", conn)

cb = cb[[c for c in cb.columns if '_name' not in c]]
cb.to_sql("budgets", conn)

sql = """
    CREATE VIEW  
        budget_view 
    AS SELECT 
        b.*,
        u.unit_name,
        fg.fund_grant_name,
        p.program_name,
        a.account_name
    FROM 
        budgets b
    LEFT JOIN 
        fund_grants fg 
    ON 
        fg.fund_grant = b.fund_grant
        AND fg.current_label = 1
    LEFT JOIN 
        programs p
    ON 
        p.program = b.program
        AND p.current_label = 1
    LEFT JOIN 
        accounts a 
    ON 
        a.account = b.account
        AND a.current_label = 1
    LEFT JOIN 
        units u
    ON 
        u.unit = b.unit
        AND u.current_label = 1
    ;
"""
cursor.execute(sql)
conn.commit()

conn.close()
