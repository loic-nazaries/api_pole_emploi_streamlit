"""API of Pôle Emploi.

Specifically, an API to consult available job offers.

In this version, the username/secrets method input was changed.
Instead, secrets were created (see '.toml' file in '.streamlit' folder)
for connecting to the Web app. A new function 'def check_password()' was
written to perform this task.
As a consequence to this change, all the code BELOW was shifted by one indent.

Similarly, the API credentials were moved to the 'secrets.toml' file from the
'.env' file. As a consequence, the 'decouple' library in not needed any more.

Tabs coded previously are now active (an update was necessary)

A function to remove the categories with high number of missing values was
created to avoid hard-coding these categories list. There are now no bugs when
categories had to be deleted manually from the list.

BUG IMPORTANT !!
        'Search based on dates and keywords' section does NOT work any more !!
TODO Better describe the sections and results
BUG The default minimum date cannot be set
TODO Deploy app to Heroku or Streamlit Community + try Voila
FIXME IMPORTANT !!
        Fix the issue that top 150 hits is the limit for search output
TODO Merge the custom search types into one ?
        if so, using a date range should not be compulsory
TODO Split app sections/steps into different files ?
        Hence, main file will be less complicated (and shorter)
        See new Streamlit functionality for displaying multiple pages
TODO Avoid hard-coding the categories (not elegant + prone to bugs)
        When the 'results_df_redux' is called in the 'if' loop of the
        'Search based on values in categories' section, an error message
        appears:
            '''NameError: name 'results_df_redux' is not defined'''
        This is because 'results_df_redux' was created in a different loop
TODO Select a category and add a filter for numerical &
        non-numerical filters (using sliders and number inputs)
BUG It is not possible to build a table of missing data ('nan_table') with
        the 'results_df_merged' dataframe.
        Getting below error message:
            '''StreamlitAPIException: ('cannot mix list and non-list, non-null
            values', 'Conversion failed for column None with type object')'''
BUG Renaming the flattened 'langues', 'formations' and 'competences'
        variables is not working
TODO Get last week's number of job offers
        (use search_categories["Content-Range"] ?)
TODO Write a snippet for subsetting filtered data (see 'lambda' functions)
TODO Format numbers with a space between thousands
        => '{number:,}'.replace(',', ' ') is not working...
TODO Remove the object 'You have successfully logged in.' after 2 seconds
TODO Similarly, remove the top of the page (API image) after logging in
TODO Modify exception/error (using 'assert' ?) in the date range to print out
        the following message:
            st.error(
                '''If an error message appears below, it is likely that
                the start and end dates are the same.
                Please choose a range of at least ONE day.
                '''
            )
BUG Why is 'client.referentiel('metiers')' not working ?!
TODO Set up email address or web client to report a bug
XXX Not possible to change the names of x-axis label in barplots (or elsewhere)
        as the definition of the acronyms is not provided by Pôle Emploi
"""

from datetime import date
from dateutil import relativedelta
from offres_emploi import Api
from offres_emploi.utils import dt_to_str_iso, filters_to_df
from st_aggrid import AgGrid
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
import time
import custom_functions as cf

# -------------------------------------------------------------------------------------------

# SET-UP THE APP

# Initial page config
st.set_page_config(
    page_title="API Pôle Emploi",
    page_icon="./images/epsilon_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Loïc Nazaries was here!",
        "Get help": "https://docs.streamlit.io/library/api-reference",
        # "Report a Bug": "lnazaries@epsilon-alcen.com",
    },
)

