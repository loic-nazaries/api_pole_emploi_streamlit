"""Functions used for extracting data from Pole Emploi API.

TODO split the function 'def extract_search_content()'
into THREE different functions
"""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import sidetable as stb
import missingno as msno
import altair as alt
from datetime import date  # delete ?
import datetime


@st.cache
def start_search(api_client=None, params=None):
    # fix type hints for the content of the dict
    """Search the client's API.

    Args:
        params (dict, optional): _description_. Defaults to None.

    Returns:
        dict: _description_
    """
    basic_search = api_client.search(params)
    return basic_search


@st.cache
def extract_search_content(search_session):
    # fix type hints for the content of each dict
    """Prepare the search output from a basic search.

    The basic search corresponds to two lists and one dictionary, namely:
    - the `resultats`, which contains all the available data
    - the `filtresPossibles`, which is composed of 4 `filters` ('themes')
        -
        -
        -
        -
    - the `Content-Range`, which indicates the number of hits from  search

    Args:
        basic_search (dict): _description_

    Returns:
        list: _description_
        dict:
    """
    results = search_session["resultats"]
    filters = search_session["filtresPossibles"]
    content_range = search_session["Content-Range"]
    return results, filters, content_range


def display_max_content(content_range):
    # fix type hints for the content of the dict
    """Get the number of hits from the search.

    Args:
        content_range (dict): _description_

    Returns:
        str: _description_
    """
    content_max = content_range["max_results"]
    return content_max


def convert_search_results_to_dataframe(
    search_results
):
    """Convert the search content into a dataframe.

    Args:
        search_results (dict): _description_

    Returns:
        _type_: _description_
    """
    dataframe = pd.json_normalize(search_results)
    return dataframe


# @st.cache(allow_output_mutation=True)
def convert_df_to_html_table(
    dataframe,
    use_checkbox
):
    """_summary_.

    Args:
        dataframe (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    gridbuilder = GridOptionsBuilder.from_dataframe(dataframe)
    gridbuilder.configure_pagination(paginationPageSize=20)  # NOT working
    gridbuilder.configure_side_bar()
    gridbuilder.configure_selection(use_checkbox)
    gridbuilder.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc="sum",
        editable=True,
    )
    gridOptions = gridbuilder.build()
    html_table = AgGrid(
        dataframe,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
    )
    return html_table


def extract_search_categories(dataframe):
    """Extract a list of all columns/categories in the dataframe.

    Args:
        results_df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    category_list = pd.DataFrame(dataframe.columns)
    category_list.columns = ["Categories"]
    return category_list


def extract_linked_categories(
    dataframe,
    category_to_extract,
    new_fields
):
    """Extract of columns with multiple/mixed names.

    Also, drop the source category from the dataframe as it is now redundant.

    Args:
        dataframe (pd.DataFrame): _description_
        category_to_extract (str): _description_
        new_fields (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe[new_fields] = dataframe[category_to_extract].str.split(
        " - ", expand=True
    )
    dataframe = dataframe.drop(category_to_extract, axis=1)
    return dataframe


@st.cache(allow_output_mutation=True)
def flatten_category(
    dataframe,
    category
):
    """Extract the categories WITHIN the category.

    Args:
        dataframe (pd.DataFrame): _description_
        category (str): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe = dataframe[category].apply(pd.Series)
    # dataframe = dataframe.drop(category, axis=1)  # NOT working
    return dataframe


def rename_columns_auto(dataframe, column_name):
    """Rename automatically the categories previously extracted.

    Args:
        dataframe (pd.DataFrame): _description_
        column_name (str): _description_

    Returns:
        list: _description_
    """
    auto_renamed_columns = [
        f"{column_name} %d" % i for i in range(len(dataframe.columns))
    ]
    dataframe.columns = [auto_renamed_columns]
    return dataframe


