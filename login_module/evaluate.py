
import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import io
import base64



def create_metrics_chart(metrics_dict):
    """Creates a pie chart image from metrics."""
    try:
        labels = list(metrics_dict.keys())
        sizes = list(metrics_dict.values())

        fig, ax = plt.subplots(figsize=(6, 6)) # Adjust size as needed
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.

        # Save plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig) # Important to close the figure
        return buf
    except Exception as e:
        print(f"Error creating chart: {e}")
        return None

def generate_evaluation_report(metrics_data_list):
    """
    Generates a text evaluation report and a chart.
    metrics_data_list: List of dictionaries, each containing metrics for a question.
    """
    if not metrics_data_list:
        return "No interview data available for evaluation.", None

    # Aggregate metrics (average scores)
    aggregated_metrics = {
        "Communication skills": 0.0,
        "Teamwork and collaboration": 0.0,
        "Problem-solving and critical thinking": 0.0,
        "Time management and organization": 0.0,
        "Adaptability and resilience": 0.0
    }
    num_questions = len(metrics_data_list)
    if num_questions == 0:
        num_questions = 1 # Avoid division by zero

    for metrics_dict in metrics_data_list:
        for key, value in metrics_dict.items():
            if key in aggregated_metrics:
                aggregated_metrics[key] += value

    for key in aggregated_metrics:
        aggregated_metrics[key] /= num_questions
        aggregated_metrics[key] = round(aggregated_metrics[key], 2) # Round to 2 decimal places

    average_rating = sum(aggregated_metrics.values()) / len(aggregated_metrics)
    average_rating = round(average_rating, 2)

    # --- Generate Text Report ---
    report_lines = [f"## Hey Candidate, here is your interview evaluation:\n"]
    report_lines.append("### Skill Ratings:\n")
    for metric, rating in aggregated_metrics.items():
        report_lines.append(f"* **{metric}:** {rating}/10\n")

    report_lines.append(f"\n### Overall Average Rating: {average_rating:.2f}/10\n")

    improvement_content = """
### Areas for Improvement:

*   **Communication:** Focus on clarity, conciseness, and tailoring your responses to the audience. Use examples and evidence to support your points.
*   **Teamwork and collaboration:** Highlight your teamwork skills through specific examples and demonstrate your ability to work effectively with others.
*   **Problem-solving and critical thinking:** Clearly explain your problem-solving approach and thought process. Show your ability to analyze information and arrive at logical solutions.
*   **Time management and organization:** Emphasize your ability to manage time effectively and stay organized during challenging situations.
*   **Adaptability and resilience:** Demonstrate your ability to adapt to new situations and overcome challenges. Share examples of how you have handled unexpected situations or setbacks in the past.

**Remember:** This is just a starting point. Customize the feedback based on the specific strengths and weaknesses identified in your interview.
"""
    report_lines.append(improvement_content)
    report_text = "".join(report_lines)

    # --- Generate Chart ---
    chart_buffer = create_metrics_chart(aggregated_metrics)

    return report_text, chart_buffer

# --- Gradio Interface for Evaluation (Example Usage) ---

# This part would typically be called from your main interview completion logic
# and the outputs connected to Gradio components.

# Example dummy data for testing the evaluation function
# dummy_metrics_data = [
#     {
#         "Communication skills": 7.5,
#         "Teamwork and collaboration": 6.0,
#         "Problem-solving and critical thinking": 8.0,
#         "Time management and organization": 5.5,
#         "Adaptability and resilience": 7.0
#     },
#     {
#         "Communication skills": 8.0,
#         "Teamwork and collaboration": 7.5,
#         "Problem-solving and critical thinking": 6.5,
#         "Time management and organization": 8.0,
#         "Adaptability and resilience": 6.0
#     }
# ]

# def run_evaluation(metrics_data_input):
#     report, chart = generate_evaluation_report(metrics_data_input)
#     return report, chart

# with gr.Blocks() as eval_demo:
#     gr.Markdown("## Interview Evaluation")
#     metrics_input = gr.JSON(label="Metrics Data (List of Dicts)", value=dummy_metrics_data)
#     run_btn = gr.Button("Generate Evaluation")
#     report_output = gr.Markdown(label="Evaluation Report")
#     chart_output = gr.Image(label="Skills Breakdown", type="pil") # or type="filepath"

#     run_btn.click(
#         fn=run_evaluation,
#         inputs=metrics_input,
#         outputs=[report_output, chart_output]
#     )

# if __name__ == "__main__":
#     eval_demo.launch()