# Change the default font ?
st.write(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family:Fascinate'
    );

    html, body, [class*="css"] {
        font-family:'Fascinate' cursive;
    }
    <style>
    """,
    unsafe_allow_html=True
)

# Other default settings
# Disable warnings from deprecation
st.set_option('deprecation.showPyplotGlobalUse', False)
# pd.set_option("precision", 2)  # display floats with 2 decimal places

# Display Epsilon logo
st.sidebar.image("./images/epsilon_logo.png")

# App title
st.title("API de Pôle Emploi")

# Show Pôle Emploi API log-in image
st.image("./images/api_pe_account.png")

# There is possibility to connect to different APIs when needed
api_list = [
    "Offres d'emploi v2",
    "Anotéa",
    "Pôle emploi Connect",
]

# Log-in section
# Check for user's name and  password
if cf.check_password():
    st.sidebar.success("You have successfully logged in.")

    st.sidebar.selectbox(label="Choose an API", options=api_list)

    st.write(
        """
        Click
        [here](https:/pole-emploi.io/data/api, "Pôle emploi API catalog")
        to access the **Pôle emploi API catalog**.
        """
    )

# # Add a 'st.selectbox()' to access different API analyses
# # Below does not seem to work, even when adding an indent to the rest of the
# # code below the 'START DATA ANALYSIS' section
# if api_list == "Offres d'emploi v2":
#     st.header(
#         "Recherche d'offres d'emploi avec l'API '**Offres d'emploi v2'**"
#     )
#     # Add link to API page
#     st.write(
#         """
#         Click
#         [here](
#             https:/pole-emploi.io/data/api/offres-emploi,
#             "Offres d'emploi v2** API page"
#         )
#         to access the **Offres d'emploi v2 API page**.
#         """
#     )

# ----------------------------------------------------------------------------