def rename_category(
    dataframe,
    columns,
):
    """Rename specific category.

    Args:
        dataframe (pd.DataFrame): _description_
        columns (dict): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe.rename(columns=columns, inplace=True)
    return dataframe


def concatenate_dataframes(column_list):
    """Concatenate a list of dataframes.

    Args:
        column_list (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe = pd.concat(column_list, axis=1)
    return dataframe


def merge_dataframes(
    input_dataframe_1,
    input_dataframe_2,
    on,
    how="left",
):
    """Merge two dataframes based on a column.

    Args:
        input_dataframes (pd.DataFrame): _description_
        column_name (str): _description_
        how (str, optional): _description_. Defaults to "left".

    Returns:
        pd.DataFrame: _description_
    """
    output_dataframe = pd.merge(
        input_dataframe_1, input_dataframe_2, how=how, on=on
    )
    output_dataframe


# @st.cache
def create_missing_data_table(dataframe):
    """Display percentage of missing data in a table.

    Args:
        dataframe (pd.DataFrame): _description_
    """
    nan_table = dataframe.stb.missing(clip_0=False)
    return nan_table


def drop_categories(
    dataframe,
    drop_list
):
    """Drop categories not needed or redundant.

    Args:
        dataframe (pd.DataFrame): _description_
        list (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe = dataframe.drop(drop_list, axis=1)
    return dataframe


# @st.cache
def create_missing_data_matrix(dataframe):
    # fix type hints for the content of the 'object'
    """Display missing values status for each column in a matrix.

    Args:
        dataframe (pd.DataFrame): _description_

    Returns:
        object: _description_
    """
    missing_data_matrix = msno.matrix(
        dataframe,
        sort="descending",  # NOT working
        figsize=(10, 5),
        fontsize=8,
        sparkline=False,
    )
    return missing_data_matrix


def filter_categories(
    dataframe, filter_name
):
    """Filter job offer categories.

    Args:
        dataframe (pd.DataFrame): _description_
        filter_name (str): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe = dataframe[dataframe["filtre"] == filter_name]
    return dataframe


def create_barplot(data):
    # fix type hints for the content of the 'object'
    """Plot 'barplots' for each category filter.

    Args:
        variable (pd.DataFrame): _description_

    Returns:
        object: _description_
    """
    barplot = (
        alt.Chart(data, title="Total Number of Job Offers")
        .mark_bar()
        .encode(
            x=alt.X(
                "valeur_possible",
                axis=alt.Axis(title=f"{data.iloc[0, 0]}"),
            ),
            y=alt.Y(
                "nb_resultats",
                axis=alt.Axis(title="Number of Job Offers"),
            ),
        )
        .configure_view(strokeWidth=0)
        .interactive()
    )
    return barplot


def convert_to_datetime_format(date_var):
    """Convert date/time to 'datetime' format.

    Args:
        date (str): _description_

    Returns:
        datetime: _description_
    """
    datetime_var = datetime.datetime(
        year=date_var.year, month=date_var.month, day=date_var.day
    )
    return datetime_var


# def combine_date_to_time(date_stamp: str, time_stamp: str) -> object:
#     """Merge date and time

#     Args:
#         date (str): _description_
#         time (str): _description_

#     Returns:
#         datetime: _description_
#     """
#     date_time_combo = datetime.datetime.combine(date_stamp, time_stamp)
#     return date_time_combo


# @st.cache(suppress_st_warning=True)
def save_output_file(dataframe, file_name):
    """_summary_.

    Args:
        dataframe (_type_): _description_
        file_name (_type_): _description_

    Returns:
        _type_: _description_
    """
    save_output = st.download_button(
        label="Save results",
        data=dataframe.to_csv().encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        help="The file will be saved in your default directory",
    )
    return save_output


# if __name__ == "__main__":
#     start_search()
#     extract_search_content()
#     display_max_content()
#     convert_search_results_to_dataframe()
#     convert_df_to_html_table()
#     extract_search_categories()
#     extract_linked_categories()
#     rename_category()
#     flatten_category()
#     rename_columns_auto()
#     create_missing_data_table()
#     drop_categories()
#     create_missing_data_matrix()
#     filter_categories()
#     create_barplot()
#     convert_to_datetime_format()
#     # combine_date_to_time()
#     save_output_file


def main():
    """_summary_."""
    start_search()
    extract_search_content()
    display_max_content()
    convert_search_results_to_dataframe()
    convert_df_to_html_table()
    extract_search_categories()
    extract_linked_categories()
    rename_category()
    flatten_category()
    rename_columns_auto()
    create_missing_data_table()
    drop_categories()
    create_missing_data_matrix()
    filter_categories()
    create_barplot()
    convert_to_datetime_format()
    # combine_date_to_time()
    save_output_file()


if __name__ == "__main__":
    main()
