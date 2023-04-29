import pandas as pd
from time import time, sleep
import streamlit as st
import plotly.express as px
from gtts import gTTS
from tempfile import NamedTemporaryFile


RESULT_COLUMNS = ["No", "Epoch Time", "Correct", "Question"]
N_PREV = 2


def set_correct(question_number, correct: bool) -> None:
    new_row = pd.DataFrame(
        [(question_number, int(time()), correct, "")],
        columns=RESULT_COLUMNS,
    )
    st.session_state.results = pd.concat(
        [st.session_state.results, new_row], ignore_index=True
    )


@st.cache_data
def upload_results(raw_results):
    print("Reloading results...")
    results = pd.read_csv(raw_results)
    st.session_state.results = results


def add_questions_to_results(questions: pd.DataFrame, results: pd.DataFrame):
    if "Question" in results.columns:
        results.drop(columns=["Question"], inplace=True)
    results = results.merge(
        questions.reset_index()[["No", "Question"]],
        on="No",
        how="left",
    )
    return results


@st.cache_data
def get_questions(raw_questions):
    st.session_state.results = create_default_results()
    questions = pd.read_csv(raw_questions)
    questions.rename(
        columns={
            st.session_state.headers["answer"]: "Answer",
            st.session_state.headers["question"]: "Question",
            st.session_state.headers["index"]: "No",
            st.session_state.headers["topic"]: "Topic",
        },
        inplace=True,
    )
    # uncomment to test images
    # questions.dropna(subset=["Image"], inplace=True)
    questions.set_index("No", inplace=True)
    return questions


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


@st.cache_data
def create_date_plot(df, y, title, hover_data):
    fig = px.line(
        df,
        x="Date",
        y=y,
        title=title,
        hover_data=hover_data,
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            )
        ),
    )
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


def plot_results(results):
    results = results.copy()
    results["Date"] = pd.to_datetime(results["Epoch Time"], unit="s").dt.date
    results_perc = results.groupby(["Date"])[["Correct"]].mean().reset_index()
    results_sum = results.groupby(["Date"])[["Correct"]].count().reset_index()
    results_sum.rename(columns={"Correct": "Questions"}, inplace=True)

    create_date_plot(
        results_perc,
        y="Correct",
        title="Percentage Correct Over Time",
        hover_data={"Correct": ":.00%"},
    )
    create_date_plot(
        results_sum,
        y="Questions",
        title="Questions Answered Over Time",
        hover_data=None,
    )


def get_time_lapse(df, datecol: str) -> int:
    return df[datecol].max() - df[datecol].min()


def create_default_results():
    df = pd.DataFrame(columns=RESULT_COLUMNS)
    df.Correct = df.Correct.astype(bool)
    return df


def text_to_speech(play, txt: str, **kwargs) -> None:
    """Convert text into binary and send into play function"""
    mp3_fp = NamedTemporaryFile()
    tts = gTTS(txt, **kwargs)
    sleep(0.25)
    tts.write_to_fp(mp3_fp)
    play(mp3_fp)
    mp3_fp.close()


def create_audio_button(txt, **kwargs):
    text_to_speech(lambda b: st.audio(b.name, format="audio/mpeg"), txt, **kwargs)
