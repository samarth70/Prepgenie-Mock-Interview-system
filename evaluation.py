import streamlit as st
import matplotlib.pyplot as plt
st.set_page_config(layout="wide")
# Define metrics and random ratings (customize if needed)
metrics = {
    "Communication skills": 7,
    "Teamwork and collaboration": 8,
    "Problem-solving and critical thinking": 9,
    "Time management and organization": 6,
    "Adaptability and resilience": 8,
}
col1, col2 = st.columns(2)

# Calculate overall average rating
average_rating = sum(metrics.values()) / len(metrics)

# Option 1: Full width containers
with col1:
    st.header("Hey Deven, we have evaluated your interview:")
    # Display metrics and progress bars
    for metric, rating in metrics.items():
        st.subheader(metric)
        st.write(f"Rating: {rating}")
        progress_bar_width = int(200 * rating / 10)
        st.markdown(f"<div style='background-color: lightblue; width: {progress_bar_width}px; height: 10px;'></div>", unsafe_allow_html=True)

with col2:
    st.header("Areas for improvement based on your answers:")
    # Create and display pie chart
    plt.figure(figsize=(4, 4))
    plt.pie(metrics.values(), labels=metrics.keys(), autopct="%1.1f%%")
    plt.axis("equal")
    st.pyplot(use_container_width=True)

    st.subheader(f"Overall average rating: {average_rating:.2f}")
    # Use Markdown for rich text and flexibility
    improvement_content = """

    * **Communication:** Focus on clarity, conciseness, and tailoring your responses to the audience. Use examples and evidence to support your points.
    * **Teamwork and collaboration:** Highlight your teamwork skills through specific examples and demonstrate your ability to work effectively with others.
    * **Problem-solving and critical thinking:** Clearly explain your problem-solving approach and thought process. Show your ability to analyze information and arrive at logical solutions.
    * **Time management and organization:** Emphasize your ability to manage time effectively and stay organized during challenging situations.
    * **Adaptability and resilience:** Demonstrate your ability to adapt to new situations and overcome challenges. Share examples of how you have handled unexpected situations or setbacks in the past.

    **Remember:** This is just a starting point. Customize the feedback based on the specific strengths and weaknesses identified in your interview.

    """

    st.markdown(improvement_content)