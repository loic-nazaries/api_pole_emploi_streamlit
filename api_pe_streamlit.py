"""API of Pole Emploi
    Specifically, an API to consult available job offers.

    TODO create a GitHub repo
    TODO better describe the sections and results
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
    TODO write a snippet for subsetting filtered data (see 'lambda' functions)
    TODO why is 'client.referentiel("metiers")' not working?!
    TODO format numbers with a space between thousands
                => "{number:,}".replace(",", " ") is not working...
    TODO in basic search (or sidebar ?), add a column next to
                'List of Categories' containing a definition of the categories;
                e.g. scroll down list
    TODO fix missing values table and data plot
    TODO the default minimum date cannot be set
    TODO correct the column names in "Table of 'competences' "
    TODO add streamlit pandas-profiling (see website)
    TODO tick/untick the 'competences' column to display missing values
                => propagation to other 'buggy' tables ?
    TODO deploy app to Heroku
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
# Run a basic search
# A 'basic search'  targets all the data available from the API
basic_search = client.search()

# The basic search corresponds to three lists, namely:
# - the `resultats`, which contains all the available data
# - the `filtresPossibles`, which composed of four `filters` (or 'themes')
#       -
#       -
#       -
#       -
# - the `Content-Range`, which indicates the number of hits from the search

# Prepare the search output from a basic search
results = basic_search["resultats"]
filters = basic_search["filtresPossibles"]
content_range = basic_search["Content-Range"]

# Get the number of hits from the search
content_max = content_range["max_results"]
st.write(f"Total number of job offers: {content_max}")

# -------------------------------------------------------------------------------------------

# Prepare the data for data cleaning
# Display the first raw result
st.subheader("Search Output Preview of First Hit")
search_preview = results[0]
st.json(search_preview)  # delete ?

# Transform results list into a dataframe
st.subheader("Summary Table of First Five Hits")
results_df = pd.DataFrame(results)
AgGrid(results_df.iloc[0:5, :])

# Extract a list of all columns in the dataframe
st.write("List of all the categories in the database")
category_list = pd.DataFrame(results_df.columns)
category_list.columns = ["Categories"]
# AgGrid(category_list)  # NOT working: argument of type 'int' is not iterable
category_list

# # Manually extract the dictionary variables from nested designs
# st.write("Dictionary variables to be flattened")
# columns_to_flatten = [
#     "lieuTravail",
#     "entreprise",
#     "salaire",
#     "contact",
#     "origineOffre",
#     "competences",  # unpack a list - NOT working
#     "langues",  # unpack a list - NOT working
#     # "qualitesProfessionnelles",  # unpack a list - NOT working
#     # "formations",  # unpack a list - NOT working
#     # "permis",  # unpack a list - NOT working
# ]
# st.dataframe(columns_to_flatten)

# Variable 'lieuTravail'
st.write(
    """
    Flattening of 'lieuTravail' (sometimes buggy with
    the 'libelle' variable, hence column not always showing)
    """
)
flatten_lieu_travail = results_df["lieuTravail"].apply(pd.Series)
# flatten_lieu_travail[["departement", "ville"]] = flatten_lieu_travail[
#     "libelle"
# ].str.split("-", expand=True)
flatten_lieu_travail = flatten_lieu_travail.drop(
    "libelle",
    # inplace=True,
    axis=1,
)
AgGrid(flatten_lieu_travail.iloc[0:5, :])

# Variable 'entreprise'
flatten_entreprise = results_df["entreprise"].apply(pd.Series)
flatten_entreprise.rename(
    columns={"nom": "nomEntreprise", "description": "descriptionEntreprise"},
    inplace=True,
)

# Variable 'salaire'
flatten_salaire = results_df["salaire"].apply(pd.Series)
flatten_salaire.rename(columns={"libelle": "salaire"}, inplace=True)

# Variable 'contact'
flatten_contact = results_df["contact"].apply(pd.Series)
flatten_contact.rename(columns={"nom": "nomContact"}, inplace=True)

# Variable 'origineOffre'
flatten_origineOffre = results_df["origineOffre"].apply(pd.Series)
flatten_origineOffre.rename(columns={"origine": "origineOffre"}, inplace=True)

# # Variable 'langues'
# flatten_langues = results_df["langues"].apply(pd.Series)
# flatten_langues.rename(columns={"0": "langues"}, inplace=True)  # NOT working

# Variable 'qualitesProfessionnelles'
flatten_qualitesProfessionnelles = results_df[
    "qualitesProfessionnelles"
].apply(pd.Series)
# Create automatic list of 'qualitesProfessionnelles' (problem w/ column name)
qualitePro_columns = [
    "qualitesPro %d" % i
    for i in range(len(flatten_qualitesProfessionnelles.columns))
]
# Change column names to 'competences'
st.write("Table of 'qualitePro' ")
flatten_qualitesProfessionnelles.columns = [qualitePro_columns]
flatten_qualitesProfessionnelles.rename(
    columns={
        "('qualitePro 0',)": "qualitePro_0",
        "('qualitePro 1',)": "qualitePro_1",
        "('qualitePro 2',)": "qualitePro_2",
    },
    inplace=True,
)  # NOT working
flatten_qualitesProfessionnelles.iloc[0:5, :]

# Variable 'competences'
flatten_competences = results_df["competences"].apply(pd.Series)
# flatten_competences
# Create automatic list of competences (problem with column name)
competence_columns = [
    "competences %d" % i for i in range(len(flatten_competences.columns))
]
# competence_columns_list = list(competence_columns)
st.write(flatten_competences.columns)

# Change column names of 'competences'
st.write("Table of 'competences' ")
flatten_competences.columns = [competence_columns]
# flatten_competences.columns = [competence_columns_list]
flatten_competences.iloc[0:5, :]

# Below NOT working
# Rename the columns from the 'competences' category
flatten_competences.rename(
    columns={"0": "competence 0"}, inplace=True
)  # NOT working

# # Using regex ?
# flatten_competences["('competences 0',)"].str.replace(
#     '"|(@*[-]?+)', "", regex=True
# )
# # OR
# import re
# flatten_competences.rename(
#     columns={
#         element: re.sub(r"(.+)", r"x_\1", element)
#         for element in flatten_competences.columns.tolist()
#     }
# )

# AgGrid(flatten_competences.iloc[0:5, :])  # NOT working as cannot be tuple ?
flatten_competences.iloc[0:5, :]

# Drop the columns used for flattening
st.write("Reduced Dataframe 'results_df'  Without Columns Used for Flattening")
results_df_redux = results_df.drop(
    [
        "lieuTravail",
        "entreprise",
        "salaire",
        "contact",
        "origineOffre",
        "qualitesProfessionnelles",
        "competences",
        # "langues",  # coding to be done as above
        # "formations",  # coding to be done as above
        # "permis",  # coding to be done as above
    ],
    axis=1,
)
AgGrid(results_df_redux.iloc[0:5, :])

# Concatenation of the flattened tables
st.write("Table of Flattened Columns")
flattened_columns = (
    flatten_lieu_travail,
    flatten_entreprise,
    flatten_salaire,
    # flatten_contact,  # this could NOT be concatenated
    # flatten_origineOffre,  # this could NOT be concatenated
    # flatten_langues,  # flattening and renaming did NOT work
    # flatten_qualitesProfessionnelles,  # bugs with missing data
    # flatten_competences,  # bugs with missing data if included in the search
    # # hence, deactivate for now
)
results_df_flattened = pd.concat(flattened_columns, axis=1)
results_df_flattened.iloc[0:5, :]

# Concatenation of the flattened tables to the reduced 'results_df'
st.write("Penultimate Table Including Reduced Dataframe and Flattened Tables")
results_df_final = pd.concat([results_df_redux, results_df_flattened], axis=1)
results_df_final.iloc[0:5, :]

# Prepare summary table of missing data
st.write("Summary of Missing Data (buggy if 'competences' are included)")

# Display missing values status for each column in a matrix
missing_data_matrix = msno.matrix(
    results_df_final,
    sort="descending",  # NOT working
    figsize=(10, 5),
    fontsize=10,
    sparkline=False,
)
st.pyplot(missing_data_matrix.figure, key=1)
# Display missing values status for each column in a bar chart
missing_data_bars = msno.bar(
    results_df_final,
    sort="descending",
    color="dodgerblue",
    figsize=(10, 5),
    fontsize=10,
    # p=0.5,  # NOT working ?
)
# st.pyplot(missing_data_bars.figure, key=2)

st.write("Table of missing values in each category")
st.text(
    """
    The following categories were not included in the missing data table
    below because they could not be flattened properly:
        - competences
        - qualitesProfessionnelles
    """
)
# Display percentage of missing data in a table
nan_table = results_df_final.stb.missing(clip_0=False)
nan_table

# # Delete unnecessary columns with over 50% of missing data per columns
st.write("Final Table of Job offers")
# # Below  NOT working
# results_df_final_redux = [
#     results_df_final.drop(col)
#     for col in results_df_final.columns
#     if results_df_final[col] > 50
# ]
# AgGrid(results_df_final_redux)
# results_df_final_redux

# Since above code not working, dropping unnecessary manually
results_df_final_redux = results_df_final.drop(
    [
        # "agence",  # does not always shows up in the analysis
        # "experienceCommentaire",  # does not always shows up in the analysis
        # "complement2",  # does not always shows up in the analysis
        "deplacementCode",
        "deplacementLibelle",
        "permis",
        # "langues",  # does not always shows up in the analysis
        "commentaire",  # does not always shows up in the analysis
        "formations",
        "complement1",
        "logo",
        "url",
        "descriptionEntreprise",
    ],
    axis=1,
)
AgGrid(results_df_final_redux)

st.markdown("---")


# # html output of final dataframe
# from st_aggrid import AgGrid, GridOptionsBuilder
# from st_aggrid.shared import GridUpdateMode


# def aggrid_interactive_table(df: pd.DataFrame):
#     """Creates an st-aggrid interactive table based on a dataframe.

