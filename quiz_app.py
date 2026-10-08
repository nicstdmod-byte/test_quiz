import streamlit as st

st.set_page_config(page_title="Kid Quiz", page_icon="🎈")

st.title("🎈 Kid Quiz")
st.subheader("What is 2 + 3?")

options = ["3", "4", "5", "6"]
answer = st.radio("Pick one:", options, index=None)

if st.button("Check answer"):
    if answer is None:
        st.info("Please choose an answer first 🙂")
    elif answer == "5":
        st.success("Correct! Great job! 🎉")
        st.balloons()
    else:
        st.error("Oops, try again! 💪")
