import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
from datetime import datetime
from time import time

# -------------- app config ---------------

st.set_page_config(page_title="Learn with Flashcards", page_icon="🚀")
RESULT_COLUMNS = ["No", "Epoch Time", "Correct", "Question"]
N_PREV = 2

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
    new_row = pd.DataFrame(
        [(st.session_state.q_no_temp, int(time()), correct, None)],
        columns=RESULT_COLUMNS,
    )
    st.session_state.results = pd.concat(
        [st.session_state.results, new_row], ignore_index=True
    )


@st.cache_data
def convert_results(results):
    if len(results):
        if "Question" in results.columns:
            results.drop(columns=["Question"], inplace=True)
        results = results.merge(
            rows.reset_index()[["No", "Question"]],
            on="No",
            how="left",
        )
        st.session_state.results = results
    return results.to_csv(index=False).encode("utf-8")


@st.cache_data
def get_weights(results) -> pd.Series:
    def get_unstd_weight_by_question(res) -> float:
        """Get some sort of probability of not getting it right"""
        n_correct = res["Correct"].sum()
        return 1.0 - (N_PREV / 2 + n_correct) / (N_PREV + len(res))

    unstd_weight = results.groupby(["No"]).apply(get_unstd_weight_by_question)
    # fill in words with no weights
    unstd_weight = unstd_weight.reset_index()
    unstd_weight.columns = ["No", "Weight"]
    unstd_weight = unstd_weight.merge(
        st.session_state.questions, on=["No"], how="right"
    )
    unstd_weight.set_index("No", inplace=True)
    unstd_weight = unstd_weight["Weight"].fillna(0.5)
    weights = unstd_weight / unstd_weight.sum()
    return weights


if (
    "results" in st.session_state
    and len(st.session_state.results)
    and "questions" in st.session_state
    and len(st.session_state.questions)
):
    results = st.session_state.results
    sample_weights = get_weights(results)
else:
    sample_weights = None

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.write("**Streamlit app originally created by:**")
    st.caption("Tomasz Hasiów | https://tomjohn.streamlit.app/")
    st.write("**Adapted for your questions by:**")
    st.caption("Juan Montero de Espinosa Reina | https://github.com/jmonteroers")
    # Load the data with questions/answers
    rows = st.file_uploader("**Upload your question/answers**")
    if rows:
        rows = pd.read_csv(rows)
        rows.rename(
            columns={
                st.session_state.headers["answer"]: "Answer",
                st.session_state.headers["question"]: "Question",
                st.session_state.headers["index"]: "No",
            },
            inplace=True,
        )
        # uncomment to test images
        # rows.dropna(subset=["Image"], inplace=True)
        rows.set_index("No", inplace=True)
    else:
        rows = pd.DataFrame(columns=["No", "Topic", "Question", "Answer"])
    st.session_state.questions = rows


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
    st.session_state.results = pd.DataFrame(columns=RESULT_COLUMNS)

if "questions" not in st.session_state:
    st.session_state.questions = pd.DataFrame(
        columns=["No", "Topic", "Question", "Answer"]
    )

if "headers" not in st.session_state:
    st.session_state.headers = {
        "index": "Index",
        "question": "Word",
        "answer": "Explanation",
    }

# print(f"{datetime.now()}: {st.session_state.results.head()}")

# ---------------- Main page ----------------

tab_cards, tab_search, tab_headers, tab_results = st.tabs(
    [
        "Flashcards",
        "Search engine",
        "Headers",
        "Results",
    ]
)

with tab_headers:
    st.session_state.headers["index"] = st.text_input(
        "Index", value=st.session_state.headers["index"]
    )
    st.session_state.headers["question"] = st.text_input(
        "Question",
        value=st.session_state.headers["question"],
    )
    st.session_state.headers["answer"] = st.text_input(
        "Answer",
        value=st.session_state.headers["answer"],
    )

with tab_cards:
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
        st.session_state.q_no = rows.sample(weights=sample_weights).index.values[0]
        # this 'if' checks if algorithm should use value from temp or new value (temp assigment in else)
        if st.session_state.button2_clicked:
            question_number = st.session_state.q_no_temp
        else:
            question_number = st.session_state.q_no
            # keep memory of question number in order to show answer
            st.session_state.q_no_temp = st.session_state.q_no
        st.markdown(
            '<div class="blockquote-wrapper"><div class="blockquote"><h1><span style="color:#ffffff">'
            + rows.loc[question_number, "Question"]
            + f"</span></h1><h4>&mdash; Question no. {question_number}</em></h4></div></div>",
            unsafe_allow_html=True,
        )
        if answer:
            # add image using link if available
            if "Image" in rows.columns:
                image_link = rows.loc[question_number, "Image"]
                print(image_link)
                if image_link and not pd.isna(image_link):
                    image_html = f'<br><img src="{rows.loc[question_number, "Image"]}" class="center" alt="Image" >'
                else:
                    image_html = ""
            else:
                image_html = ""
            st.markdown(
                "<div class='answer'><span style='font-weight: bold; color:#6d7284;'>"
                + f"Answer to question number {question_number}</span>"
                + f"<br><br>{rows.loc[question_number, 'Answer']}{image_html}</div>",
                unsafe_allow_html=True,
            )
            downcol1, downcol2 = st.columns(2)
            with downcol1:
                st.button(
                    "Incorrect",
                    on_click=lambda: set_correct(False),
                    use_container_width=True,
                )
            with downcol2:
                st.button(
                    "Correct",
                    on_click=lambda: set_correct(True),
                    use_container_width=True,
                )
            st.session_state.button2_clicked = False

    # this part normally should be on top however st.markdown always adds divs even it is rendering non visible parts?

    st.markdown(
        '<div><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Barlow+Condensed&family=Cabin&display=swap" rel="stylesheet"></div>',
        unsafe_allow_html=True,
    )

with tab_search:
    df = pd.DataFrame(rows)

    # Use a text_input to get the keywords to filter the dataframe
    text_search = st.text_input("Search in questions and answers", value="")

    # Filter the dataframe using masks
    m2 = df["Question"].str.contains(text_search)
    m3 = df["Answer"].str.contains(text_search)
    df_search = df[m2 | m3]

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
                st.markdown(f"**{row['Question'].strip()}**")
                if not pd.isna(row["Answer"]):
                    st.markdown(f"{row['Answer'].strip()}")
                if sample_weights is not None:
                    st.write(f"Sample weight: {sample_weights[row['No']]:.2%}")
                # with st.expander("Answer"):
                #     st.markdown(f"*{row['Answer'].strip()}*")


with tab_results:
    # Load previous results
    results = st.file_uploader("**Upload previous results ('No' must match)**")
    default_results = (
        "results" in st.session_state and len(st.session_state.results) == 0
    )
    if results and default_results:
        st.session_state.results = pd.read_csv(results)

    # Download results
    if "results" in st.session_state:
        csv = convert_results(st.session_state.results)
        st.download_button(
            f"Download (CSV, {len(st.session_state.results)} rows)",
            csv,
            file_name="results.csv",
            mime="text/csv",
        )

    st.write("### Sample Results")
    st.write(st.session_state.results.tail())
