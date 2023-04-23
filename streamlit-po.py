import streamlit as st
import pandas as pd
from backend import (
    set_correct,
    upload_results,
    add_questions_to_results,
    get_weights,
    get_questions,
    plot_results,
    get_time_lapse,
    create_default_results,
    create_audio_button,
)

# -------------- app config ---------------

st.set_page_config(page_title="Learn with Flashcards", page_icon="🚀")

# ---------------- functions ----------------


# external css
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# callbacks
def callback_question_once_clicked():
    st.session_state.question_once_clicked = True


def callback_answer():
    st.session_state.show_answer_clicked = True


# ---------------- Prepare Results --------
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
    raw_questions = st.file_uploader("**Upload your question/answers**")
    if raw_questions is None:
        questions = pd.DataFrame(columns=["No", "Topic", "Question", "Answer"])
    else:
        questions = get_questions(raw_questions)
    st.session_state.questions = questions

    # Selecting a topic and filtering questions
    available_topics = (
        ["No selection"] + questions.Topic.unique().tolist()
        if "Topic" in questions.columns
        else []
    )
    available_topics = [str(topic) for topic in available_topics]
    selected_topic = st.selectbox("Select a Topic", options=available_topics)
    if selected_topic is not None:
        if selected_topic == "nan":
            questions = questions.loc[pd.isna(questions.Topic)]
        elif selected_topic != "No selection":
            questions = questions.loc[questions.Topic == selected_topic]

    read_question = st.checkbox("Audio for Questions")


# ---------------- CSS ----------------

local_css("style.css")

# ---------------- SESSION STATE ----------------

if "question_once_clicked" not in st.session_state:
    st.session_state.question_once_clicked = False

if "show_answer_clicked" not in st.session_state:
    st.session_state.show_answer_clicked = False

if "q_no" not in st.session_state:
    st.session_state.q_no = 0

if "q_no_temp" not in st.session_state:
    st.session_state.q_no_temp = 0

if "results" not in st.session_state:
    st.session_state.results = create_default_results()

if "questions" not in st.session_state:
    st.session_state.questions = pd.DataFrame(
        columns=["No", "Topic", "Question", "Answer"]
    )

if "headers" not in st.session_state:
    st.session_state.headers = {
        "index": "Index",
        "question": "Word",
        "answer": "Explanation",
        "topic": "Topic",
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
        "Index",
        value=st.session_state.headers["index"],
    )
    st.session_state.headers["question"] = st.text_input(
        "Question",
        value=st.session_state.headers["question"],
    )
    st.session_state.headers["answer"] = st.text_input(
        "Answer",
        value=st.session_state.headers["answer"],
    )
    st.session_state.headers["topic"] = st.text_input(
        "Topic",
        value=st.session_state.headers["topic"],
    )

with tab_cards:
    st.title("Your Flashcards")
    no = len(questions)
    st.caption("Currently we have " + str(no) + " questions in the database")

    # ---------------- Questions & answers logic ----------------

    col1, col2 = st.columns(2)
    with col1:
        question = st.button(
            "Draw question",
            on_click=callback_question_once_clicked,
            key="Draw",
            use_container_width=True,
        )
    with col2:
        answer = st.button(
            "Show answer",
            on_click=callback_answer,
            key="Answer",
            use_container_width=True,
        )

    if len(questions) and (question or st.session_state.question_once_clicked):
        # randomly select question number
        st.session_state.q_no = questions.sample(weights=sample_weights).index.values[0]

        # this 'if' checks if algorithm should use value from temp or new value
        if st.session_state.show_answer_clicked:
            question_number = st.session_state.q_no_temp
        else:
            question_number = st.session_state.q_no
            # keep memory of question number in order to show answer
            st.session_state.q_no_temp = st.session_state.q_no

        selected_question = questions.loc[question_number, "Question"]
        st.markdown(
            '<div class="blockquote-wrapper"><div class="blockquote"><h1><span style="color:#ffffff">'
            + selected_question
            + f"</span></h1><h4>&mdash; Question no. {question_number}</em></h4></div></div>",
            unsafe_allow_html=True,
        )
        if read_question:
            create_audio_button(selected_question)
        if answer:
            # add image using link if available
            if "Image" in questions.columns:
                image_link = questions.loc[question_number, "Image"]
                if image_link and not pd.isna(image_link):
                    image_html = f'<br><img src="{questions.loc[question_number, "Image"]}" class="center" alt="Image" >'
                else:
                    image_html = ""
            else:
                image_html = ""
            st.markdown(
                "<div class='answer'><span style='font-weight: bold; color:#6d7284;'>"
                + f"Answer to question number {question_number}</span>"
                + f"<br><br>{questions.loc[question_number, 'Answer']}{image_html}</div>",
                unsafe_allow_html=True,
            )
            if (
                "Formula" in questions.columns
                and not pd.isna(questions.loc[question_number, "Formula"])
                and questions.loc[question_number, "Formula"]
            ):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### Formula\n")
                st.latex(questions.loc[question_number, "Formula"])
            downcol1, downcol2 = st.columns(2)
            with downcol1:
                st.button(
                    "Incorrect",
                    on_click=lambda: set_correct(question_number, False),
                    use_container_width=True,
                )
            with downcol2:
                st.button(
                    "Correct",
                    on_click=lambda: set_correct(question_number, True),
                    use_container_width=True,
                )
            st.session_state.show_answer_clicked = False

    # this part normally should be on top however st.markdown always adds divs even it is rendering non visible parts?

    st.markdown(
        '<div><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Barlow+Condensed&family=Cabin&display=swap" rel="stylesheet"></div>',
        unsafe_allow_html=True,
    )

with tab_search:
    df = questions
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
    raw_results = st.file_uploader("**Upload previous results ('No' must match)**")
    if raw_results:
        upload_results(raw_results)
    st.session_state.results = add_questions_to_results(
        questions, st.session_state.results
    )
    # Download results
    csv = st.session_state.results.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download (CSV, {len(st.session_state.results)} rows)",
        csv,
        file_name="results.csv",
        mime="text/csv",
    )

    st.write("### Sample Results")
    st.write(st.session_state.results.tail())

    st.write("### Evolution over Time")
    if (
        len(st.session_state.results)
        and get_time_lapse(st.session_state.results, "Epoch Time") > 24 * 60**2
    ):
        plot_results(st.session_state.results)
    else:
        st.write("Sorry, to show evolution we need results more than one day apart")
