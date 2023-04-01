import streamlit as st
import streamlit.components.v1 as components
import random
import pandas
from datetime import datetime
from time import time

# -------------- app config ---------------

st.set_page_config(page_title="Learn with Flashcards", page_icon="🚀")
RESULT_COLUMNS = ["No", "Epoch Time", "Correct"]

# ---------------- functions ----------------


# external css
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# callbacks
def callback():
    st.session_state.button_clicked = True


def callback2():
    st.session_state.button2_clicked = True


def set_correct(correct: bool) -> None:
    new_row = pandas.DataFrame(
        [(st.session_state.q_no_temp, int(time()), correct)], columns=RESULT_COLUMNS
    )
    st.session_state.results = pandas.concat([st.session_state.results, new_row])


@st.cache_data
def convert_results(results):
    return results.to_csv(index=False).encode("utf-8")


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.write("**Streamlit app originally created by:**")
    st.caption("Tomasz Hasiów | https://tomjohn.streamlit.app/")
    st.write("**Adapted for your questions by:**")
    st.caption("Juan Montero de Espinosa Reina | https://github.com/jmonteroers")
    # Load the data with questions/answers
    rows = st.file_uploader("**Upload your question/answer dataframe**")
    if rows:
        rows = pandas.read_csv(rows)
    else:
        rows = pandas.DataFrame(columns=["No", "Topic", "Question", "Answer"])

    # Load previous results
    results = st.file_uploader("**Upload previous results ('No' must match)**")
    default_results = (
        "results" in st.session_state and len(st.session_state.results) == 0
    )
    if results and default_results:
        st.session_state.results = pandas.read_csv(results)

    # Download results
    if "results" in st.session_state:
        csv = convert_results(st.session_state.results)
        st.download_button(
            "Download (CSV)", csv, file_name="results.csv", mime="text/csv"
        )

# ---------------- CSS ----------------

local_css("style.css")

# ---------------- SESSION STATE ----------------

if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False

if "button2_clicked" not in st.session_state:
    st.session_state.button2_clicked = False

if "q_no" not in st.session_state:
    st.session_state.q_no = 0

if "q_no_temp" not in st.session_state:
    st.session_state.q_no_temp = 0

if "results" not in st.session_state:
    st.session_state.results = pandas.DataFrame(columns=RESULT_COLUMNS)

print(f"{datetime.now()}: {st.session_state.results}")

# ---------------- Main page ----------------

tab1, tab2 = st.tabs(["Flashcards", "Search engine"])

with tab1:
    # st.title("Product Owner Interview Questions Flashcards")
    no = len(rows)
    st.caption("Currently we have " + str(no) + " questions in the database")

    # ---------------- Questions & answers logic ----------------

    col1, col2 = st.columns(2)
    with col1:
        question = st.button(
            "Draw question", on_click=callback, key="Draw", use_container_width=True
        )
    with col2:
        answer = st.button(
            "Show answer", on_click=callback2, key="Answer", use_container_width=True
        )

    if question or st.session_state.button_clicked:
        # randomly select question number
        st.session_state.q_no = random.randint(0, no - 1)

        # this 'if' checks if algorithm should use value from temp or new value (temp assigment in else)
        if st.session_state.button2_clicked:
            st.markdown(
                f'<div class="blockquote-wrapper"><div class="blockquote"><h1><span style="color:#ffffff">{rows.iloc[st.session_state.q_no_temp].Question}</span></h1><h4>&mdash; Question no. {st.session_state.q_no_temp+1}</em></h4></div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="blockquote-wrapper"><div class="blockquote"><h1><span style="color:#ffffff">{rows.iloc[st.session_state.q_no].Question}</span></h1><h4>&mdash; Question no. {st.session_state.q_no+1}</em></h4></div></div>',
                unsafe_allow_html=True,
            )
            # keep memory of question number in order to show answer
            st.session_state.q_no_temp = st.session_state.q_no

        if answer:
            st.markdown(
                f"<div class='answer'><span style='font-weight: bold; color:#6d7284;'>Answer to question number {st.session_state.q_no_temp+1}</span><br><br>{rows.iloc[st.session_state.q_no_temp].Answer}</div>",
                unsafe_allow_html=True,
            )
            downcol1, downcol2 = st.columns(2)
            with downcol1:
                st.button(
                    "Easy",
                    on_click=lambda: set_correct(True),
                    use_container_width=True,
                )
            with downcol2:
                st.button(
                    "Hard",
                    on_click=lambda: set_correct(False),
                    use_container_width=True,
                )
            st.session_state.button2_clicked = False

    # this part normally should be on top however st.markdown always adds divs even it is rendering non visible parts?

    st.markdown(
        '<div><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Barlow+Condensed&family=Cabin&display=swap" rel="stylesheet"></div>',
        unsafe_allow_html=True,
    )

with tab2:
    df = pandas.DataFrame(rows)

    # Use a text_input to get the keywords to filter the dataframe
    text_search = st.text_input("Search in titles, questions and answers", value="")

    # Filter the dataframe using masks
    m1 = df["Topic"].str.contains(text_search)
    m2 = df["Question"].str.contains(text_search)
    m3 = df["Answer"].str.contains(text_search)
    df_search = df[m1 | m2 | m3]

    # Another way to show the filtered results
    # Show the cards
    N_cards_per_row = 2
    if text_search:
        for n_row, row in df_search.reset_index().iterrows():
            i = n_row % N_cards_per_row
            if i == 0:
                st.write("---")
                cols = st.columns(N_cards_per_row, gap="large")
            # draw the card
            with cols[n_row % N_cards_per_row]:
                st.caption(f"Question {row['No']:0.0f}")
                st.caption(f"{row['Topic'].strip()}")
                st.markdown(f"**{row['Question'].strip()}**")
                st.markdown(f"{row['Answer'].strip()}")
                # with st.expander("Answer"):
                #     st.markdown(f"*{row['Answer'].strip()}*")