# START DATA ANALYSIS

    st.header("Choose a type of analysis from the left-side panel")

    # Analysis options
    customised_search = (
        "Default analysis",
        "Search based on dates and keywords",
        "Search based on values in categories",
    )
    st.sidebar.subheader("Customised Search")
    search_type = st.sidebar.selectbox(
        label="Pick a Type of Analysis", options=customised_search
    )

    # Call API client using the token details provided
    # (client ID and secret from the 'secrets.toml' file)
    client = Api(
        client_id=st.secrets["passwords"]["API_PE_CLIENT"],
        client_secret=st.secrets["passwords"]["API_PE_SECRET"],
    )

    if search_type == "Default analysis":
        st.subheader("Default analysis")

        # Search the client's API
        basic_search = cf.start_search(api_client=client)

        # Tuple unpacking of search content
        (results, filters, content_range) = cf.extract_search_content(
            search_session=basic_search
        )

        # Get total number of lines
        content_max = cf.display_max_content(
            content_range=content_range)

        st.write(f"Total number of job offers: {content_max}")

        # --------------------------------------------------------------------

        # DATA CLEANING

        # # Display the first raw result (.json file format)
        # st.subheader("Search Output Preview of First Hit")
        # search_preview = results[0]
        # search_preview

        # Convert the search content into a dataframe
        results_df = cf.convert_search_results_to_dataframe(
            search_results=results
        )

        # Variable 'lieuTravail.libelle'
        # Extract the words separated by a '-'
        results_df = cf.extract_linked_categories(
            dataframe=results_df,
            category_to_extract="lieuTravail.libelle",
            new_fields=["departement", "ville"],
        )
        # 'flattened_lieuTravail' variable is to be coded using above and
        # below function structures so merging will work without the duplicate
        # error message

        # Variable 'langues'
        # Extract the categories WITHIN the category
        flattened_langues = cf.flatten_category(
            dataframe=results_df, category="langues"
        )

        # Rename automatically the categories previously extracted
        flattened_langues = cf.rename_columns_auto(
            dataframe=flattened_langues,
            column_name="langues"
        )

        # # Rename specific categories
        # # Below NOT working
        # flattened_langues = cf.rename_category(
        #     dataframe=flattened_langues,
        #     columns={
        #         "('langues 0',)": "langues_0",
        #         "('langues 1',)": "langues_1",
        #     },
        # )

        # Variable 'qualitesProfessionnelles'
        flattened_qualitesPro = cf.flatten_category(
            dataframe=results_df, category="qualitesProfessionnelles"
        )

        flattened_qualitesPro = cf.rename_columns_auto(
            dataframe=flattened_qualitesPro,
            column_name="qualitesPro"
        )

        # # Below NOT working
        # flattened_qualitesPro = cf.rename_category(
        #     dataframe=flattened_qualitesPro,
        #     columns={
        #         "('qualitePro 0',)": "qualitePro_0",
        #         "('qualitePro 1',)": "qualitePro_1",
        #         "('qualitePro 2',)": "qualitePro_2",
        #     },
        # )

        # Variable 'competences'
        flattened_competences = cf.flatten_category(
            dataframe=results_df, category="competences"
        )

        flattened_competences = cf.rename_columns_auto(
            dataframe=flattened_competences,
            column_name="competences"
        )

        # Keep top 3 competences
        flattened_competences = flattened_competences.iloc[:, 0:3]

        # # Below NOT working
        # flattened_competences = cf.rename_category(
        #     dataframe=flattened_competences,
        #     columns={
        #         "('competences 0',)": "competences_0",
        #         "('competences 1',)": "competences_1",
        #         "('competences 2',)": "competences_2",
        #     },
        # )

        # Variable 'permis'
        flattened_permis = cf.flatten_category(
            dataframe=results_df, category="permis"
        )

        flattened_permis = cf.rename_columns_auto(
            dataframe=flattened_permis,
            column_name="permis"
        )

        # # Below NOT working
        # flattened_permis = cf.rename_category(
        #     flattened_permis, columns={
        #         0: "permis_0",
        #         1: "permis_1"
        #     }
        # )

        # Variable 'formations'
        flattened_formations = cf.flatten_category(
            dataframe=results_df, category="formations"
        )

        flattened_formations = cf.rename_columns_auto(
            dataframe=flattened_formations,
            column_name="formations"
        )

        # # Below NOT working
        # flattened_formations = cf.rename_category(
        #     dataframe=flattened_formations,
        #     columns={
        #         "('formations 0',)": "formations_0",
        #         "('formations 1',)": "formations_1",
        #     },
        # )

        # Concatenate flattened categories
        # Note: 'id' column was added to apply the '.merge()' function later on
        flattened_categories = [
            results_df["id"],
            # flattened_lieuTravail,
            flattened_langues,
            flattened_qualitesPro,
            flattened_competences,
            flattened_permis,
            flattened_formations,
        ]
        flattened_categories = cf.concatenate_dataframes(
            column_list=flattened_categories
        )

        # Merge initial 'results_df' with flattened categories
        # Use a custom function
        # Below NOT working
        results_df_merged = cf.merge_dataframes(
            results_df, flattened_categories, on="id"
        )
        # Use the 'left cache' method to delete 'permis_x' after merge
        # # Also rename de 'permis_y' variable
        # .rename(columns={"permis_y": "permis"})
        results_df_merged

        # Display percentage of missing data in a table
        nan_table = cf.create_missing_data_table(
            # dataframe=results_df_merged,  # NOT working so using initial data
            dataframe=results_df
        )

        # # Create a dictionary of the categories
        # category_dictionary =

        # Display over 3 tabs the main information from the database
        tab1, tab2, tab3 = st.tabs(
            [
                "Job offers",
                "Table of missing values in each category",
                "Definition of category names and values"  # or on sidebar?
            ]
        )
        with tab1:
            st.subheader("Initial table of job offers")
            # Build a paginated html-styled table
            # It is how the function should be called, otherwise it won't work
            cf.convert_df_to_html_table(results_df, key=2)
        with tab2:
            st.subheader("Table of missing values in each category")
            nan_table
        with tab3:
            st.subheader("Dictionary of Categories")
            st.write("Coming Soon!")
            # category_dictionary

        st.subheader("Summary of Missing Data")

        # Detect columns with a high number of missing values
        low_category_list = cf.detect_low_occurrence_categories(
            dataframe=nan_table,
            threshold=20,
        )

        # Drop categories not needed or redundant
        results_df_redux = cf.drop_categories(
            dataframe=results_df_merged, drop_list=low_category_list,
        )

        # Display missing values status for each column in a matrix
        missing_data_matrix = cf.create_missing_data_matrix(
            dataframe=results_df_redux
        )

        # Below NOT working as some flattened columns are not deleted although
        # their missing data are higher than the threshold value
        # The reason is that the 'nan_table' did not work with
        # 'results_df_redux' and 'results_df' was used instead
        st.pyplot(missing_data_matrix.figure)

        st.subheader("Table of job offers (cleaned)")
        results_df_redux
        # AgGrid(results_df_redux)  # NOT working
        # cf.convert_df_to_html_table(results_df_redux)  # NOT working

        # The total number must be fixed with regards to total number of pages,
        # not the first 150 entries as it is now
        st.write(f"Total number of job offers: {len(results_df_redux)}")

        # Save the search output
        save_output = cf.save_output_file(
            dataframe=results_df_redux,
            file_name="table_job_offer.csv"
        )
        if save_output:
            with st.spinner(text="Saving..."):
                time.sleep(1)
            st.success("File saved.")

        st.markdown("---")

        # --------------------------------------------------------------------

        # BUILD A METRIC DASHBOARD

        st.subheader("Number of Hits for Each Job Offer Filter")

        filters_df = filters_to_df(filters)
        cf.convert_df_to_html_table(
            dataframe=filters_df,
            use_checkbox=False,
        )

        # Get the number of hits from the search
        left_column, right_column = st.columns(2)
        with left_column:
            st.info(
                f"""
                Total number of job offers today\n
                {content_max}
                """
            )

        # Add a metric of the change in job offer number since previous week
        # i.e. use the non-working snippet below:
        default_start_date = (
            date.today() - relativedelta.relativedelta(days=7)
        )
        default_start_date

        # # Get last week's number of job offers
        # # (use search_categories["Content-Range"] ?)
        # past_week_offers =

        with right_column:
            st.metric(
                label="Number of job offers since previous week",
                value=654321,
                # value=past_week_offers,  # 'past_week_offers' to be coded
                # delta=12345,
                delta=int(content_max) - 654321,
            )

        # --------------------------------------------------------------------

        # DRAW AN HISTOGRAM OF JOB OFFERS FOR EACH CATEGORY

        filter_names = [
            "typeContrat",
            "experience",
            "qualification",
            "natureContrat"
        ]

        contract_type_df = cf.filter_categories(
            dataframe=filters_df, filter_name="typeContrat"
        )
        experience_df = cf.filter_categories(
            dataframe=filters_df, filter_name="experience"
        )
        qualification_df = cf.filter_categories(
            dataframe=filters_df, filter_name="qualification"
        )
        contract_nature_df = cf.filter_categories(
            dataframe=filters_df, filter_name="natureContrat"
        )

        filters_list = (
            contract_type_df,
            experience_df,
            qualification_df,
            contract_nature_df,
        )

        for filter_var in filters_list:
            filters_barplot = cf.create_barplot(filter_var)
            st.altair_chart(filters_barplot, use_container_width=True)

    # ------------------------------------------------------------------------

    # CUSTOMISE THE SEARCH

    elif search_type == "Search based on dates and keywords":
        st.subheader("Search based on dates and keywords")

        ############################################
        #  This section does NOT work any more !!  #
        ############################################

        # Display error message in case the date range is not of at least 1 day
        st.error(
            """
            Please choose a date range of at least ONE day.
            """
        )
        # Custom settings
        # Set a default date to avoid error message when loading the page
        # as the date menu will ask for 'maxCreationDate ' superior to
        # 'minCreationDate '
        # Hence 'default_start_date' is set to SEVEN DAYS prior to today's date
        default_start_date = (
            date.today() - relativedelta.relativedelta(days=7)
        )

        st.warning(
            f"""
            Bug: Default Start Date should be SEVEN (7) days BEFORE the
            current (end) date, i.e the {default_start_date}.
            """
        )

        # 'default_start_date' does NOT work with 'min_value' below
        left_column, right_column = st.columns(2)
        with left_column:
            start_date = st.date_input(
                label="Pick a Start Date", min_value=default_start_date
            )
            # start_time = st.time_input(label="Pick a Start Time")

        with right_column:
            end_date = st.date_input(label="Pick an End Date")
            # end_time = st.time_input(label="Pick an End Time")

        # Set-up the search parameters
        key_words = st.text_input(
            label="Enter One or More Keywords, e.g. data analyst, bi"
        )

        # Pass on the parameters of the search
        parameters = {
            "motsCles": key_words,
            "minCreationDate": dt_to_str_iso(start_date),
            "maxCreationDate": dt_to_str_iso(end_date),
        }
        search_date = cf.start_search(
            api_client=client, params=parameters
        )

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
        AgGrid(filters_df)

        # Save the search output
        save_output = cf.save_output_file(
            dataframe=filters_df,
            file_name="filter_output.csv"
        )
        if save_output:
            # Below NOT working
            with st.spinner(text="Saving..."):
                time.sleep()
            st.success("File saved.")

    # ------------------------------------------------------------------------

    elif search_type == "Search based on values in categories":
        st.subheader("Search based on values in categories")

        # # Below NOT working
        # # NameError: name 'results_df_redux' is not defined
        # category_list = cf.extract_search_categories(
        #     dataframe=results_df_redux
        # )
        # category_list

        # IMPORTANT: could not worked out yet how to isolate the column names
        # from above, hence they were hard-coded below
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

        # Rename items in the list
        dict_category_names = {
            "appellationlibelle": "romeAppellation",
            "accessibleTH": "accessibleTauxHoraire",
            "origineOffre": "publicationOffre",
            "deplacementCode": "deplacementPossibleCode",
            "deplacementLibelle": "deplacementPossibleLibelle",
        }
        category_list = [dict_category_names.get(
            n, n) for n in category_list]

        # Sort list of categories and change column name
        category_list.sort(reverse=False)

        # Change list name
        list_categories = {"Final list of categories": category_list}

        # Display list of categories on the left-side panel
        st.sidebar.dataframe(list_categories)  # delete ?

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

        # Input key words
        key_words = st.text_input(
            label="Enter One or More Keywords, e.g. data analyst, bi"
        )

        # Select/deselect categories
        # Click a button to clear the selected categories
        container = st.container()
        clear_categories = st.button(label="Clear categories")
        # All options are selected by default (no click of button)
        if not clear_categories:
            selected_categories = container.multiselect(
                label="Select/Deselect one or more categories",
                options=category_list,
                default=category_list,
            )
        # The selected categories are cleared when clicking the button
        else:
            selected_categories = container.multiselect(
                label="Select/Deselect one or more categories",
                options=category_list,
            )
        # There is a bug as when clearing the categories and selecting more
        # than one back, all categories are automatically re-selected

        # Merge search parameters
        # # Use coded objects above
        # parameters = {
        #     "motsCles": key_words,
        #     "categories": selected_categories,
        # }
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

        search_categories = cf.start_search(
            api_client=client, params=parameters
        )

        # Prepare search results
        results = search_categories["resultats"]

        # Transform results list into a dataframe
        st.subheader("Summary Table")

        # Get the number of hits from the search
        content_range = search_categories["Content-Range"]
        st.write(
            f"Total number of job offers: {content_range['max_results']}")

        results_df_from_categories = pd.DataFrame(results)
        cf.convert_df_to_html_table(dataframe=results_df_from_categories)

        # Save the search output
        save_output = cf.save_output_file(
            dataframe=results_df_from_categories,
            file_name="search_category_output.csv"
        )
        if save_output:
            with st.spinner(text="Saving..."):
                time.sleep(1)
            st.success("File saved.")

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

        # Delete and/or merge code snippet below with subsetting snippet
        # Also, all columns should be flattened out
        # Use hard-coded parameters for now
        filtered_results = pd.DataFrame(results)[
            ["id", "entreprise", "salaire"]
        ]

        # Custom filters
        # Filter a category based on  a value
        # filter_category = st.multiselect(
        #     label="Choose filters to apply",
        #     options=category_list
        #     )

        # Select enterprise name from `nom` column & salary from `libelle` col
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

        # Re-insert the 'id_offre' series to the 'salary_by_enterprise' df
        salary_by_enterprise.insert(0, "id", id_offre)

        # Drop the rows with missing data
        salary_by_enterprise_dropna = salary_by_enterprise.dropna()

        # Below needs refactoring !
        # Tick a box to remove missing data from the dataframe
        remove_missing_data = st.checkbox(
            label="Remove missing data",
            value=False
        )
        if remove_missing_data:
            st.write(
                f"""
                Final number of job offers after removing missing data:
                    {len(salary_by_enterprise_dropna)}
                """
            )
            cf.convert_df_to_html_table(
                dataframe=salary_by_enterprise_dropna)
        else:
            st.write(
                f"""
                Final number of job offers after removing missing data:
                    {len(salary_by_enterprise)}
                """
            )
            cf.convert_df_to_html_table(dataframe=salary_by_enterprise)

        # Save the search output
        save_output = cf.save_output_file(
            dataframe=salary_by_enterprise,
            file_name="salary_by_enterprise.csv"
        )
        if save_output:
            with st.spinner(text="Saving..."):
                time.sleep(1)
            st.success("File saved.")


# # NOT working
# # Access job type (referentiel)
# referentiel_metiers = client.referentiel("metiers")
# referentiel_metiers
