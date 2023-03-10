import pandas as pd
from typing import Callable, Any
from functools import wraps
    
def df_composable(func) -> Callable[[pd.DataFrame], Any]:
    """Decorate a functions to create a function that takes a df as an argument."""
    @wraps(func)
    def df_composed(*args, **kwargs):
        @wraps(func)
        def internal(df): 
            return func(df, *args, **kwargs)
        return internal
    return df_composed

def col_strip(df, string,  columns=None) -> pd.DataFrame:
    """Strip string from column names."""
    if columns is None:
        columns = df.columns
    return df.rename(columns={col: col.strip(string) for col in columns})

def col_replace(df, old, new, columns=None, count=-1):
    """Replace old in column names with new."""
    if columns is None:
        columns = df.columns
    return df.rename(columns={col: col.replace(old, new, count) for col in columns})

def col_truncate(df, stop, start=0, columns=None):
    """Truncate column names by slicing strings."""
    if columns is None:
        columns = df.columns
    return df.rename(columns={col: col[start:stop] for col in columns})

def col_lambda_clean(df, map_fn, filter_fn=None, columns=None):
    """Clean column names with functions."""
    if filter_fn is not None:
        #print(df)
        columns = [col for col in df.columns if filter_fn(col)]
    elif columns is None:
        columns = df.columns
    return df.rename(columns={col: map_fn(col)  for col in columns})

def add_col(df, col, value):
    """Add column to DataFrame."""
    df = df.copy()
    df[col] = value
    return df

def reorder_cols(df, left: list, right: list):
    """Reorder DataFrame columns.

    The columns will be those in left, any in neither left nor right, and then right.

    Parameters
    ----------
    left:
        The columns to appear on the left.
    right:
        The columns to appear on the right.

    """
    df = df.copy()
    other = [col for col in df.columns if col not in left + right]
    return df[left + other + right]

def test_col_cleaners():
    df = pd.DataFrame({'abc': [1], 'xyz': [2]})
    assert 'xy' in col_strip(df, 'z').columns 
    assert 'def' in col_replace(df, 'abc', 'def')
    assert 'ab' in col_truncate(df, 2)
    assert 'cba' in col_lambda_clean(df, lambda x: ''.join(reversed(x)))

def test_reorder_cols():
    df = pd.DataFrame({'abc': [1], 'xyz': [2]})
    assert reorder_cols(df, ['xyz'], []).columns.to_list() == ['xyz', 'abc']

if __name__ == '__main__':
    test_col_cleaners()
    test_reorder_cols()