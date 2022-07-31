"""API of Pole Emploi
    Specifically, an API to consult available job offers.

    TODO split the function 'def extract_search_content()'
                into THREE different functions
    TODO merge the custom search types into one
    TODO better describe the sections and results
    TODO fix the function 'drop_low_occurrence_categories'
    TODO build functions
                TODO then, add cache function decorators, i.e.:
                @st.cache  # to be uncommented when function is written
    TODO keep 'st.json()' objects?
    TODO avoid hard-coding the categories (not elegant)
    TODO IMPORTANT !!
                fix the issue that top 150 hits is the limit for  search output
    TODO fix output format after filtering the categories (flatten out dicts)
                TODO then, select a category and add a filter for numerical &
                non-numerical filters (using sliders and number inputs)
    TODO add progress bar when saving files ?
    TODO modify exception/error in date range to print out following message:
                st.error(
                    '''If an error message appears below, it is likely that
                    the start and end dates are the same.\n
                    Please choose a range of at least ONE day.
                    '''
                )
    TODO write a snippet for subsetting filtered data (see 'lambda' functions)
    TODO why is 'client.referentiel("metiers")' not working?!
    TODO format numbers with a space between thousands
                => "{number:,}".replace(",", " ") is not working...
    TODO in basic search (or sidebar ?), add a column next to
                'List of Categories' containing a definition of the categories;
                e.g. scroll down list
    TODO keep top 5 competences and qualitesProfessionnelles
    TODO the default minimum date cannot be set
    TODO correct the column names in "Table of 'competences' "
                and in "Table of 'qualitesProfessionnelles' "
    TODO add streamlit pandas-profiling (see Streamlit website)
    TODO tick/untick the 'competences' and 'qualitesProfessionnelles' columns
                in nan table to display missing values without these columns
    TODO deploy app to Heroku or Streamlit
"""

from datetime import date
from decouple import config
from offres_emploi import Api
from offres_emploi.utils import dt_to_str_iso, filters_to_df
from dateutil import relativedelta
from st_aggrid import AgGrid
import sidetable as stb
import altair as alt
import datetime
import matplotlib.pyplot as plt
import missingno as msno
import pandas as pd
import seaborn as sns
import streamlit as st
import time


# -------------------------------------------------------------------------------------------

# SET-UP THE APP

# Initial page config
st.set_page_config(
    page_title="API Pole Emploi",
    page_icon="./images/epsilon_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Loïc Nazaries was here!",
        "Get help": "https://docs.streamlit.io/library/api-reference",
        # "Report a Bug": "lnazaries@epsilon-alcen.com",
    },
)

# Other default settings
# disable warnings from deprecation
st.set_option('deprecation.showPyplotGlobalUse', False)
# pd.set_option("precision", 2)  # display floats with 2 decimal places

# Display Epsilon logo
st.sidebar.image("./images/epsilon_logo.png")

# App title
st.title("API de Pole Emploi")

# Show Pole Emploi API log-in image
st.image("./images/api_pe_account.png")

st.header("Recherche d'offres d'emploi avec l'API '**Offres d'emploi v2'**")
# Add link to API page
st.write(
    """
    Click
    [here](https:/pole-emploi.io/data/api/offres-emploi)
    to access the API page.
    """
)

st.markdown("---")


# Log-in section
st.sidebar.info("Enter user log-in details")
user_name = st.sidebar.text_input(label="Username")
user_password = st.sidebar.text_input(label="Password")

if not user_name:
    st.warning("Please input your user name.")
    st.stop()
elif not user_password:
    st.warning("Please input your password.")
    st.stop()
st.sidebar.success("You have successfully logged in.")


# Define API client
st.subheader("Enter your API client credentials")

left_column, right_column = st.columns(2)
with left_column:
    client_id = st.text_input(label="Client ID", key=1)

with right_column:
    client_secret = st.text_input(label="Password", key=2)

# Add a clickable log-in action ?
connect_api = st.button(label="Connect to API")

