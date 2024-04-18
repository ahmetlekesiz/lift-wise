import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Weight Lifting Logs Dashboard')

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Reading the uploaded CSV file
    data = pd.read_csv(uploaded_file)

    # Display the dataframe (optional, could be commented out in production)
    # st.write(data)

    # Convert 'Date' column to datetime format to make manipulation easier
    data['Date'] = pd.to_datetime(data['Date'])

    # Basic Data Overview
    st.header("Data Overview")
    st.write(data.describe())

    # Generate a list of exercises
    exercises = data['Exercise Name'].unique()
    selected_exercise = st.selectbox('Select an Exercise', exercises)

    # Filter data for the selected exercise
    exercise_data = data[data['Exercise Name'] == selected_exercise]

    # Summary Statistics for Selected Exercise
    st.header(f"Summary for {selected_exercise}")
    if not exercise_data.empty:
        st.write(exercise_data[['Date', 'Weight', 'Reps', 'RPE']].describe())

    # Progress Over Time
    st.header(f"Progress Over Time for {selected_exercise}")

    # Assuming 'Weight' multiplied by 'Reps' gives an indication of volume
    exercise_data['Total Volume'] = exercise_data['Weight'] * exercise_data['Reps']
    volume_summary = exercise_data.groupby(exercise_data['Date'].dt.date)['Total Volume'].sum().reset_index()

    fig, ax = plt.subplots()
    ax.plot(volume_summary['Date'], volume_summary['Total Volume'], marker='o', linestyle='-')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Volume Lifted')
    ax.set_title(f"Volume Over Time for {selected_exercise}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)

    # Advanced: Plotting multiple metrics might require additional filtering or interactive widgets
else:
    st.write("Please upload a CSV file to get started.")