#     Args:
#         df (pd.DataFrame]): Source dataframe

#     Returns:
#         dict: The selected row
#     """
#     options = GridOptionsBuilder.from_dataframe(
#         df, enableRowGroup=True, enableValue=True, enablePivot=True
#     )

#     options.configure_side_bar()

#     options.configure_selection("single")
#     selection = AgGrid(
#         df,
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

# selection = aggrid_interactive_table(df=iris)

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
    content_range = basic_search["Content-Range"]
    st.info(
        f"""
        Total number of job offers this month\n
        {content_range['max_results']}
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
        delta=int(content_range["max_results"]) - 654321,
    )

# -------------------------------------------------------------------------------------------

# DRAW AN HISTOGRAM OF JOB OFFERS FOR EACH CATEGORY

# Prepare the dataframes for plotting 'barplots' for each filter categories
# What is the difference with Pandas' `df.where()`, like this:
# contract_type_df = filters_df.where(
#     [filters_df["filtre"] == "typeContrat"], inplace=True
# )
contract_type_df = filters_df[filters_df["filtre"] == "typeContrat"]
experience_df = filters_df[filters_df["filtre"] == "experience"]
qualification_df = filters_df[filters_df["filtre"] == "qualification"]
contract_nature_df = filters_df[filters_df["filtre"] == "natureContrat"]

# Merge the four filter types into a list (or tuple ?)
filters_list = (
    contract_type_df,
    experience_df,
    qualification_df,
    contract_nature_df,
)
for filter_var in filters_list:
    filters_barplot = (
        alt.Chart(filter_var, title="Total Number of Job Offers")
        .mark_bar()
        .encode(
            x=alt.X(
                "valeur_possible",
                axis=alt.Axis(title=f"{filter_var.iloc[0, 0]}"),
            ),
            y=alt.Y(
                "nb_resultats",
                axis=alt.Axis(title="Number of Job Offers"),
            ),
        )
        .configure_view(strokeWidth=0)
        .interactive()
    )
    st.altair_chart(filters_barplot, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------------------------------------

# CUSTOMISE THE SEARCH

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

    with right_column:
        start_time = st.time_input(label="Pick a Start Time")
        end_time = st.time_input(label="Pick an End Time")

    # Convert start/end date/time to 'datetime' format
    # No default start date used, hence, it will be the same as end date
    start_dt = datetime.datetime(
        year=start_date.year, month=start_date.month, day=start_date.day
    )
    # Merge start date and start time
    start_datetime = datetime.datetime.combine(start_dt, start_time)
    # Same as above
    end_dt = datetime.datetime(
        year=end_date.year, month=end_date.month, day=end_date.day
    )
    end_datetime = datetime.datetime.combine(end_date, end_time)

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
        "minCreationDate": dt_to_str_iso(start_datetime),
        "maxCreationDate": dt_to_str_iso(end_datetime),
    }
    search_date = client.search(params=parameters)

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
    column_list = [
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
    column_list.sort(reverse=False)
    # Change list name
    list_categories = {"Final list of categories": column_list}
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
    select_columns = st.multiselect(
        label="Select one or more categories", options=column_list
    )
    parameters = {
        "motsCles": key_words,
        "categories": select_columns,
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
    search_categories = client.search(params=parameters)

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
    #     options=column_list
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
