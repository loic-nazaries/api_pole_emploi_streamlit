"""API of Pole Emploi.

Specifically, an API to consult available job offers.

In this version, the username/secrets method input was changed.
Instead, secrets were created (see '.toml' file in '.streamlit' folder)
for connecting to the Web app. A new function 'def check_password()' was
written to perform this task.
As a consequence to this change, all the code BELOW was shifted by one indent.

Similarly, the API credentials were moved to the 'secrets.toml' file from the
'.env' file. As a consequence, the 'decouple' library in not needed any more.

FIXME Renaming the flattened 'langues', 'formations' and 'competences'
        variables is not working
TODO There is possibility to connect to different APIs when needed
        Hence, a 'st.selectbox()' component could be added
TODO Split the function 'def extract_search_content()'
        into THREE different functions
TODO Merge the custom search types into one ?
TODO Split app sections/steps into different files ?
        Hence, main file will be less complicated (and shorter)
TODO Similarly, remove the top of the page (API image) after logging in
TODO Remove the object 'You have successfully logged in.' after 2 seconds
TODO Edit code to change saving file location manually
TODO Better describe the sections and results
FIXME Fix the function 'drop_low_occurrence_categories'
TODO avoid hard-coding the categories (not elegant + prone to bugs)
FIXME IMPORTANT !!
        Fix the issue that top 150 hits is the limit for  search output
TODO Select a category and add a filter for numerical &
        non-numerical filters (using sliders and number inputs)
TODO Modify exception/error in date range to print out following message:
        st.error(
            '''If an error message appears below, it is likely that
            the start and end dates are the same.
            Please choose a range of at least ONE day.
            '''
        )
FIXME Fix code for displaying tabs (try update streamlit library)
TODO Write a snippet for subsetting filtered data (see 'lambda' functions)
FIXME Why is 'client.referentiel('metiers')' not working ?!
TODO Format numbers with a space between thousands
        => '{number:,}'.replace(',', ' ') is not working...
TODO In basic search (or sidebar ?), add a column next to
        'List of Categories' containing a definition of the categories;
        e.g. scroll down list ?
TODO And/or modify barplot layout to have definition of acronyms on right
            use st.columns() with 2/3-1/3 layout
FIXME The default minimum date cannot be set
TODO Change the x-axis label in barplots (experience, qualification)
TODO Correct column names for flattened
        'competences', 'formations' and 'qualitesPro'
TODO Set up email address or web client to report a bug
TODO Deploy app to Heroku or Streamlit Community + try Voila
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
# Disable warnings from deprecation
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

# Log-in section
# Check for user's name and  password
if cf.check_password():
    st.sidebar.success("You have successfully logged in.")
    # then, all code below should be indented

# -------------------------------------------------------------------------------------------

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
    # (client ID and secret from the secrets.toml file)
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

        # -------------------------------------------------------------------------------------------

        # DATA CLEANING

        # # Display the first raw result (.json file format)
        # st.subheader("Search Output Preview of First Hit")
        # search_preview = results[0]
        # search_preview

        # Convert the search content into a dataframe
        results_df = cf.convert_search_results_to_dataframe(
            search_results=results
        )

        st.subheader("Initial table of job offers")

        # Build a paginated html-styled table
        # This is how the function should be called, otherwise it won't work
        cf.convert_df_to_html_table(results_df)

        # Get the list of categories within the database
        category_list = cf.extract_search_categories(
            dataframe=results_df
        )
        # # Create a dictionary of the categories
        # category_dictionary =

        # # Display  above tasks on different tabs
        # # (default position would undeveloped - use 'st.expander' component)
        # # Below NOT working and get error:
        # # AttributeError: module 'streamlit' has no attribute 'tabs'
        # tab1, tab2, tab3 = st.tabs([
        #     "Job offers",
        #     "List of categories",
        #     "Definition of category values"  # or elsewhere like on sidebar?
        # ])
        # with tab1:
        #     st.subheader("Initial table of job offers")
        #     cf.convert_df_to_html_table(results_df)
        # with tab2:
        #     st.subheader("List of the categories in the database")
        #     category_list
        # with tab3:
        #     st.subheader("Dictionary of Categories (coming soon)")
        #     # category_dictionary

        # Variable 'lieuTravail.libelle'
        # Extract the words separated by a '-'
        results_df = cf.extract_linked_categories(
            dataframe=results_df,
            category_to_extract="lieuTravail.libelle",
            new_fields=["departement", "ville"],
        )

        # # Variable 'langues'
        # # st.write("langues")
        # # Extract the categories WITHIN the category
        # flattened_langues = cf.flatten_category(
        #     dataframe=results_df, category="langues"
        # )

        # # Rename automatically the categories previously extracted
        # flattened_langues = cf.rename_columns_auto(
        #     dataframe=flattened_langues,
        #     column_name="langues"
        # )

        # # Below NOT working
        # # Rename specific categories
        # flattened_langues = cf.rename_category(
        #     dataframe=flattened_langues,
        #     columns={
        #         "('langues 0',)": "langues_0",
        #         "('langues 1',)": "langues_1",
        #     },
        # )

        # Variable 'qualitesProfessionnelles'
        # st.write("qualitesProfessionnelles")
        flattened_qualitesPro = cf.flatten_category(
            dataframe=results_df, category="qualitesProfessionnelles"
        )

        flattened_qualitesPro = cf.rename_columns_auto(
            dataframe=flattened_qualitesPro,
            column_name="qualitesPro"
        )
        # Below NOT working
        flattened_qualitesPro = cf.rename_category(
            dataframe=flattened_qualitesPro,
            columns={
                "('qualitePro 0',)": "qualitePro_0",
                "('qualitePro 1',)": "qualitePro_1",
                "('qualitePro 2',)": "qualitePro_2",
            },
        )

        # Variable 'competences'
        # st.write("competences")
        flattened_competences = cf.flatten_category(
            dataframe=results_df, category="competences"
        )

        flattened_competences = cf.rename_columns_auto(
            dataframe=flattened_competences,
            column_name="competences"
        )
        # Keep top 3 competences
        flattened_competences = flattened_competences.iloc[:, 0:3]
        # Below NOT working
        flattened_competences = cf.rename_category(
            dataframe=flattened_competences,
            columns={
                "('competences 0',)": "competences_0",
                "('competences 1',)": "competences_1",
                "('competences 2',)": "competences_2",
            },
        )

        # Variable 'permis'  # to be (re)done
        # st.write("permis")
        flattened_permis = cf.flatten_category(
            dataframe=results_df, category="permis"
        )

        flattened_permis = cf.rename_category(
            flattened_permis, columns={0: "permis"}
        )

        # Variable 'formations'
        # st.write("formations")
        flattened_formations = cf.flatten_category(
            dataframe=results_df, category="formations"
        )

        flattened_formations = cf.rename_columns_auto(
            dataframe=flattened_formations,
            column_name="formations"
        )
        # Below NOT working
        flattened_formations = cf.rename_category(
            dataframe=flattened_formations,
            columns={
                "('formations 0',)": "formations_0",
                "('formations 1',)": "formations_1",
            },
        )

        # Concatenate flattened categories
        # Note: 'id' column was added to apply the '.merge()' function later on
        flattened_categories = [
            results_df["id"],
            # flattened_langues,
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
        # results_df_merged

        # Without calling a custom function
        # Also rename de 'permis_y' variable
        results_df_merged = pd.merge(
            results_df, flattened_categories, how="left", on="id"
        ).rename(columns={"permis_y": "permis"})

        # Display percentage of missing data in a table
        nan_table = cf.create_missing_data_table(
            # dataframe=results_df_merged,  # NOT working
            dataframe=results_df
        )
        # nan_table

        # Prepare summary table of missing data based on missing data threshold
        # and/or chosen variables
        # # a menu with all categories is displayed, and user 'unticks'
        # # the unwanted values (see next section too)
        # st.multiselect(
        #     label="Deselect variables with a high number of missing values",
        #     options=results_df_final.columns
        # )

        # def drop_low_occurrence_categories(
        #     dataframe: pd.DataFrame, threshold: int = 50
        # ) -> pd.DataFrame:
        #     """Delete unnecessary columns with > 50% missing data per column

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
        # # st.write("Delete columns with more than 10% of missing values")
        # results_df_final_redux = drop_low_occurrence_categories(
        #     dataframe=results_df_final,
        #     threshold=10,
        # )
        # results_df_final_redux
        # AgGrid(results_df_final_redux)

        # Since above code not working, dropping unnecessary manually
        category_drop = [
            "qualitesProfessionnelles",
            "competences",
            "permis",
            "permis_x",
            "formations",
            # "('formations 0',)",
            # "('formations 1',)",
            "contact.commentaire",
            "salaire.complement2",
            "contact.telephone",
            "experienceCommentaire",
            "contact.coordonnees3",
            "contact.coordonnees2",
            "langues",
            # "('langues 0',)",
            # "('langues 1',)",
            "salaire.commentaire",
            "deplacementCode",
            "formations",
            "deplacementLibelle",
            "salaire.complement1",
            "entreprise.logo",
            "contact.courriel",
            "entreprise.url",
            "entreprise.description",
            "contact.nom",
            "contact.urlPostulation",
            "agence.courriel",
            "complementExercice",
        ]

        # Drop categories not needed or redundant
        results_df_redux = cf.drop_categories(
            dataframe=results_df_merged, drop_list=category_drop,
        )

        # Display missing values status for each column in a matrix
        missing_data_matrix = cf.create_missing_data_matrix(
            dataframe=results_df_redux
        )

        # # Below NOT working
        # nan_table = cf.create_missing_data_table(
        #     dataframe=results_df_redux  # same issue as 1st nan table
        # )
        # nan_table

        # Extract column names into a dataframe
        category_list = cf.extract_search_categories(
            dataframe=results_df_redux
        )

        # Display table and matrix of missing data next to each other
        left_column, right_column = st.columns(2)
        with left_column:
            # Build a paginated html-styled table
            st.subheader("List of the categories in the database")
            cf.convert_df_to_html_table(
                dataframe=category_list,
                use_checkbox=False,
            )
        with right_column:
            st.subheader("Table of missing values in each category")
            nan_table

        st.subheader("Summary of Missing Data")
        st.pyplot(missing_data_matrix.figure)

        st.subheader("Table of job offers")
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

        # --------------------------------------------------------------------------------------------

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
            # content_range = basic_search["Content-Range"]
            st.info(
                f"""
                Total number of job offers this month\n
                {content_max}
                """
            )

        # Add a metric of the change in job offer number since previous month
        # i.e. use the non-working snippet below:
        # default_start_date = (
        #     date.today() - relativedelta.relativedelta(months=1)
        # )
        with right_column:
            st.metric(
                label="Number of job offers since previous month",
                value=654321,
                # value=past_month_offers,  # 'past_month_offers' to be coded
                # delta=12345,
                delta=int(content_max) - 654321,
            )

        # -------------------------------------------------------------------------------------------

        # DRAW AN HISTOGRAM OF JOB OFFERS FOR EACH CATEGORY

        filter_names = [
            "typeContrat",
            "experience",
            "qualification",
            "natureContrat"
        ]

        # def apply_filter(dataframe=filters_df):
        #     for _ in filter_names:
        #         filters_df = filter_categories(
        #             dataframe=filters_df, filter_name="typeContrat"
        #     )

        # add loop (see above)
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

    # --------------------------------------------------------------------------------------------

    # CUSTOMISE THE SEARCH

    if search_type == "Search based on dates and keywords":
        st.subheader("Search based on dates and keywords")

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
        # Hence 'default_start_date' is set to SEVEN SAYS prior to today's date
        default_start_date = (
            date.today() + relativedelta.relativedelta(days=-7)
        )
        st.write(f"Start Date should be {default_start_date}...")

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

    # -------------------------------------------------------------------------------------------

    elif search_type == "Search based on values in categories":
        st.subheader("Search based on values in categories")

        # # Below NOT working
        # # NameError: name 'results_df_redux' is not defined
        # category_list = cf.extract_search_categories(
        #     dataframe=results_df_redux
        # )
        # category_list

        # IMPORTANT: could not worked out yet how to isolate the column names,
        # hence they were hard-coded below
        # use columns of the concatenated list of flattened variables instead ?
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
        category_list = [dict_category_names.get(n, n) for n in category_list]

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
        key_words

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
        st.write(f"Total number of job offers: {content_range['max_results']}")

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
            cf.convert_df_to_html_table(dataframe=salary_by_enterprise_dropna)
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