# Use de token details from the online account.
# Use client ID and secret using .env file
client = Api(
    client_id=config("API_PE_CLIENT", default=""),
    client_secret=config("API_PE_SECRET", default=""),
)

if connect_api:
    with st.spinner(text="Connecting..."):
        time.sleep(2)
    st.success("You can now access the API of Pole Emploi.")


# Analysis options
customised_search = (
    "Default settings",
    "Search based on dates and keywords",
    "Search based on values in categories",
)
st.sidebar.subheader("Customised Search")
search_type = st.sidebar.selectbox(
    label="Pick a Type of Analysis", options=customised_search
)

st.markdown("---")

# -------------------------------------------------------------------------------------------

# START DATA ANALYSIS

st.header("Default Analysis")

# This coming section is done "behind the scene"
# This is to prepare the data for analysis
# Importantly, we want to flatten  all the variables coming from a .JSON file
# This is because there are some sections with nested dictionaries and lists


def start_search(params: dict = None) -> dict:
    # fix type hints for the content of the dict
    """_summary_

    Args:
        params (dict, optional): _description_. Defaults to None.

    Returns:
        dict: _description_
    """
    basic_search = client.search(params)
    return basic_search


basic_search = start_search()


def extract_search_content(search_session: dict) -> list[int]:
    # fix type hints for the content of each dict
    """Prepare the search output from a basic search
    The basic search corresponds to two lists and one dictionary, namely:
    - the `resultats`, which contains all the available data
    - the `filtresPossibles`, which composed of four `filters` (or 'themes')
        -
        -
        -
        -
    - the `Content-Range`, which indicates the number of hits from the search

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


(results, filters, content_range) = extract_search_content(
    search_session=basic_search
)


def display_max_content(content_range: dict[str, int]) -> str:
    # fix type hints for the content of the dict
    """Get the number of hits from the search

    Args:
        content_range (dict): _description_

    Returns:
        str: _description_
    """
    content_max = content_range["max_results"]
    return content_max


content_max = display_max_content(content_range=content_range)

st.write(f"Total number of job offers: {content_max}")

# -------------------------------------------------------------------------------------------

# Prepare the data for data cleaning

# Display the first raw result
st.subheader("Search Output Preview of First Hit")
search_preview = results[0]
st.json(search_preview)  # delete ?


def convert_search_results_to_dataframe(
    search_results: list[int],
) -> pd.DataFrame:
    # fix type hints for the content of the list
    """Transform results list into a dataframe

    Args:
        results (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    results_df = pd.DataFrame(search_results)
    return results_df


results_df = convert_search_results_to_dataframe(search_results=results)

st.subheader("Summary Table of First Five Hits")
AgGrid(results_df.iloc[0:5, :], key=1)


st.write("List of all the categories in the database")


def extract_search_categories(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Extract a list of all columns/categories in the dataframe

    Args:
        results_df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    category_list = pd.DataFrame(dataframe.columns)
    category_list.columns = ["Categories"]
    return category_list


category_list = extract_search_categories(dataframe=results_df)
category_list

# # Manually extract the dictionary variables from nested designs
# st.write("Dictionary variables to be flattened")
# columns_to_flatten = [
#     "lieuTravail",
#     "entreprise",
#     "salaire",
#     "contact",
#     "origineOffre",
#     # "langues",  # unpack a list - NOT working
#     # "qualitesProfessionnelles",  # unpack a list - NOT working
#     #  "competences",  # unpack a list - NOT working
#     # "formations", # unpack a list - NOT working
#     # "permis",  # unpack a list - NOT working
# ]
# st.dataframe(columns_to_flatten)


def flatten_category(dataframe: pd.DataFrame, category: str) -> pd.DataFrame:
    """_summary_

    Args:
        dataframe (pd.DataFrame): _description_
        category (str): _description_

    Returns:
        pd.DataFrame: _description_
    """
    flattened_category = dataframe[category].apply(pd.Series)
    return flattened_category


# Variable 'lieuTravail'
st.write("Category 'lieuTravail' ")

flattened_lieu_travail = flatten_category(
    dataframe=results_df, category="lieuTravail"
)


def extract_bound_categories(
    dataframe: pd.DataFrame,
    category_to_extract: str,
    new_fields: list[str]
) -> pd.DataFrame:
    """Extraction of columns with nested design

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
    return dataframe


flattened_lieu_travail = extract_bound_categories(
    dataframe=flattened_lieu_travail,
    category_to_extract="libelle",
    new_fields=["departement", "ville"],
)


def drop_unnecessary_categories(
    dataframe: pd.DataFrame, category_list: list[str]
) -> pd.DataFrame:
    """_summary_

    Args:
        dataframe (pd.DataFrame): _description_
        category_list (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe = dataframe.drop(category_list, axis=1)
    return dataframe


flattened_lieu_travail = drop_unnecessary_categories(
    dataframe=flattened_lieu_travail,
    category_list=[
        "libelle",
        "commune",
        "latitude",
        "longitude"
    ],
)
AgGrid(flattened_lieu_travail.iloc[0:5, :], key=2)


# Variable 'entreprise'
st.write("Category 'entreprise' ")

flattened_entreprise = flatten_category(
    dataframe=results_df, category="entreprise"
)


def rename_category(
    dataframe: pd.DataFrame,
    columns: dict[str, str],
) -> pd.DataFrame:
    """_summary_

    Args:
        dataframe (pd.DataFrame): _description_
        columns (dict): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe.rename(columns=columns, inplace=True)
    return dataframe


flattened_entreprise = rename_category(
    dataframe=flattened_entreprise,
    columns={"nom": "nomEntreprise", "description": "descriptionEntreprise"},
)

flattened_entreprise = drop_unnecessary_categories(
    dataframe=flattened_entreprise,
    category_list=["logo", "url"],
)
AgGrid(flattened_entreprise.iloc[0:5, :], key=3)


# Variable 'salaire'
# not always present... needs to be hidden, sometimes
st.write("Category 'salaire' ")

flattened_salaire = flatten_category(dataframe=results_df, category="salaire")

flattened_salaire = rename_category(
    dataframe=flattened_salaire,
    columns={"libelle": "salaire"},
)

flattened_salaire = drop_unnecessary_categories(
    dataframe=flattened_salaire,
    category_list=[
        "complement1",
        # "complement2",
        "commentaire",
    ],
)
AgGrid(flattened_salaire.iloc[0:5, :], key=4)

# Variable 'contact'
st.write("Category 'contact' ")

flattened_contact = flatten_category(dataframe=results_df, category="contact")

flattened_contact = rename_category(
    dataframe=flattened_contact,
    columns={"nom": "nomContact"},
)

flattened_contact = drop_unnecessary_categories(
    dataframe=flattened_contact,
    category_list=[
        "coordonnees1",
        # "commentaire",  # NOT always in the searches
        "urlPostulation",
        # "coordonnees2",  # NOT always in the searches
        # "coordonnees3",  # NOT always in the searches
    ],
)
AgGrid(flattened_contact.iloc[0:5, :], key=5)  # NOT working ?


# Variable 'origineOffre'
st.write("Category 'origineOffre' ")

flattened_origineOffre = flatten_category(
    dataframe=results_df, category="origineOffre"
)

flattened_origineOffre = rename_category(
    dataframe=flattened_origineOffre,
    columns={"origine": "origineOffre"},
)
AgGrid(flattened_origineOffre.iloc[0:5, :], key=6)


# Variable 'langues'
st.write("Category 'langues' ")

# flattenerd_langues = results_df["langues"].apply(pd.Series)
# flattened_langues.rename(columns={"0": "langues"}, inplace=True) # NOT workin

# st.table(flattened_langues.iloc[0:5, :])


# Variable 'qualitesProfessionnelles'
st.write("Category 'qualitesProfessionnelles' ")

flattened_qualitesPro = flatten_category(
    dataframe=results_df, category="qualitesProfessionnelles"
)


def rename_columns_auto(dataframe: pd.DataFrame, column_name: str) -> list:
    """Create automatic list of 'qualitesPro' (problem w/ column name)

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


flattened_qualitesPro = rename_columns_auto(
    dataframe=flattened_qualitesPro, column_name="qualitesPro"
)
flattened_qualitesPro.iloc[0:5, :]

# below NOT working
flattened_qualitesPro = rename_category(
    dataframe=flattened_qualitesPro,
    columns={
        "('qualitePro 0',)": "qualitePro_0",
        "('qualitePro 1',)": "qualitePro_1",
        "('qualitePro 2',)": "qualitePro_2",
    },
)
# flattened_qualitesPro.iloc[0:5, :]


# Variable 'competences'
st.write("Category 'competences' ")

flattened_competences = flatten_category(
    dataframe=results_df, category="competences"
)

flattened_competences = rename_columns_auto(
    dataframe=flattened_competences, column_name="competences"
)
flattened_competences.iloc[0:5, :]
# Eventually, keep top 5 competences

# Variable 'permis'  # to be done


# Variable 'formations'  # to be done


# Drop the columns used for flattening
st.write(
    "Reduced Dataframe 'results_df'  Without Categories Used for Flattening"
)

categories_to_drop = [
    "lieuTravail",
    "entreprise",
    "salaire",  # NOT always present... hence, hiding for now
    "contact",
    "origineOffre",
    # "langues",  # NOT always present... hence, hiding for now
    "qualitesProfessionnelles",
    "competences",
    #  "formations",  # coding to be done as above
    # "permis",  # coding to be done as above
]


def drop_categories(
    dataframe: pd.DataFrame,
    drop_list: list[str]
) -> pd.DataFrame:
    # fix type hints for the content of the dict
    """_summary_

    Args:
        dataframe (pd.DataFrame): _description_
        list (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe_drop = dataframe.drop(drop_list, axis=1)
    return dataframe_drop


results_df_redux = drop_categories(
    dataframe=results_df, drop_list=categories_to_drop
)
AgGrid(results_df_redux.iloc[0:5, :], key=7)


# Concatenation of the flattened tables
st.write("Table of Flattened Categories")

flattened_categories = [
    flattened_lieu_travail,
    flattened_entreprise,
    flattened_salaire,
    flattened_contact,
    flattened_origineOffre,
    # flattened_langues,  # flattening and renaming did NOT work
    # # also, bugs with missing data table. hence, deactivate for now
    # flattened_qualitesPro,  # bugs with missing data table
    # # hence, deactivate for now
    # flattened_competences,  # bugs with missing data table
    # # hence, deactivate for now
    # flattened_formations,  # to be done
    # flattened_permis,  # to be done
]


def concatenate_dataframes(column_list: list[str]) -> pd.DataFrame:
    """_summary_

    Args:
        column_list (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    dataframe = pd.concat(column_list, axis=1)
    return dataframe


results_df_flattened = concatenate_dataframes(column_list=flattened_categories)
st.dataframe(results_df_flattened.iloc[0:5, :])


# Concatenation of the flattened tables to the reduced 'results_df'
st.write("Penultimate Table Including Reduced Dataframe and Flattened Tables")

results_df_final = concatenate_dataframes(
    column_list=[results_df_redux, results_df_flattened]
)
st.dataframe(results_df_final.iloc[0:5, :])


# Prepare summary table of missing data
st.write("Summary of Missing Data (buggy if 'competences' are included)")


def create_missing_data_matrix(dataframe: pd.DataFrame) -> object:
    # fix type hints for the content of the 'object'
    """Display missing values status for each column in a matrix

    Args:
        dataframe (pd.DataFrame): _description_

    Returns:
        object: _description_
    """
    missing_data_matrix = msno.matrix(
        dataframe,
        sort="descending",  # NOT working
        figsize=(10, 5),
        fontsize=10,
        sparkline=False,
    )
    return missing_data_matrix


missing_data_matrix = create_missing_data_matrix(dataframe=results_df_final)


# Create matrix of missing data
st.pyplot(missing_data_matrix.figure, key=1)


def create_missing_data_bars(dataframe: pd.DataFrame) -> object:
    # fix type hints for the content of the 'object'
    """Display missing values status for each column in a bar chart

    Args:
        dataframe (pd.DataFrame): _description_

    Returns:
        object: _description_
    """
    missing_data_bars = msno.bar(
        dataframe,
        sort="descending",
        color="dodgerblue",
        figsize=(10, 15),
        fontsize=10,
    )
    return missing_data_bars


missing_data_bars = create_missing_data_bars(results_df_final)


# Create bar chart of missing data
st.pyplot(dataframe=missing_data_bars.figure, key=2)


st.write("Table of missing values in each category")


def create_missing_data_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Display percentage of missing data in a table

    Args:
        dataframe (pd.DataFrame): _description_
    """
    nan_table = dataframe.stb.missing(clip_0=False)
    return nan_table


st.text(
    """
    The following categories were not included in the missing data table
    below because they could not be flattened properly:
        - qualitesPro
        - competences
    """
)

nan_table = create_missing_data_table(dataframe=results_df_final)
nan_table


# alternatively, a menu with all categories is displayed, and user 'unticks'
# the unwanted values (see next section too)
st.write(results_df_redux.columns)
st.selectbox("pick me", results_df_redux.columns)
# st.multiselect(label="Remove categories", options=results_df_redux.columns)
# # 'multiselect' NOT working


st.write("Final Table of Job Offers")


# def drop_low_occurrence_categories(
#     dataframe: pd.DataFrame, threshold: int = 50
# ) -> pd.DataFrame:
#     """Delete unnecessary columns with over 50% of missing data per columns

#     Args:
#         dataframe (pd.DataFrame): _description_
#         threshold (int, optional): _description_. Defaults to 50.

#     Returns:
#         _type_: _description_
#     """
#     dataframe_redux = [
#         dataframe.drop(col)
#         for col in dataframe.columns
#         if dataframe[col] > threshold
#     ]
#     return dataframe_redux


# # Below  NOT working
# results_df_final_redux = drop_low_occurrence_categories(
#     dataframe=results_df_final
# )
# results_df_final_redux
# AgGrid(results_df_final_redux)

# Since above code not working, dropping unnecessary manually
final_category_drop = [
    # "agence",  # does not always shows up in the analysis
    # "experienceCommentaire",  # does not always shows up in the analysis
    # "complement2",  # does not always shows up in the analysis
    # "deplacementCode",
    # "deplacementLibelle",
    # "permis",
    # "langues",  # does not always shows up in the analysis
    # "commentaire",  # does not always shows up in the analysis
    "formations",
    # "complement1",  # does not always shows up in the analysis
    # "logo",  # does not always shows up in the analysis
    # "url",  # does not always shows up in the analysis
    "descriptionEntreprise",
]

results_df_final_redux = results_df_final.drop(
    final_category_drop,
    axis=1,
)
AgGrid(results_df_final_redux)

st.markdown("---")


# # html output of final dataframe
# from st_aggrid import AgGrid, GridOptionsBuilder
# from st_aggrid.shared import GridUpdateMode


# def aggrid_interactive_table(dataframe: pd.DataFrame):
#     """Creates an st-aggrid interactive table based on a dataframe.

#     Args:
#         dataframe (pd.DataFrame]): Source dataframe

#     Returns:
#         dict: The selected row
#     """
#     options = GridOptionsBuilder.from_dataframe(
#         dataframe, enableRowGroup=True, enableValue=True, enablePivot=True
#     )

#     options.configure_side_bar()

#     options.configure_selection("single")
#     selection = AgGrid(
#         dataframe,
#         enable_enterprise_modules=True,
#         gridOptions=options.build(),
#         theme="light",
#         update_mode=GridUpdateMode.MODEL_CHANGED,
#         allow_unsafe_jscode=True,
#     )

#     return selection


# iris = pd.read_csv(
#     "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
# )

# selection = aggrid_interactive_table(dataframe=iris)

# if selection:
#     st.write("You selected:")
#     st.json(selection["selected_rows"])

# --------------------------------------------------------------------------------------------

# BUILD A METRIC DASHBOARD

st.subheader("Number of Hits for Each Job Offer Filter")

filters_df = filters_to_df(filters)
AgGrid(filters_df)

# Get the number of hits from the search
left_column, right_column = st.columns(2)
with left_column:
    # content_range = basic_search["Content-Range"]
    st.info(
        f"""
        Total number of job offers this month\n
        {content_max}
        """
    )

# Add a metric of the change in job offer number since previous month
# i.e. use the non-working snippet below:
# default_start_date = date.today() - relativedelta.relativedelta(months=1)
with right_column:
    st.metric(
        label="Number of job offers since previous month",
        value=654321,
        # value=past_month_offers,
        # delta=12345,
        delta=int(content_max) - 654321,
    )

# -------------------------------------------------------------------------------------------

# DRAW AN HISTOGRAM OF JOB OFFERS FOR EACH CATEGORY


def filter_categories(
    dataframe: pd.DataFrame, filter_name: str
) -> pd.DataFrame:
    """Filter job offer categories.

    Args:
        dataframe (pd.DataFrame): _description_
        filter_name (str): _description_

    Returns:
        pd.DataFrame: _description_
    """
    filtered_category = dataframe[dataframe["filtre"] == filter_name]
    return filtered_category


contract_type_df = filter_categories(
    dataframe=filters_df, filter_name="typeContrat"
)
experience_df = filter_categories(
    dataframe=filters_df, filter_name="experience"
)
qualification_df = filter_categories(
    dataframe=filters_df, filter_name="qualification"
)
contract_nature_df = filter_categories(
    dataframe=filters_df, filter_name="natureContrat"
)

filters_list = (
    contract_type_df,
    experience_df,
    qualification_df,
    contract_nature_df,
)


def create_barplot(data: pd.DataFrame) -> object:
    # fix type hints for the content of the 'object'
    """Plot 'barplots' for each category filter

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


for filter_var in filters_list:
    filters_barplot = create_barplot(filter_var)
    st.altair_chart(filters_barplot, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------------------------------------

# CUSTOMISE THE SEARCH


def convert_to_datetime_format(date_var: str) -> object:
    """Convert date/time to 'datetime' format

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


st.header("Choose a custom analysis from the left-side panel")

if search_type == "Search based on dates and keywords":
    # Run a custom search  based on dates and keywords
    st.subheader("Search based on dates and keywords")

    # Custom settings
    # Set a default date to avoid error message when loading the page as the
    # date menu will ask for 'maxCreationDate ' superior to 'minCreationDate '
    # Hence 'default_start_date' is set to ONE month prior to today's date
    default_start_date = date.today() + relativedelta.relativedelta(months=-1)
    default_start_date

    # 'default_start_date' does NOT work with 'min_value' below
    left_column, right_column = st.columns(2)
    with left_column:
        start_date = st.date_input(
            label="Pick a Start Date", min_value=default_start_date
        )
        end_date = st.date_input(label="Pick an End Date")

    # with right_column:
    #     start_time = st.time_input(label="Pick a Start Time")
    #     end_time = st.time_input(label="Pick an End Time")

    start_date = convert_to_datetime_format(start_date)
    end_date = convert_to_datetime_format(end_date)

    # start_dt = convert_to_datetime_format(start_date)
    # end_dt = convert_to_datetime_format(end_date)

    # start_datetime = combine_date_to_time(start_dt, start_time)
    # end_datetime = combine_date_to_time(start_time, end_time)

    # start_dt = datetime.datetime(
    #     year=start_date.year, month=start_date.month, day=start_date.day
    # )
    # start_datetime = datetime.datetime.combine(start_dt, start_time)

    # end_dt = datetime.datetime(
    #     year=end_date.year, month=end_date.month, day=end_date.day
    # )
    # end_datetime = datetime.datetime.combine(end_date, end_time)

    # Set-up the search parameters
    key_words = st.text_input(
        label="Enter One or More Keywords, e.g. data analyst, bi"
    )

    # Display an error message in case the date range is not of at least 1 day
    st.error(
        """
        If an error message appears below, it is likely that the start and
        end dates are the same.\n
        Please choose a range of at least ONE day.
        """
    )

    # Pass on the parameters of the search
    parameters = {
        "motsCles": key_words,
        "minCreationDate": dt_to_str_iso(start_date),
        "maxCreationDate": dt_to_str_iso(end_date),
    }

    search_date = start_search(params=parameters)

    # Prepare filters output
    filters = search_date["filtresPossibles"]
    # Transform filters list into a dataframe using `filters_to_df()`
    st.info(
        """
        Search Filters based on:\n
            - Contract Type\n
            - Experience\n
            - Qualification\n
            - Contract Nature
        """
    )

    filters_df = filters_to_df(filters)
    # filters_df = filters_df.columns.values[0] = "categories"  # NOT working
    AgGrid(filters_df)

    # # Plot the filters output  # NOT working
    # g = sns.FacetGrid(filters_df, col="filtre", sharex=False, sharey=False)
    # g = g.map(data=sns.barplot, row="valeur_possible", col="nb_resultats")

    # Save the search output
    st.download_button(
        label="Save results",
        data=filters_df.to_csv().encode("utf-8"),
        file_name="filter_output.csv",
        mime="text/csv",
        help="The file will be saved in your default directory",
        key=1,
    )

# -------------------------------------------------------------------------------------------

elif search_type == "Search based on values in categories":
    # Run a custom search  using keywords and categories
    st.subheader("Search based on values in categories")

    # IMPORTANT: I could not worked out yet how to isolate the column names,
    # hence they were hard-coded below
    # use the columns of the concatenated list of flattened variables instead ?
    category_list = [
        "id",
        "intitule",
        "description",
        "dateCreation",
        "dateActualisation",
        "lieuTravail",
        "departement",
        "ville",
        "romeCode",
        "romeLibelle",
        "appellationlibelle",
        # "entreprise",
        "nomEntreprise",
        "descriptionEntreprise",
        "typeContrat",
        "typeContratLibelle",
        "natureContrat",
        "experienceExige",
        "experienceLibelle",
        "competences",
        "salaire",
        "dureeTravailLibelle",
        "dureeTravailLibelleConverti",
        "alternance",
        # "contact",
        "nomContact",
        "nombrePostes",
        "accessibleTH",
        "qualificationCode",
        "qualificationLibelle",
        "secteurActivite",
        "secteurActiviteLibelle",
        "qualitesProfessionnelles",
        "origineOffre",
        "offresManqueCandidats",
        "langues",
        "formations",
        "deplacementCode",
        "deplacementLibelle",
        "agence",
        "permis",
        "experienceCommentaire",
    ]
    # Sort list of categories and change column name
    category_list.sort(reverse=False)
    # Change list name
    list_categories = {"Final list of categories": category_list}
    # Display list of categories on the left-side panel
    st.sidebar.dataframe(list_categories)

    # Set-up the search parameters
    # Default search
    st.info(
        """
        For the purpose of demonstration,  we search job offers using
        keywords and categorical values, such as:\n
            - keywords: BI, Talend, Bac+5\n
            - departement: 33\n
            - typeContrat: CDI\n
            - qualitesProfessionnelles: ouverture d'esprit
        """
    )

    key_words = st.text_input(
        label="Enter One or More Keywords, e.g. data analyst, bi"
    )
    # select_columns = st.multiselect(
    #     label="Select one or more categories", options=category_list
    # )
    parameters = {
        "motsCles": key_words,
        # "categories": select_columns,
    }
    # Use hard-coded parameters for now
    parameters = {
        "motsCles": {
            "BI",
            # "Talend",
            "Bac+5",
        },
        "departement": "33",
        "typeContrat": "CDI",
        "qualitesProfessionnelles": "ouverture d'esprit",
    }

    search_categories = start_search(params=parameters)

    # Get the number of hits from the search
    content_range = search_categories["Content-Range"]
    st.write(f"Total number of job offers: {content_range['max_results']}")

    # Prepare search results
    results = search_categories["resultats"]

    # Display the first result
    st.subheader("Search Output Preview of First Hit")
    search_categories_preview = results[0:1]
    st.json(search_categories_preview)

    # Transform results list into a dataframe
    st.subheader("Summary Table")
    results_df = pd.DataFrame(results)
    AgGrid(results_df)

    # Save the search output
    st.download_button(
        label="Save results",
        data=results_df.to_csv().encode("utf-8"),
        file_name="search_category_output.csv",
        mime="text/csv",
        help="The file will be saved in your default directory",
        key=2,
    )

    # Filter data by using the `salaire` for each `entreprise`
    st.subheader("Filter Categories")
    # Select the variables to keep
    # Default filters
    st.info(
        """
        For the purpose of demonstration,  we filter job offers for:\n
            - id\n
            - entreprise\n
            - salaire/libelle
        """
    )

    # This code snippet should be deleted and/or merged with subsetting snippet
    # Also, all columns should be flattened out
    st.write("Job Offers Before Filtering")
    # Use hard-coded parameters for now
    filtered_results = pd.DataFrame(results)[["id", "entreprise", "salaire"]]
    AgGrid(filtered_results)

    # Custom filters
    # filtered_results = st.multiselect(
    #     label="Choose filters to apply",
    #     options=category_list
    #     )
    # AgGrid(filtered_results)

    # Subset the dataframe for `enterprise` name and `salaire` within
    # `libelle` category; this is hard-coded below, for now
    st.subheader(
        "Subset the filtered data to analyse the salary per enterprise"
    )
    # Select enterprise name from `nom` column and salary from `libelle` column
    salary_by_enterprise = filtered_results.agg(
        dict(
            entreprise=lambda x: x.get("nom"),
            salaire=lambda x: x.get("libelle"),
        )
    )

    # Transform 'id' column into a series type to be able to use the
    # 'insert()' function to add it to the dataframe after the previous
    # operation
    id_offre = filtered_results["id"].squeeze()

    # Re-insert the 'id_offre' series to the 'salary_by_enterprise' dataframe
    salary_by_enterprise.insert(0, "id_offre", id_offre)
    AgGrid(salary_by_enterprise)

    # Drop the rows with missing data
    salary_by_enterprise = salary_by_enterprise.dropna()
    # Get the final number of hits from the search
    st.write(
        f"""
        Final number of job offers after removing missing data:
            {len(salary_by_enterprise)}
        """
    )
    AgGrid(salary_by_enterprise)

    # # Convert the final dataframe to a '.csv' format string
    # # NOT working but works well with the next code block
    # salary_by_enterprise_output = salary_by_enterprise.to_csv(
    #     sep=",",
    #     na_rep="",
    #     index=False,
    # ).encode("utf-8"),

    # Save the search output
    st.download_button(
        label="Save results",
        data=salary_by_enterprise.to_csv(
            sep=",",
            na_rep="",
            index=False,
        ).encode("utf-8"),
        file_name="salary_by_enterprise.csv",
        mime="text/csv",
        help="The file will be saved in your default directory",
        key=3,
    )


# # NOT working
# # Access job type (referentiel)
# referentiel_metiers = client.referentiel("metiers")
# referentiel_metiers
